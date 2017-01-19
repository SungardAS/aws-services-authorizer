
"""
export SSO_HOST=
export SSO_BASIC_AUTH_USERNAME=
export SSO_BASIC_AUTH_PASSWORD=
export SSO_MASTER_TOKEN=
"""

import sys
sys.path.insert(0, r"../src")

import json
from sso import authenticate
ret = authenticate('<username>', '<password>')
refresh_token = json.loads(ret)['refresh_token']

from authorizer import lambda_handler
context = None
event = {
    'authorizationToken': refresh_token,
    'methodArn': 'arn:aws:lambda:us-east-1:11111111:function/aaa:custom_authorizer'
}
lambda_handler(event, context)
