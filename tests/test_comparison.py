from lambda_function import determine_changes


def test_no_changes_now(cloudflare_cidrs, sg_ip_permissions, ports):
    changes = determine_changes(cloudflare_cidrs, sg_ip_permissions)
    assert len(changes.keys()) == 2
    for action in changes.keys():
        assert len(changes[action].keys()) == 2
        assert 'ipv4' in changes[action].keys()
        assert 'ipv6' in changes[action].keys()
        assert changes[action]['ipv4'] == set()
        assert changes[action]['ipv6'] == set()


def test_no_changes_then(old_cloudflare_cidrs, old_sg_ip_permissions, ports):
    changes = determine_changes(old_cloudflare_cidrs, old_sg_ip_permissions)
    assert len(changes.keys()) == 2
    for action in changes.keys():
        assert len(changes[action].keys()) == 2
        assert 'ipv4' in changes[action].keys()
        assert 'ipv6' in changes[action].keys()
        assert changes[action]['ipv4'] == set()
        assert changes[action]['ipv6'] == set()


def test_changes(cloudflare_cidrs, old_sg_ip_permissions, ports):
    changes = determine_changes(cloudflare_cidrs, old_sg_ip_permissions)
    assert len(changes.keys()) == 2
    for action in changes.keys():
        assert len(changes[action].keys()) == 2
        assert 'ipv4' in changes[action].keys()
        assert 'ipv6' in changes[action].keys()
        assert changes[action]['ipv6'] == set()
    assert changes['remove']['ipv4'] == {('104.16.0.0/12', 80),
                                         ('104.16.0.0/12', 443)}
    assert changes['add']['ipv4'] == {('104.16.0.0/13', 80),
                                      ('104.16.0.0/13', 443),
                                      ('104.24.0.0/14', 80),
                                      ('104.24.0.0/14', 443)}


def test_reverse_changes(old_cloudflare_cidrs, sg_ip_permissions, ports):
    changes = determine_changes(old_cloudflare_cidrs, sg_ip_permissions)
    assert len(changes.keys()) == 2
    for action in changes.keys():
        assert len(changes[action].keys()) == 2
        assert 'ipv4' in changes[action].keys()
        assert 'ipv6' in changes[action].keys()
        assert changes[action]['ipv6'] == set()
    assert changes['add']['ipv4'] == {('104.16.0.0/12', 80),
                                      ('104.16.0.0/12', 443)}
    assert changes['remove']['ipv4'] == {('104.16.0.0/13', 80),
                                         ('104.16.0.0/13', 443),
                                         ('104.24.0.0/14', 80),
                                         ('104.24.0.0/14', 443)}
