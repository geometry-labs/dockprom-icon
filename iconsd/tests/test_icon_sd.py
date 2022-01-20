import unittest
from unittest.mock import patch
import os
import json
import yaml

from main import main, get_prometheus_config, replace_config, cli

INPUT_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'prometheus.yml')
PEERS_FIXTURE = ['1.2.3.4', '1.2.3.5']


class TestCli(unittest.TestCase):
    @patch('main.main')
    def test_cli_cron(self, mock_run):
        mock_run.return_value = True
        cli(['run', '-i', INPUT_FILE, '-o', INPUT_FILE + '.test'])

    @patch('main.cron')
    def test_cli_main(self, mock_cron):
        mock_cron.return_value = True
        cli(['main', '-i', INPUT_FILE, '-o', INPUT_FILE + '.test'])


class TestMain(unittest.TestCase):
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
        out = get_prometheus_config(INPUT_FILE, self.ips, self.labels)

        assert len(out['scrape_configs']) > 6

    @patch('main.check_endpoint_alive')
    def test_main_update_config(self, mock_check):
        mock_check.return_value = True
        config = get_prometheus_config(INPUT_FILE, self.ips, self.labels)
        replace_config(INPUT_FILE, config)
