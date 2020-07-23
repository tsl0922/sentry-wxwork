from __future__ import absolute_import

from django.apps import AppConfig

class Config(AppConfig):
    name = "sentry_wxwork"

    def ready(self):
        from sentry.auth import register

        from .provider import WxWorkAuthProvider

        register("wxwork", WxWorkAuthProvider)
