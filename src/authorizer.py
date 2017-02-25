from __future__ import print_function

import os
import re
import json
import boto3
from base64 import b64decode
from sso import extend_token, find_user_detail
import redis

redis_connection = None

def find_user_detail_from_sso(access_token):
    try:
        ret = find_user_detail(access_token)
        print("user detail of access_token [%s] : %s" % (access_token, ret))
        return ret
    except Exception, ex:
        print("failed to find user detail of access_token [%s] : %s" % (access_token, ex))
        return None

def lambda_handler(event, context):
    print("Client token: " + event['authorizationToken'])
    print("Method ARN: " + event['methodArn'])

    '''
    Validate the incoming token and produce the principal user identifier
    associated with the token. This can be accomplished in a number of ways:

    1. Call out to the OAuth provider
    2. Decode a JWT token inline
    3. Lookup in a self-managed DB
    '''

    # connect to the redis cluster
    global redis_connection
    if redis_connection is None:
        redis_host = os.environ.get('REDIS_HOST')
        redis_port = os.environ.get('REDIS_PORT')
        if redis_host:
            redis_connection = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    user_info = None
    refresh_token = None
    access_token = None
    user_guid = None
    error = None

    token = event.get('authorizationToken')
    if token is None:
        #raise Exception('Unauthorized')
        error = 'Unauthorized'
    else:
        master_token = os.environ.get('SSO_MASTER_TOKEN')
        DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(master_token))['Plaintext']
        if token == DECRYPTED:
            refresh_token = token
        else:
            if redis_connection:
                # find the latest refresh_token if exists
                user_info = redis_connection.get(token)
                print("user_info = %s" % user_info)
                if user_info:
                    user_info = json.loads(user_info)
                    user_guid = user_info.get('user_guid')
                    refresh_token = user_info.get('refresh_token')
                else:
                    user_info = {}
            if refresh_token is None:
                refresh_token = token
            try:
                ret = extend_token(refresh_token)
                print(ret)
                access_token = json.loads(ret).get('access_token')
                refresh_token = json.loads(ret).get('refresh_token')
            except Exception, ex:
                print(ex)
                #raise Exception('Unauthorized')
                error = 'Unauthorized'
            print('refresh_token = %s' % refresh_token)
            if refresh_token is None:
                #raise Exception('Unauthorized')
                error = 'Unauthorized'
            elif redis_connection:
                if user_guid is None:
                    # find user_guid using the access_token
                    user_detail = find_user_detail_from_sso(access_token)
                    if user_detail is None:
                        error = 'Unauthorized'
                    else:
                        user_guid = json.loads(user_detail).get('userGuid')
                        user_info['user_guid'] = user_guid
                # save the latest refresh token
                user_info['refresh_token'] = refresh_token
                redis_connection.set(token, json.dumps(user_info))
                print("user info is saved : %s" % user_info)

        principalId = 'user|a1b2c3d4'

    '''
    You can send a 401 Unauthorized response to the client by failing like so:

      raise Exception('Unauthorized')

    If the token is valid, a policy must be generated which will allow or deny
    access to the client. If access is denied, the client will receive a 403
    Access Denied response. If access is allowed, API Gateway will proceed with
    the backend integration configured on the method that was called.

    This function must generate a policy that is associated with the recognized
    principal user identifier. Depending on your use case, you might store
    policies in a DB, or generate them on the fly.

    Keep in mind, the policy is cached for 5 minutes by default (TTL is
    configurable in the authorizer) and will apply to subsequent calls to any
    method/resource in the RestApi made with the same token.

    The example policy below denies access to all resources in the RestApi.
    '''
    tmp = event['methodArn'].split(':')
    apiGatewayArnTmp = tmp[5].split('/')
    awsAccountId = tmp[4]

    policy = AuthPolicy(principalId, awsAccountId)
    policy.restApiId = apiGatewayArnTmp[0]
    policy.region = tmp[3]
    policy.stage = apiGatewayArnTmp[1]
    #policy.denyAllMethods()
    #policy.allowMethod(HttpVerb.GET, '/pets/*')
    policy.allowAllMethods()

    # Finally, build the policy
    authResponse = policy.build()

    # new! -- add additional key-value pairs associated with the authenticated principal
    # these are made available by APIGW like so: $context.authorizer.<key>
    # additional context is cached
    context = {
        #'key': 'value',  # $context.authorizer.key -> value
        #'number': 1,
        #'bool': True
        'refresh_token': refresh_token,
        'user_guid': user_guid
    }
    # context['arr'] = ['foo'] <- this is invalid, APIGW will not accept it
    # context['obj'] = {'foo':'bar'} <- also invalid
    if error:
        context['error'] = error

    authResponse['context'] = context

    return authResponse


