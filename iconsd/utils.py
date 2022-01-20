from logging import log
import json

import requests
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout


def post_rpc(url: str, payload: dict):
    r = requests.post(url, data=json.dumps(payload))

    if r.status_code != 200:
        log(f"Error {r.status_code} with payload {payload}")
        return None

    return r.json()


def get_preps(url: str):
    payload = {
        "jsonrpc": "2.0",
        "id": 1234,
        "method": "icx_call",
        "params": {
            "to": "cx0000000000000000000000000000000000000000",
            "dataType": "call",
            "data": {
                "method": "getPReps",
                "params": {"startRanking": "0x1", "endRanking": "0xaaa"},
            },
        },
    }
    return post_rpc(url, payload)


def p2p_to_rpc_address(p2p_address):
    return p2p_address.split(":")[0], "9000"


def get_admin_chain(ip_address: str):
    """Get the response from the admin API."""
    url = f"http://{ip_address}:9000/admin/chain/0x1"

    try:
        response = requests.get(url, timeout=1)
    except requests.exceptions.RequestException:
        return None

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_prep_address_peers(ip_address):
    admin_metrics = get_admin_chain(ip_address=ip_address)

    peers = []
    for peer in admin_metrics["module"]["network"]["p2p"]["friends"]:
        peers.append({"ip_address": peer["addr"], "public_key": peer["id"]})

    return peers


def scrape_peers(peers):
    neighbor_peers = []
    for peer in peers:
        neighbor_peers.append(get_prep_address_peers(peer["ip_address"].split(":")[0]))
    return neighbor_peers


def get_peers(peer_set: set, added_peers: list = None):
    """
    Function that takes in a set with a tuple of the ip and node_address as a seed to
    then call that node's orphan peers, call those nodes
    """
    if added_peers is None:
        added_peers = []

    old_peer_count = len(added_peers)

    for i in peer_set.copy():
        if i not in added_peers:
            admin_metrics = get_admin_chain(ip_address=i)
            added_peers.append(i)
        else:
            continue

        if admin_metrics is None:
            continue

        for peer in admin_metrics["module"]["network"]["p2p"]["orphanages"]:

            peer_item = peer["addr"].split(":")[0]

            if peer_item not in peer_set:
                peer_set.add(peer_item)

    if old_peer_count == len(added_peers):
        return peer_set
    else:
        return get_peers(peer_set, added_peers=added_peers)


def check_endpoint_alive(endpoint: str):
    try:
        r = requests.get(endpoint, timeout=1)
    except (ConnectTimeout, ConnectionError, ReadTimeout):
        return False
    if r.status_code == 200:
        return True
    else:
        return False


def reload_config():
    requests.post("http://prometheus:9090/-/reload")
