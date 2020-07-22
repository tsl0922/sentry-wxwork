from __future__ import absolute_import

import logging
from time import time
from sentry.auth.provider import Provider
from sentry.http import safe_urlopen
from sentry.utils import json
from sentry.auth.exceptions import IdentityNotValid

from .views import WxWorkLogin, WxWorkCallback, FetchUser

from .constants import (
    ACCESS_TOKEN_URL, CLIENT_ID, CLIENT_SECRET
)

class WxWorkAuthProvider(Provider):
    name = 'WeChat Work'

    logger = logging.getLogger('auth_wxwork')

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    access_token_url = ACCESS_TOKEN_URL

    def get_auth_pipeline(self):
        return [
            WxWorkLogin(),
            WxWorkCallback(),
            FetchUser()
        ]

    def build_config(self, config):
        return {}

    def get_identity_data(self, payload):
        return {
            'access_token': payload['access_token'],
            'expires': int(time()) + int(payload['expires_in']),
        }

    def build_identity(self, state):
        data = state['data']
        user_data = state['user']
        return {
            'id': user_data['userid'],
            'email': user_data['email'],
            'name': user_data['name'],
            'data': self.get_identity_data(data),
        }

    def update_identity(self, new_data, current_data):
        return new_data

    def refresh_identity(self, auth_identity):
        url = '%s?corpid=%s&corpsecret=%s' % (self.access_token_url, self.client_id, self.client_secret)
        response = safe_urlopen(url)
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))
        data = json.loads(response.content)

        if data['errcode'] != 0:
            raise IdentityNotValid('errcode: %d, errmsg: %s' & (data['errcode'], data['errmsg']))

        auth_identity.data.update(self.get_identity_data(data))
        auth_identity.update(data=auth_identity.data)
        