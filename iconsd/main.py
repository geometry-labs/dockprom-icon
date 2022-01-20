#!/usr/bin/env python3
import logging
import os
import yaml
from time import sleep

from utils import get_preps, get_peers, check_endpoint_alive, reload_config

METRICS = [
    {
        'job_name': 'goloop',
        'port': '9000',
        'static_configs': []
    },
    {
        'job_name': 'node_exporter_icon',
        'port': '9100',
        'static_configs': []
    },
    {
        'job_name': 'cadvisor_icon',
        'port': '8080',
        'static_configs': []
    },
]


def get_prometheus_config(config_path: str, ips: list, labels: dict):
    # Load the prom config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # All the targets will be updated except for persistent ones from this file
    with open(os.path.join(os.path.dirname(__file__),
                           'persistent-scrape-configs.yml')) as f:
        persistent_scrape = yaml.safe_load(f)

    static_configs = []

    for i in ips:
        if i in labels:
            prep_label = labels[i].replace(" ", "")
            is_prep = True
        else:
            prep_label = f"{i}"
            is_prep = False

        for m in METRICS:
            endpoint = i + f':{m["port"]}'
            # Need to append metrics for the check but then prom infers this after
            if check_endpoint_alive('http://' + endpoint + '/metrics'):
                m['static_configs'].append({
                        'targets': [endpoint],
                        'labels': {
                            'is_prep': is_prep,
                            'prep_name': prep_label,
                        }
                    }
                )

    # Put the scrape configs into jobs
    for m in METRICS:
        """
        - job_name: nodeexporter
          scrape_interval: 5s
          static_configs:
        """
        static_configs.append({
            'job_name': m['job_name'],
            'scrape_interval': '5s',
            'static_configs': m['static_configs']
        })


    config.pop('scrape_configs')
    config['scrape_configs'] = persistent_scrape['scrape_configs'] + static_configs

    return config


def replace_config(config_path: str, config: dict):
    with open(config_path, 'w') as f:
        yaml.dump(config, f)


def main():
    logging.warning("Starting icon service discovery...")

    url = os.getenv('ICON_NODE_URL', 'https://ctz.solidwallet.io/api/v3')
    output = os.getenv('ICONSD_OUTPUT', '/etc/prometheus/prometheus.yml')

    seed_nodes = get_preps(url)

    labels = {i['p2pEndpoint'].split(':')[0]: i['name'] for i in
              seed_nodes['result']['preps']}
    ips = {i['p2pEndpoint'].split(':')[0] for i in seed_nodes['result']['preps']}
    logging.warning(f"Found {len(ips)} ips seeds.")

    peers = get_peers(ips)
    logging.warning(f"Found {len(peers)} ips peers.")

    config = get_prometheus_config(output, peers, labels)
    replace_config(output, config)
    reload_config()
    logging.warning(f"Reloaded config.")


def cron():
    sleep_time = os.getenv('SLEEP_TIME', 3600)
    while True:
        main()
        logging.warning(f"Sleeping.")
        sleep(int(sleep_time))


if __name__ == '__main__':
    cron()
