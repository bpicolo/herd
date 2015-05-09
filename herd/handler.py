from __future__ import print_function  # Sadly, fixes a flake8 issue

from collections import namedtuple
from concurrent import futures

import paramiko
from scp import SCPClient

import herd.config
from herd.cluster import manager_for_cluster


class ClusterExecutor(namedtuple('ClusterExecutor', [])):

    @staticmethod
    def execute(commands, config, manager, node):
        handler = NodeHandler.connect(config, manager.ip_for_node(node))
        for command in commands:
            print("Executing {} on {}".format(command.command, node))
            for out in command.run(handler):
                print("{}: {}".format(node, out))

    @staticmethod
    def execute_parallel(config, command, cluster, max_workers=None):
        if not max_workers:
            max_workers = herd.config.parallel_connections(config) or 4

        manager = manager_for_cluster(config, cluster)
        manager.wait_for_ready(cluster)
        nodes = manager.node_names(cluster)

        if not nodes:
            return

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {
                executor.submit(ClusterExecutor.execute, command, config, manager, node): node
                for node in nodes
            }
            for future in futures.as_completed(future_to_node):
                print("COMPLETED commands on {}".format(future_to_node[future]))


class NodeHandler(namedtuple(
    'NodeHandler',
    ['client', 'ip_address'],
)):
    """
    A NodeHandler executes SSH commands against a machine.

    It's designed to be thread safe to run ssh commands in parallel. Turns
    out being immutable makes parallel super crazily easy

    :client: a paramiko SSHClient connection
    :cluster_manager: cluster manager for node
    :node_name: node name of node to talk to
    """

    @classmethod
    def connect(cls, config, ip_address):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            ip_address,
            key_filename=config['ssh']['path'],
            password=config['ssh']['password'],
            username='root',  # TODO this is clearly suboptimal
        )

        return cls(client, ip_address)


def execute(handler, command):
    """
    :param client: NodeHandler
    :command: string, command to execute on remote machine
    """
    _, stdout, stderr = handler.client.exec_command(command)
    for line in stdout:
        yield line.rstrip()


def copy(handler, src, dest, recursive=False):
    """
    :param client: NodeHandler
    :param src: source file path (local)
    :param dest: destination file path (remote)
    :recursive: folder + all subfolders, files?
    """
    # Context manager doesnt work properly? try later -_-
    scp = SCPClient(handler.client.get_transport())
    scp.put(src, dest, recursive=recursive)
