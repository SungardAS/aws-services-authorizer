from __future__ import print_function

import os
import json
import boto3
from base64 import b64decode
from sso import authenticate

def lambda_handler(event, context):
    master_token = os.environ.get('SSO_MASTER_TOKEN')
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(master_token))['Plaintext']
    try:
        ret = authenticate(event['username'], event['password'])
        print(ret)
        refresh_token = json.loads(ret).get('refresh_token')
    except Exception, ex:
        print(ex)
        raise Exception('Unauthorized')
    print('refresh_token = %s' % refresh_token)
    if refresh_token is None:
        raise Exception('Unauthorized')
    return refresh_token