class HttpVerb:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    ALL = '*'


class AuthPolicy(object):
    # The AWS account id the policy will be generated for. This is used to create the method ARNs.
    awsAccountId = ''
    # The principal used for the policy, this should be a unique identifier for the end user.
    principalId = ''
    # The policy version used for the evaluation. This should always be '2012-10-17'
    version = '2012-10-17'
    # The regular expression used to validate resource paths for the policy
    pathRegex = '^[/.a-zA-Z0-9-\*]+$'

    '''Internal lists of allowed and denied methods.

    These are lists of objects and each object has 2 properties: A resource
    ARN and a nullable conditions statement. The build method processes these
    lists and generates the approriate statements for the final policy.
    '''
    allowMethods = []
    denyMethods = []

    # The API Gateway API id. By default this is set to '*'
    restApiId = '*'
    # The region where the API is deployed. By default this is set to '*'
    region = '*'
    # The name of the stage used in the policy. By default this is set to '*'
    stage = '*'

    def __init__(self, principal, awsAccountId):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods = []
        self.denyMethods = []

    def _addMethod(self, effect, verb, resource, conditions):
        '''Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null.'''
        if verb != '*' and not hasattr(HttpVerb, verb):
            raise NameError('Invalid HTTP verb ' + verb + '. Allowed verbs in HttpVerb class')
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError('Invalid resource path: ' + resource + '. Path should match ' + self.pathRegex)

        if resource[:1] == '/':
            resource = resource[1:]

        resourceArn = 'arn:aws:execute-api:{}:{}:{}/{}/{}/{}'.format(self.region, self.awsAccountId, self.restApiId, self.stage, verb, resource)

        if effect.lower() == 'allow':
            self.allowMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })
        elif effect.lower() == 'deny':
            self.denyMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })

    def _getEmptyStatement(self, effect):
        '''Returns an empty statement object prepopulated with the correct action and the
        desired effect.'''
        statement = {
            'Action': 'execute-api:Invoke',
            'Effect': effect[:1].upper() + effect[1:].lower(),
            'Resource': []
        }

        return statement

    def _getStatementForEffect(self, effect, methods):
        '''This function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy.'''
        statements = []

        if len(methods) > 0:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if curMethod['conditions'] is None or len(curMethod['conditions']) == 0:
                    statement['Resource'].append(curMethod['resourceArn'])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement['Resource'].append(curMethod['resourceArn'])
                    conditionalStatement['Condition'] = curMethod['conditions']
                    statements.append(conditionalStatement)

            if statement['Resource']:
                statements.append(statement)

        return statements

    def allowAllMethods(self):
        '''Adds a '*' allow to the policy to authorize access to all methods of an API'''
        self._addMethod('Allow', HttpVerb.ALL, '*', [])

    def denyAllMethods(self):
        '''Adds a '*' allow to the policy to deny access to all methods of an API'''
        self._addMethod('Deny', HttpVerb.ALL, '*', [])

    def allowMethod(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy'''
        self._addMethod('Allow', verb, resource, [])

    def denyMethod(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy'''
        self._addMethod('Deny', verb, resource, [])

    def allowMethodWithConditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._addMethod('Allow', verb, resource, conditions)

    def denyMethodWithConditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._addMethod('Deny', verb, resource, conditions)

    def build(self):
        '''Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy.'''
        if ((self.allowMethods is None or len(self.allowMethods) == 0) and
                (self.denyMethods is None or len(self.denyMethods) == 0)):
            raise NameError('No statements defined for the policy')

        policy = {
            'principalId': self.principalId,
            'policyDocument': {
                'Version': self.version,
                'Statement': []
            }
        }

        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Allow', self.allowMethods))
        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Deny', self.denyMethods))

        return policy
