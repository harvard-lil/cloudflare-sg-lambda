import os
import boto3
import requests
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_cloudflare_ip_list():
    """ Call the Cloudflare API and return a list of IPs """
    response = requests.get('https://api.cloudflare.com/client/v4/ips')
    try:
        return response.json()['result']
    except KeyError:
        raise Exception('Cloudflare response error')


def get_aws_security_group(group_id):
    """ Return the defined Security Group """
    ec2 = boto3.resource('ec2')
    group = ec2.SecurityGroup(group_id)
    if group.group_id == group_id:
        return group
    raise Exception('Failed to retrieve Security Group')


def change_ipv4_rule(action, group, address, port):
    """ Add/remove the IP address/port to/from the security group """
    kwargs = {
        'IpProtocol': 'tcp',
        'CidrIp': address,
        'FromPort': port,
        'ToPort': port
    }
    if action == 'add':
        group.authorize_ingress(**kwargs)
    elif action == 'remove':
        group.revoke_ingress(**kwargs)
    else:
        raise Exception('Invalid action')
    logger.info(f'{action}: {address}:{port}')


def change_ipv6_rule(action, group, address, port):
    """ Add/remove the IP address/port to/from the security group """
    if action == 'add':
        func = group.authorize_ingress
    elif action == 'remove':
        func = group.revoke_ingress
    else:
        raise Exception('Invalid action')
    func(IpPermissions=[{
        'IpProtocol': "tcp",
        'FromPort': port,
        'ToPort': port,
        'Ipv6Ranges': [
            {
                'CidrIpv6': address
            },
        ]
    }])
    logger.info(f'{action}: {address}:{port}')


def lambda_handler(event, context):
    """ AWS Lambda main function """
    protocols = ['ipv4', 'ipv6']

    ports = list(map(int, os.environ['PORTS_LIST'].split(",")))
    if not ports:
        ports = [80]

    security_group = get_aws_security_group(os.environ['SECURITY_GROUP_ID'])
    rules = security_group.ip_permissions

    cf = get_cloudflare_ip_list()

    cf_sets = {
        p: {(cidr, port)
            for cidr in cf[f'{p}_cidrs']
            for port in ports}
        for p in protocols
    }

    sg_sets = {
        'ipv4': {(ip_range['CidrIp'], rule['FromPort'])
                 for rule in rules
                 for ip_range in rule['IpRanges']},
        'ipv6': {(ip_range['CidrIpv6'], rule['FromPort'])
                 for rule in rules
                 for ip_range in rule['Ipv6Ranges']}
    }

    changes = {k: {} for k in ['add', 'remove']}

    for p in protocols:
        changes['add'][p] = cf_sets[p] - sg_sets[p]
        changes['remove'][p] = sg_sets[p] - cf_sets[p]

    for action in changes.keys():
        for cidr, port in changes[action]['ipv4']:
            change_ipv4_rule(action, security_group, cidr, port)
        for cidr, port in changes[action]['ipv6']:
            change_ipv6_rule(action, security_group, cidr, port)
