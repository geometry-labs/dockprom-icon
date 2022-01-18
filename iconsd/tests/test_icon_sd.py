import unittest
from unittest.mock import patch
import os
import json
import yaml

from main import main, get_prometheus_config, replace_config

OUTPUT_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'prometheus.yml')
PEERS_FIXTURE = ['1.2.3.4', '1.2.3.5']


class TestMain(unittest.TestCase):
    def setUp(self):
        os.environ['ICONSD_OUTPUT'] = OUTPUT_FILE

    @patch('main.get_peers')
    @patch('main.reload_config')
    def test_main(self, mock_get_peers, mock_reload_config):
        mock_get_peers.return_value = PEERS_FIXTURE
        main()


class TestUpdatePromConfig(unittest.TestCase):

    def setUp(self):
        with open('test-ips.yaml') as f:
            self.ips = yaml.safe_load(f)

        with open('labels.json') as f:
            self.labels = json.load(f)

    @patch('main.check_endpoint_alive')
    def test_main_get_prometheus_config(self, mock_check):
        mock_check.return_value = True
        out = get_prometheus_config(OUTPUT_FILE, self.ips, self.labels)

        assert len(out['scrape_configs']) > 100

    @patch('main.check_endpoint_alive')
    def test_main_update_config(self, mock_check):
        mock_check.return_value = True
        config = get_prometheus_config(OUTPUT_FILE, self.ips, self.labels)
        replace_config(OUTPUT_FILE, config)
