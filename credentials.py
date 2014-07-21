#!/usr/bin/env python

import os

def set_creds(username,
                       password,
                       auth_url,
                       tenant,
                       current_os):
    D = dict(OS_USERNAME = username,
             OS_PASSWORD = password,
             OS_AUTH_URL = auth_url,
             OS_TENANT_NAME = tenant)
    current_os.environ.update(D)


def get_keystone_creds(current_os):
    d = {}
    d['username'] = current_os.environ['OS_USERNAME']
    d['password'] = current_os.environ['OS_PASSWORD']
    d['auth_url'] = current_os.environ['OS_AUTH_URL']
    d['project_id'] = current_os.environ['OS_TENANT_NAME']
    return d

def get_nova_creds(current_os):
    d = {}
    d['username'] = current_os.environ['OS_USERNAME']
    d['api_key'] = current_os.environ['OS_PASSWORD']
    d['auth_url'] = current_os.environ['OS_AUTH_URL']
    d['project_id'] = current_os.environ['OS_TENANT_NAME']
    return d
