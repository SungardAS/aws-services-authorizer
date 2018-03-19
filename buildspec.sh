
source env.local

sed -i 1 "s/AWS::REGION/$AWS_DEFAULT_REGION/g" swagger.yaml
sed -i 2 "s/AWS::ACCOUNT_ID/$AWS_ACCOUNT_ID/g" swagger.yaml
cd src; pip install -r requirements.txt -t .; cd ..


aws cloudformation package \
   --template-file ./templates/template.yaml \
   --s3-bucket $S3_BUCKET_NAME \
   --output-template-file samTemplate.yaml


mv swagger.yaml1 swagger.yaml
rm swagger.yaml2


aws cloudformation deploy --template-file ./samTemplate.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --stack-name SungardAS-aws-services-authorizer \
  --parameter-overrides VpcCidr=$VPC_CIDR PublicCidr1=$PUBLIC_CIDR_1 PublicCidr2=$PUBLIC_CIDR_2 \
  PrivateCidr1=$PRIVATE_CIDR_1 PrivateCidr2=$PRIVATE_CIDR_2 NameTag=$NAME_TAG \
  SSOHost=$SSO_HOST SSOBasicAuthUsername=$SSO_BASIC_AUTH_USERNAME SSOBasicAuthPassword=$SSO_BASIC_AUTH_PASSWORD \
  SSOMasterToken=$SSO_MASTER_TOKEN
