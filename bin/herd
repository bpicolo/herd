import argparse
import sys

import pytoml

from herd.cluster import cluster_manager_for_provider
from herd.cluster import manager_for_cluster
from herd.command import UbuntuCommand
from herd.handler import ClusterExecutor


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
    manager_for_cluster(config, args.cluster).sync()


def cluster_info(args):
    parser = argparse.ArgumentParser(description='Cluster config runner')
    parser.add_argument('cluster', action='store', help='Name of cluster to sync')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    manager = manager_for_cluster(config, args.cluster)
    print(manager.cluster_info(args.cluster))


def cluster_install(args):
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to install program on')
    parser.add_argument('program', action='store', help='Name of program to install')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(UbuntuCommand.install(args.program), config, args.cluster)


def cluster_uninstall(args):
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to uninstall program on')
    parser.add_argument('program', action='store', help='Name of program to uninstall')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(
        UbuntuCommand.uninstall(args.program), config, args.cluster
    )


def postsync(args):
    """Run commands that should happen after a machine is synced"""
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to install program on')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(UbuntuCommand.update(sudo=True), config, args.cluster)
    ClusterExecutor.execute_parallel(UbuntuCommand.upgrade(sudo=True), config, args.cluster)


def start(args):
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to start program on')
    parser.add_argument('program', action='store', help='Name of program to start')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(
        UbuntuCommand.service_start(args.program), config, args.cluster
    )


def stop(args):
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to stop program on')
    parser.add_argument('program', action='store', help='Name of program to stop')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(
        UbuntuCommand.service_stop(args.program), config, args.cluster
    )


def execute(args):
    parser = argparse.ArgumentParser(description='Install program on all nodes in a luster')
    parser.add_argument('cluster', action='store', help='Name of cluster to stop program on')
    parser.add_argument('command', action='store', help='Name of program to stop', nargs='+')
    parser.add_argument('--config', action='store', help='Specify path to config file', default="config.toml")
    args = parser.parse_args(args)

    config = load_config(args.config)
    ClusterExecutor.execute_parallel(" ".join(args.command), config, args.cluster)


action_to_handler = {
    'syncall': sync_all_clusters,
    'sync': sync_cluster,
    'destroy': drop_cluster,
    'info': cluster_info,
    'install': cluster_install,
    'uninstall': cluster_uninstall,
    'start': start,
    'stop': stop,
    'postsync': postsync,
    'exec': execute,
}


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd not in action_to_handler:
        print("action must be one of {}".format(action_to_handler.keys()))
        sys.exit(1)

    action_to_handler[cmd](sys.argv[2:])
