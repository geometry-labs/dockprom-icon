import yaml
import json
import unittest

import utils


class TestUtils(unittest.TestCase):

    def setUp(self):
        with open('test-ips.yaml') as f:
            self.ips = yaml.safe_load(f)

        with open('labels.json') as f:
            self.labels = json.load(f)

    def test_check_endpoint_alive(self):
        assert utils.check_endpoint_alive('http://44.231.14.116:9000/metrics')

    def test_get_peers(self):
        peers = utils.get_peers(set(self.ips))
        assert len(peers) > 150
