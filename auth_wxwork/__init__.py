# coding: utf-8
"""
Plugin for Sentry which allows SSO Login via WeChat Work.
"""
from __future__ import absolute_import

from sentry.auth import register

from .provider import WxWorkAuthProvider

register('wxwork', WxWorkAuthProvider)