# Sentry WeChat Work

Plugin for Sentry which allows sending notification and SSO Login via WeChat Work.

## Installation

> NOTE: sentry > 9.1.2 is not supported.

### Prepare

Install the plugin:

```
pip install sentry-wxwork
```

Obtain required config from WeChat Work admin console ([Read Me](https://work.weixin.qq.com/api/doc/90000/90135/90664)).

### Notification

On (Legacy) Integrations page, find `WeChat Work`, enable and configure it. 

### SSO Login

Add the following settings to your `sentry.conf.py`:

```
WXWORK_CORP_ID = ''
WXWORK_SECRET = ''
WXWORK_AGENT_ID = ''
```

or, if you prefer setting it via environment variables:

```
if 'WXWORK_CORP_ID' in os.environ:
    WXWORK_CORP_ID = env('WXWORK_CORP_ID')
    WXWORK_SECRET = env('WXWORK_SECRET')
    WXWORK_AGENT_ID = env('WXWORK_AGENT_ID')
```