import argparse
import sys

import pytoml

from tinyherd.cluster import cluster_manager_for_provider


def load_config(config_path):
    with open(config_path) as cfg:
        return pytoml.load(cfg)


def sync_all_clusters(args):
    parser = argparse.ArgumentParser(description='Cluster config runner')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    for cluster in config['clusters'].values():
        manager = cluster_manager_for_provider(cluster['provider'])(config)
        manager.sync()


def drop_cluster(args):
    parser = argparse.ArgumentParser(description='Cluster config runner')
    parser.add_argument('cluster', action='store', help='Cluster name to destroy all nodes for')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    for provider in config['providers']:
        manager = cluster_manager_for_provider(provider)(config)
        manager.drop_cluster(args.cluster)


def sync_cluster(args):
    parser = argparse.ArgumentParser(description='Cluster config runner')
    parser.add_argument('cluster', action='store', help='Name of cluster to sync')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    manager = cluster_manager_for_provider(config[args.cluster]['provider'])(config)
    manager.sync()


action_to_handler = {
    'syncall': sync_all_clusters,
    'sync': sync_cluster,
    'destroy': drop_cluster,
}


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd not in action_to_handler:
        print("action must be one of {}".format(action_to_handler.keys()))
        sys.exit(1)

    action_to_handler[cmd](sys.argv[2:])
