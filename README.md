# lambda-api-gateway-ecache

This [Pulumi](https://github.com/pulumi/pulumi) example use Python to deploy a serverless app using AWS Elasticache, Lambda and API Gateway as it's show in https://learn.hashicorp.com/terraform/aws/lambda-api-gateway plus adding access to Redis DB.

This example doesn't feature any of the higher-level abstractions of Pulumi, unavailable for Python at the moment ex. `python-awsx`, but it highlitghts the ability to manage existing application code in a Pulumi application. But it shows how to integrate with `boto3` to gather data from your account.

This example assumes `pulumi` and `aws-cli` installed and configured as described [here](https://pulumi.io/quickstart/aws/setup/#shared-credentials-file)

**NOTE** Works only in Linux ( I'm abusing the fact that redis package for python 3.6 works for python 3.7 too )

```bash
# Create and configure a new stack
$ pulumi stack init lambda-api-gateway-dev
$ pulumi config set aws:region eu-west-1

# Install dependencies
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt

# Preview and run the deployment
$ pulumi up
Previewing changes:
...
Performing changes:
...
info: 13 changes performed:
    + 13 resources created
Duration: 40s

# Test it out
$ curl $(pulumi stack output base_url)
<p>Hello Value!!!</p>

# See the logs
$ pulumi logs -f

# Remove the app
$ pulumi destroy
```
