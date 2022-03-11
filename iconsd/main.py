#!/usr/bin/env python3
import sys
import argparse
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


def get_prometheus_config(input_config: str, ips: list, labels: dict):
    # Load the prom config
    with open(input_config) as f:
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

            # TODO: https://github.com/sudoblockio/icon-dockprom/issues/1
            # RM the check_endpoint due to ^^
            # Need to append metrics for the check but then prom infers this after
            # if check_endpoint_alive('http://' + endpoint + '/metrics'):
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


def main(url: str = None,
         input: str = None,
         output: str = None,
         watch_list: str = None,
         watch_labels: str = None,
         **kwargs):
    logging.warning("Starting icon service discovery...")

    labels = []
    if watch_list:
        ips = watch_list.split(',')
        if watch_labels:
            labels = {v: watch_labels[i] for i, v in enumerate(ips)}
    else:
        seed_nodes = get_preps(url)
        labels = {i['p2pEndpoint'].split(':')[0]: i['name'] for i in
                  seed_nodes['result']['preps']}
        ips = {i['p2pEndpoint'].split(':')[0] for i in seed_nodes['result']['preps']}
        ips = get_peers(ips)

    logging.warning(f"Found {len(ips)} ips.")
    config = get_prometheus_config(input_config=input, ips=ips, labels=labels)
    replace_config(output, config)
    reload_config()
    logging.warning(f"Reloaded config.")


def cron(sleep_time: int, **kwargs):
    while True:
        main(**kwargs)
        logging.warning(f"Sleeping.")
        sleep(int(sleep_time))


def cli(raw_args=None):
    if raw_args is None:
        raw_args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="ICON Service Discovery")
    parser.add_argument(
        dest='action',
        type=str,
        default=None,
        help="The action to take - one of `cron` to run continuously or `run` to run once",
    )
    parser.add_argument(
        '--url',
        '-u',
        type=str,
        metavar="",
        default='https://ctz.solidwallet.io/api/v3',
        help="The ICON node url - defaults to https://ctz.solidwallet.io/api/v3.",
    )
    parser.add_argument(
        '--input',
        '-i',
        type=str,
        metavar="",
        default='/etc/prometheus/prometheus.yml',
        help="The input file path for the prometheus.yml - defaults to "
             "/etc/prometheus/prometheus.yml which is mounted in both prom and iconsd. "
             "Change this to another file if you want to have a baseline config that "
             "you don't want to modify.",
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        metavar="",
        default='/etc/prometheus/prometheus.yml',
        help="The output file path for the prometheus.yml - defaults to input.",
    )
    parser.add_argument(
        '--sleep-time',
        '-s',
        type=int,
        metavar="",
        default=3600,
        help="If running cron, the sleep time to run.",
    )
    parser.add_argument(
        '--watch-list',
        type=str,
        metavar="",
        help="A list of comma separated IPs to constrain the watch list. Overrides "
             "doing peer discovery and just uses those IPs.",
    )
    parser.add_argument(
        '--watch-labels',
        type=str,
        metavar="",
        help="A list of comma separated labels to associate with the watch-list, "
             "applied in the same order as the input IPs for watch list.",
    )
    args, unknown_args = parser.parse_known_args(raw_args)

    if 'cron' in args.action:
        cron(**vars(args))
    elif 'run' in args.action:
        main(**vars(args))


if __name__ == '__main__':
    cli(sys.argv[1:])
