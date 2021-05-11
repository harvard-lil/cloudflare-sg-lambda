import pytest
import json
import os


@pytest.fixture()
def cloudflare_cidrs():
    with open('tests/cloudflare_cidrs.json', 'r') as f:
        return json.load(f)['result']


@pytest.fixture()
def old_cloudflare_cidrs():
    with open('tests/old_cloudflare_cidrs.json', 'r') as f:
        return json.load(f)['result']


@pytest.fixture()
def sg_ip_permissions():
    with open('tests/sg_ip_permissions.json', 'r') as f:
        return json.load(f)


@pytest.fixture()
def old_sg_ip_permissions():
    with open('tests/old_sg_ip_permissions.json', 'r') as f:
        return json.load(f)


@pytest.fixture()
def ports():
    os.environ['PORTS_LIST'] = '80,443'
