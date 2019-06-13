from pulumi import Config
import boto3

conf = Config('aws')
client = boto3.client('ec2', region_name=conf.get('region'))

def get_subnets_ids():
    return [
        subnet['SubnetId']
        for subnet
        in client.describe_subnets()['Subnets']
        ]


def get_default_security_groups_ids():
    return [
        secgrp['GroupId']
        for secgrp
        in client.describe_security_groups()['SecurityGroups']
        if secgrp['GroupName'] == 'default'
        ]
