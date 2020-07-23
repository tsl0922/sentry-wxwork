# coding: utf-8
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from sentry.plugins.bases import notify
from sentry.http import safe_urlopen
from sentry.utils import json
from sentry.utils.safe import safe_execute
from sentry.utils.forms import form_to_config
from sentry.integrations import FeatureDescription, IntegrationFeatures
from sentry.exceptions import PluginError

from . import __version__, __doc__ as package_doc


class WxworkNotificationsOptionsForm(notify.NotificationConfigurationForm):
    api_origin = forms.CharField(
        label=_('API origin'),
        widget=forms.TextInput(attrs={'placeholder': 'https://qyapi.weixin.qq.com/cgi-bin'}),
        initial='https://qyapi.weixin.qq.com/cgi-bin'
    )
    api_secret = forms.CharField(
        label=_('API secret'),
        widget=forms.PasswordInput(attrs={'placeholder': 'vQT_03RDVA3uE6JDASDASDAiXUvccqV8mDgLdLI'}),
        initial=getattr(settings, 'WXWORK_SECRET', None)
    )
    corp_id = forms.CharField(
        label=_('Corp ID'),
        widget=forms.TextInput(attrs={'placeholder': 'wwabcddzxdkrsdv'}),
        initial=getattr(settings, 'WXWORK_CORP_ID', None)
    )
    agent_id = forms.CharField(
        label=_('Agent ID'),
        widget=forms.TextInput(attrs={'placeholder': '1'}),
        initial=getattr(settings, 'WXWORK_AGENT_ID', None)
    )
    to_user = forms.CharField(
        label=_('Receivers: user list'),
        widget=forms.TextInput(attrs={'placeholder': 'UserID1|UserID2|UserID3'}),
        help_text=_('NOTE: user, party, tag list can not be empty at the same time'),
        required=False
    )
    to_party = forms.CharField(
        label=_('Receivers: party list'),
        widget=forms.TextInput(attrs={'placeholder': 'PartyID1|PartyID2'}),
        help_text=_('NOTE: user, party, tag list can not be empty at the same time'),
        required=False
    )
    to_tag = forms.CharField(
        label=_('Receivers: tag list'),
        widget=forms.TextInput(attrs={'placeholder': 'TagID1 | TagID2'}),
        help_text=_('NOTE: user, party, tag list can not be empty at the same time'),
        required=False
    )
    message_template = forms.CharField(
        label=_('Message template'),
        widget=forms.Textarea(attrs={'class': 'span4'}),
        help_text=_('Set in standard python\'s {}-format convention, available names are: '
                    '{project_name}, {url}, {title}, {message}, {tag[%your_tag%]}'),
        initial='**[{project_name}]** [{tag[level]}: {title}]({url})\n\n> {message}'
    )

class WxworkNotificationsPlugin(notify.NotificationPlugin):
    title = 'WeChat Work'
    slug = 'sentry_wxwork'
    description = package_doc
    version = __version__
    author = 'Shuanglei Tao'
    author_url = 'https://github.com/tsl0922/sentry-wxwork'
    resource_links = [
        ('Bug Tracker', 'https://github.com/tsl0922/sentry-wxwork/issues'),
        ('Source', 'https://github.com/tsl0922/sentry-wxwork'),
        ('Reference', 'https://work.weixin.qq.com/api/doc/90000/90135/90664'),
    ]

    conf_key = 'sentry_wxwork'
    conf_title = title
    project_conf_form = WxworkNotificationsOptionsForm
    logger = logging.getLogger('sentry_wxwork')
    feature_descriptions = [
        FeatureDescription(
            """
            Send notification via WeChat Work for Sentry.
            """,
            IntegrationFeatures.ALERT_RULE,
        )
    ]

    access_token = None

    def is_configured(self, project, **kwargs):
        return bool(self.get_option('api_secret', project) and self.get_option('corp_id', project) and self.get_option('agent_id', project))

    def get_config(self, project, **kwargs):
        form = self.project_conf_form
        if not form:
            return []

        return form_to_config(form)

    def request_token(self, api_origin, api_secret, corp_id):
        url = '%s/gettoken?corpid=%s&corpsecret=%s' % (api_origin, corp_id, api_secret)
        response = safe_urlopen(url)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))
        return json.loads(response.content)

    def get_token(self, api_origin, api_secret, corp_id):
        if (not self.access_token) or self.access_token['expires'] < datetime.now():
            data = self.request_token(api_origin, api_secret, corp_id)
            if data['errcode'] != 0:
                raise PluginError("invalid wechat token response: %s" % data)
            self.access_token = {
                'token': data['access_token'],
                'expires': datetime.now() + timedelta(seconds = data['expires_in'])
            }
        return self.access_token['token']

    def build_message(self, group, event):
        the_tags = defaultdict(lambda: '[NA]')
        the_tags.update({k:v for k, v in event.tags})
        names = {
            'title': event.title,
            'tag': the_tags,
            'message': event.message,
            'project_name': group.project.name,
            'url': group.get_absolute_url(),
        }

        template = self.get_option('message_template', group.project)

        text = template.format(**names)

        return {
            'msgtype': 'markdown',
            'agentid': self.get_option('agent_id', group.project),
            'markdown': {
                'content': text
            }
        }

    def build_url(self, project):
        api_origin = self.get_option('api_origin', project)
        api_secret = self.get_option('api_secret', project)
        corp_id = self.get_option('corp_id', project)
        
        token = self.get_token(api_origin, api_secret, corp_id)

        return '%s/message/send?access_token=%s' % (api_origin, token)

    def send_message(self, payload, project):
        to_user = self.get_option('to_user', project)
        to_party = self.get_option('to_party', project)
        to_tag = self.get_option('to_tag', project)

        if to_user:
            payload['touser'] = to_user
        if to_party:
            payload['toparty'] = to_party
        if to_tag:
            payload['totag'] = to_tag

        self.logger.debug('Sending message to user: %s, party: %s, tag: %s ' % (to_user, to_party, to_tag))
        response = safe_urlopen(method='POST', url=self.build_url(project), json=payload)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))

        data = json.loads(response.content)
        if data['errcode'] == 40014 or data['errcode'] == 42001: # access token invalid or expired, retry
            self.access_token = None
            safe_urlopen(method='POST', url=self.build_url(project), json=payload)

    def notify_users(self, group, event, fail_silently=False, **kwargs):
        self.logger.debug('Received notification for event: %s' % event)

        payload = self.build_message(group, event)
        self.logger.debug('Built payload: %s' % payload)
        
        safe_execute(self.send_message, payload, group.project, _with_transaction=False)
