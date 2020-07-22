from __future__ import absolute_import, print_function

from django.conf import settings

API_BASE_URL = 'https://qyapi.weixin.qq.com/cgi-bin'
AUTHORIZE_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
QRLOGIN_URL = 'https://open.work.weixin.qq.com/wwopen/sso/qrConnect'
ACCESS_TOKEN_URL = '%s/gettoken' % API_BASE_URL
SCOPE = 'snsapi_base'

CLIENT_ID = getattr(settings, 'WXWORK_CORP_ID', None)
CLIENT_SECRET = getattr(settings, 'WXWORK_SECRET', None)
AGENT_ID = getattr(settings, 'WXWORK_AGENT_ID', None)