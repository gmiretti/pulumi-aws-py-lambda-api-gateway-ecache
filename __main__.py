# Translating https://learn.hashicorp.com/terraform/aws/lambda-api-gateway

import os
import mimetypes
import hashlib as hash
import base64

from pulumi import export, FileAsset, ResourceOptions, Config
from pulumi_aws import s3, lambda_, apigateway, elasticache
import iam
import aws

LAMBDA_SOURCE = 'lambda.py'
LAMBDA_PACKAGE = 'lambda.zip'
LAMBDA_VERSION = '1.0.0'
REDIS_FOLDER = 'venv/lib/python3.6/site-packages/redis'


config = Config('lambda-api-gateway')
# you could use ec2.DefaultSubnet to gather this programmatically
subnet_ids = aws.get_subnets_ids()
# you can use ec2.DefaultSecurityGroup to gather this programmatically
security_group_ids = aws.get_default_security_groups_ids()


def sha256(filepath):
    # Specify how many bytes of the file you want to open at a time
    BLOCKSIZE = 65536

    sha = hash.sha256()
    with open(filepath, 'rb') as file_to_hash:
        file_buffer = file_to_hash.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = file_to_hash.read(BLOCKSIZE)

    return sha.digest()


# Package lambda code
os.system('zip --quiet %s %s' % (LAMBDA_PACKAGE, LAMBDA_SOURCE))
os.system('cd %s/.. ; zip --quiet -r ../../../../%s redis' % (REDIS_FOLDER, LAMBDA_PACKAGE))
deploy_sha_hash = sha256(LAMBDA_PACKAGE)
deploy_64_hash = base64.b64encode(deploy_sha_hash)
# print(deploy_sha_hash, deploy_64_hash)

# Create elasticache redis DB
cache = elasticache.Cluster(
    'cache',
    cluster_id='redis-cache',
    engine='redis',
    node_type='cache.t2.micro',
    num_cache_nodes=1,
    engine_version='5.0.4',
    apply_immediately=True
)

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket('lambda-api-gateway-example')

mime_type, _ = mimetypes.guess_type(LAMBDA_PACKAGE)
deploy_package = s3.BucketObject(
            'deploy_package',
            key=LAMBDA_VERSION+'/'+LAMBDA_PACKAGE,
            bucket=bucket.id,
            source=FileAsset(LAMBDA_PACKAGE),
            content_type=mime_type
            )

example_fn = lambda_.Function(
    'ServerlessExample',
    s3_bucket=deploy_package.bucket,
    s3_key=deploy_package.key,
    handler="lambda.handler",
    runtime="python3.7",
    role=iam.lambda_role.arn,
    timeout=10,
    source_code_hash=str(deploy_64_hash),
    environment={"variables": {"REDIS_ENDPOINT": cache.cache_nodes[0]['address']}},
    vpc_config={
        "subnet_ids": subnet_ids,
        "security_group_ids": security_group_ids
    }
)

example_api = apigateway.RestApi(
    'ServerlessExample',
    description='Pulumi Lambda API Gateway Example'
)

proxy_root_met = apigateway.Method(
    'proxy_root',
    rest_api=example_api,
    resource_id=example_api.root_resource_id,
    http_method='ANY',
    authorization='NONE'
)

example_root_int = apigateway.Integration(
    'lambda_root',
    rest_api=example_api,
    resource_id=proxy_root_met.resource_id,
    http_method=proxy_root_met.http_method,
    integration_http_method='POST',
    type='AWS_PROXY',
    uri=example_fn.invoke_arn
)

example_dep = apigateway.Deployment(
    'example',
    rest_api=example_api,
    stage_name="example-test",
    __opts__=ResourceOptions(depends_on=[example_root_int])
)

example_perm = lambda_.Permission(
    "apigw",
    statement_id="AllowAPIGatewayInvoke",
    action="lambda:InvokeFunction",
    function=example_fn,
    principal="apigateway.amazonaws.com",
    source_arn=example_dep.execution_arn.apply(lambda x: f"{x}/*/*")
)

# Export the name of the bucket with lambda code
# List bucket with:
# aws s3 ls --recursive `pulumi stack output bucket_name`
export('bucket_name',  bucket.id)
# Export the name of the lambda
# Test with:
# aws lambda invoke --region=eu-west-1 --function-name=`pulumi stack output lambda_name` output.txt
export('lambda_name',  example_fn.id)
# Export the name of the API endpoint
export('base_url', example_dep.invoke_url)
# Export redis cache first endpoint
export('redis_endpoint', cache.cache_nodes[0]['address'])
# Export redis networking
export('redis_security_group_ids', cache.security_group_ids)
