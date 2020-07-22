from __future__ import absolute_import

import logging
from uuid import uuid4
from six.moves.urllib.parse import urlencode
from sentry.auth.view import AuthView
from sentry.http import safe_urlopen
from sentry.utils import json
from sentry.utils.http import absolute_uri

from .constants import (
    API_BASE_URL, AUTHORIZE_URL, QRLOGIN_URL, ACCESS_TOKEN_URL, CLIENT_ID, CLIENT_SECRET, AGENT_ID, SCOPE
)

ERR_INVALID_STATE = "An error occurred while validating your request."

class WxWorkLogin(AuthView):
    authorize_url = None
    qrlogin_url = None
    client_id = None
    agent_id = None
    scope = ""

    def __init__(self, *args, **kwargs):
        super(WxWorkLogin, self).__init__(*args, **kwargs)
        self.authorize_url = AUTHORIZE_URL
        self.qrlogin_url = QRLOGIN_URL
        self.client_id = CLIENT_ID
        self.agent_id = AGENT_ID
        self.scope = SCOPE

    def get_scope(self):
        return self.scope

    def get_authorize_params(self, state, redirect_uri):
        return {
            "appid": self.client_id,
            "response_type": "code",
            "scope": self.get_scope(),
            "state": state,
            "redirect_uri": redirect_uri,
        }

    def get_qrlogin_params(self, state, redirect_uri):
        return {
            "appid": self.client_id,
            "agentid": self.agent_id,
            "state": state,
            "redirect_uri": redirect_uri,
        }

    def dispatch(self, request, helper):
        if "code" in request.GET:
            return helper.next_step()

        state = uuid4().hex

        if 'wxwork' in request.META.get("HTTP_USER_AGENT"):
            params = self.get_authorize_params(
                state=state, redirect_uri=absolute_uri(helper.get_redirect_url())
            )
            redirect_uri = u"{}?{}#wechat_redirect".format(self.authorize_url, urlencode(params))
        else:
            params = self.get_qrlogin_params(
                state=state, redirect_uri=absolute_uri(helper.get_redirect_url())
            )
            redirect_uri = u"{}?{}".format(self.qrlogin_url, urlencode(params))

        helper.bind_state("state", state)

        return self.redirect(redirect_uri)

class WxWorkCallback(AuthView):
    logger = logging.getLogger('auth_wxwork')

    access_token_url = None
    client_id = None
    client_secret = None

    def __init__(self, *args, **kwargs):
        super(WxWorkCallback, self).__init__(*args, **kwargs)
        self.access_token_url = ACCESS_TOKEN_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET

    def exchange_token(self, request, helper, code):
        url = '%s?corpid=%s&corpsecret=%s' % (self.access_token_url, self.client_id, self.client_secret)
        response = safe_urlopen(url)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))
        return json.loads(response.content)

    def dispatch(self, request, helper):
        error = request.GET.get("error")
        state = request.GET.get("state")
        code = request.GET.get("code")

        if error:
            return helper.error(error)

        if state != helper.fetch_state("state"):
            return helper.error(ERR_INVALID_STATE)

        data = self.exchange_token(request, helper, code)

        if data['errcode'] != 0:
            return helper.error(data["errmsg"])

        helper.bind_state("code", code)
        helper.bind_state("data", data)

        return helper.next_step()

class FetchUser(AuthView):
    logger = logging.getLogger('auth_wxwork')

    def get_user_id(self, access_token, code):
        url = '%s/user/getuserinfo?access_token=%s&code=%s' %(API_BASE_URL, access_token, code)
        response = safe_urlopen(url)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))
        data = json.loads(response.content)
        return data['UserId']

    def get_user_data(self, access_token, user_id):
        url = '%s/user/get?access_token=%s&userid=%s' %(API_BASE_URL, access_token, user_id)
        response = safe_urlopen(url)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))
        return json.loads(response.content)

    def handle(self, request, helper):
        data = helper.fetch_state("data")
        code = helper.fetch_state("code")
        
        user_id = self.get_user_id(data['access_token'], code)
        user = self.get_user_data(data['access_token'], user_id)

        helper.bind_state('user', user)
        return helper.next_step()