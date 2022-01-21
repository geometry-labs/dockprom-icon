# icon-dockprom

A monitoring solution for the ICON blockchain based on [dockprom](https://github.com/stefanprodan/dockprom). Comes with built-in service discovery and the ability to add a watch list on a subset of nodes that custom alarms can be configured with. All dockprom configurations are the same besides the custom service discovery for the ICON network. 

By default this tool scrapes both the native goloop metrics along with exporters such as a node exporter for system metrics and cadvisor for container metrics. It comes with some default dashboards though the community is encouraged to build more / make PRs to improve on the existing dashboards.  Additionally, custom alert rules / targets can be configured with a baseline config file with the service discovery agent appending targets to this custom config. 

## Install

Clone this repository on your Docker host, cd into dockprom directory and run compose up:

```bash
git clone https://github.com/geometry-labs/icon-dockprom
cd icon-dockprom
docker-compose up -d
```
The service discovery agent in the default setting will take about 3 min to build the peer list that will be used to scrape metrics.  Be patient while this list is generated, the `prometheus.yml` is updated, and endpoints are scraped. 

Once the stack is up, navigate to `localhost` to view grafana, login with username `admin` / password `admin` which you should immediately change if you are planning on running it publicly. ICON specific dashboards will be automatically detected and should work once the network discovery tool has finished scraping the network. 

## Customization 

### Watch List

By default targets are made for every node on the ICON network by detecting each nodes peers and recursively mapping all the hosts on the network. Custom watch lists can be enabled by modifying the `docker-compose.yml` file in the command comma separated lists for IPs and labels to associate with those IPs. For instance:

```yaml
services:
  iconsd:
    ...
    command: [
      "cron",
      "--watch-list", "1.2.3.4,5.6.7.8"
      "--watch-labels", "foo-node,bar-node"
    ]
```

These IPs will then be scraped and their metrics labeled appropriately. 

### Config

A custom config can be built on from the service discover agent. Simply add the file in the `./prometheus` directory and include it in the iconsd command. For example:

```yaml
services:
  iconsd:
    ...
    command: [
      "cron",
      "--input", "/etc/prometheus/custom-prometheus.yml"
    ]
```

You can also customize the output but this is likely not necessary. 

## Port Mapping 

One change in this configuration from dockprom is that grafana is mapped to port 80 instead of the default 3000. None of the other ports should be publicly accessible when running on a server with the only firewall rule needing to open is port 80. 

## Credits

[dockprom](https://github.com/stefanprodan/dockprom)