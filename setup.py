#!/usr/bin/env python
# coding: utf-8
from setuptools import setup

from sentry_wxwork import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='sentry_wxwork',
    version=__version__,
    packages=['sentry_wxwork'],
    url='https://github.com/tsl0922/sentry-wxwork',
    author='Shuanglei Tao',
    author_email='tsl0922@gmail.com',
    description='Plugin for Sentry which integrates with WeChat Work.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    entry_points={
        'sentry.plugins': [
            'sentry_wxwork = sentry_wxwork.plugin:WxworkNotificationsPlugin',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: System :: Monitoring',
    ],
    include_package_data=True,
)