
# Custom Authorizer

Lambda Function for custom authorizer in API Gateway

![aws-services][aws-services-image]

## How To Setup a CodePipeline

- First, create a S3 Bucket where the deployment files will be uploaded with below naming convention. *(You can use a different convention, but you need to add a permission for the CodeBuild to access this S3 bucket)*.

  >

      codepipeline-<region>-<account_num>-<project_name>

  like

      codepipeline-us-east-1-9999999999-aws-services-authorizer


- Follow the steps in http://docs.aws.amazon.com/lambda/latest/dg/automating-deployment.html along with an additional step to set an environment variable under 'Advanced' setting when creating a new project in CodeBuild

  > S3_BUCKET_NAME : S3 bucket name you created above

- Follow either way to set input parameter values of the template when creating a build action whose mode is 'Create of replace a change set'

  1. Using a configuration file

    > Create a configuration json file that has input parameter values as below

          {
              "Parameters": {
                "SSOHost": "value1",
                "SSOBasicAuthUsername": "value2",
                "SSOBasicAuthPassword": "value3",
                "SSOMasterToken": "value4"
              }
          }

    > Set the name of the above json file in 'Template configuration' using below format

        InputArtifactName::TemplateConfigurationFileName

    like

        MyAppBuild::env_dev.json

  2. Set the parameter json in 'Parameter overrides' under 'Advanced' setting


## How To Test Lambda Functions

- $ cd tests
- Export environment variables, SSO_HOST, SSO_BASIC_AUTH_USERNAME, SSO_BASIC_AUTH_PASSWORD, SSO_MASTER_TOKEN
- Replace \<username\> and \<password\> with proper values in 'test_authorizer.py'
- $ python test_authorizer.py

## [![Sungard Availability Services | Labs][labs-logo]][labs-github-url]

This project is maintained by the Labs group at [Sungard Availability
Services](http://sungardas.com)

GitHub: [https://sungardas.github.io](https://sungardas.github.io)

Blog:
[http://blog.sungardas.com/CTOLabs/](http://blog.sungardas.com/CTOLabs/)

[labs-github-url]: https://sungardas.github.io
[labs-logo]: https://raw.githubusercontent.com/SungardAS/repo-assets/master/images/logos/sungardas-labs-logo-small.png
[aws-services-image]: ./docs/images/logo.png?raw=true
