import os
import boto3
import requests
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_cloudflare_ip_list():
    """ Call the Cloudflare API and return a list of IPs """
    response = requests.get('https://api.cloudflare.com/client/v4/ips')
    temp = response.json()
    if 'result' in temp:
        return temp['result']
    raise Exception('Cloudflare response error')


def get_aws_security_group(group_id):
    """ Return the defined Security Group """
    ec2 = boto3.resource('ec2')
    group = ec2.SecurityGroup(group_id)
    if group.group_id == group_id:
        logger.info(f'Got security group {group_id}')
        return group
    raise Exception('Failed to retrieve Security Group')


def add_ipv4_rule(group, address, port):
    """ Add the IP address/port to the security group """
    logger.info(f'Adding {address} : {port}  ')
    group.authorize_ingress(IpProtocol="tcp",
                            CidrIp=address,
                            FromPort=port,
                            ToPort=port)
    logger.info(f'Added {address} : {port}  ')


def delete_ipv4_rule(group, address, port):
    """ Remove the IP address/port from the security group """
    group.revoke_ingress(IpProtocol="tcp",
                         CidrIp=address,
                         FromPort=port,
                         ToPort=port)
    logger.info(f'Removed {address} : {port}  ')


def add_ipv6_rule(group, address, port):
    """ Add the IP address/port to the security group """
    group.authorize_ingress(IpPermissions=[{
        'IpProtocol': "tcp",
        'FromPort': port,
        'ToPort': port,
        'Ipv6Ranges': [
            {
                'CidrIpv6': address
            },
        ]
    }])
    logger.info(f'Added {address} : {port}  ')


def delete_ipv6_rule(group, address, port):
    """ Remove the IP address/port from the security group """
    group.revoke_ingress(IpPermissions=[{
        'IpProtocol': "tcp",
        'FromPort': port,
        'ToPort': port,
        'Ipv6Ranges': [
            {
                'CidrIpv6': address
            },
        ]
    }])
    logger.info(f'Removed {address} : {port}  ')


def lambda_handler(event, context):
    """ AWS Lambda main function """
    protocols = ['ipv4', 'ipv6']

    ports = map(int, os.environ['PORTS_LIST'].split(","))
    if not ports:
        ports = [80]
    logger.info(f'Using ports {", ".join(map(str, ports))}')

    security_group = get_aws_security_group(os.environ['SECURITY_GROUP_ID'])
    rules = security_group.ip_permissions
    for rule in rules:
        logger.info(f"Rule for port {rule['FromPort']} has {len(rule['IpRanges'])} IPv4 ranges and {len(rule['Ipv6Ranges'])} IPv6 ranges")  # noqa

    cf = get_cloudflare_ip_list()
    logger.info(f'Got {len(cf["ipv4_cidrs"])} IPv4 CIDRs and {len(cf["ipv6_cidrs"])} IPv6 CIDRs from Cloudflare')  # noqa

    cf_sets = {}
    for p in protocols:
        cf_sets[p] = {(cidr, port)
                      for cidr in cf['protocol']
                      for port in ports}

    sg_sets = {}
    sg_sets['ipv4'] = {(ip_range['CidrIp'], rule['FromPort'])
                       for rule in rules
                       for ip_range in rule['IpRanges']}
    sg_sets['ipv6'] = {(ip_range['CidrIpv6'], rule['FromPort'])
                       for rule in rules
                       for ip_range in rule['Ipv6Ranges']}

    changes = {
        'add': {},
        'remove': {}
    }

    for p in protocols:
        changes['add'][p] = cf_sets[p].difference(sg_sets[p])
        changes['remove'][p] = sg_sets[p].difference(cf_sets[p])

    for action in ['add', 'remove']:
        for p in protocols:
            for tup in changes[action][p]:
                logger.info(f'I would {action} {tup[0]} on {tup[1]}')
