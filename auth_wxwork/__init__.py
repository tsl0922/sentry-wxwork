# coding: utf-8
"""
Plugin for Sentry which allows SSO Login via WeChat Work.
"""
from __future__ import absolute_import

from django import VERSION as DJANGO_VERSION

if DJANGO_VERSION >= (1, 7):
	default_app_config = "auth_wxwork.apps.Config"
else:
	from sentry.auth import register
	from .provider import WxWorkAuthProvider

	register('wxwork', WxWorkAuthProvider)
