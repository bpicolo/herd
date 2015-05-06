from __future__ import print_function  # Sadly, fixes a flake8 issue

import time
from collections import namedtuple
from concurrent import futures

import paramiko
from scp import SCPClient

import herd.config
from herd.cluster import manager_for_cluster


class ClusterExecutor(namedtuple('ClusterExecutor', [])):

    @staticmethod
    def wait_for_ready(manager, cluster_name):
        cluster_status = manager.cluster_status(cluster_name)
        waited = False
        while(len(cluster_status['new']) > 0):
            waited = True
            print("Waiting for nodes to come online: {}".format(
                [n.name for n in cluster_status['new']]
            ))
            time.sleep(10)
            cluster_status = manager.cluster_status(cluster_name)

        if waited:
            print("Giving the cluster 15 seconds to cool down")
            time.sleep(15)

        if len(cluster_status['off']) or len(cluster_status['archive']):
            nodes = [
                n.name
                for n in cluster_status['off'] + cluster_status['archive']
            ]
            print(
                "WARNING: Some nodes are NOT online. The current commands ",
                "will not be run for them"
            )
            print("Offline nodes: {}".format(nodes))

    @staticmethod
    def execute(command, config, manager, node):
        handler = NodeHandler(config, manager, node)
        print("Executing {} on {}".format(command, node))
        handler.execute(command)

    @staticmethod
    def copy(src, dest, config, manager, node, recursive=False):
        handler = NodeHandler(config, manager, node)
        print("Copying {} to {} on {}".format(src, dest, node))
        handler.copy(src, dest, recursive)

    @staticmethod
    def execute_parallel(config, command, cluster, max_workers=None):
        if not max_workers:
            max_workers = herd.config.parallel_connections(config) or 4

        manager = manager_for_cluster(config, cluster)
        ClusterExecutor.wait_for_ready(manager, cluster)
        nodes = manager.node_names(cluster)

        if not nodes:
            return

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {
                executor.submit(ClusterExecutor.execute, command, config, manager, node): node
                for node in nodes
            }
            for future in futures.as_completed(future_to_node):
                print("COMPLETED {} on {}".format(command, future_to_node[future]))

    @staticmethod
    def copy_parallel(config, src, dest, cluster, max_workers=None, recursive=False):
        if not max_workers:
            max_workers = herd.config.parallel_connections(config) or 4

        manager = manager_for_cluster(config, cluster)
        ClusterExecutor.wait_for_ready(manager, cluster)
        nodes = manager.node_names(cluster)

        if not nodes:
            return

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {
                executor.submit(
                    ClusterExecutor.copy, src, dest,
                    config, manager, node, recursive=recursive
                ): node
                for node in nodes
            }
            for future in futures.as_completed(future_to_node):
                print("COMPLETED copy {} to {} on {}".format(src, dest, future_to_node[future]))


class NodeHandler(namedtuple(
    'NodeHandler',
    ['client', 'cluster_manager', 'node_name'],
)):
    """
    A NodeHandler executes SSH commands against a machine.

    It's designed to be thread safe to run ssh commands in parallel. Turns
    out being immutable makes parallel super crazily easy

    :client: a paramiko SSHClient connection
    :cluster_manager: cluster manager for node
    :node_name: node name of node to talk to
    """

    def __new__(cls, config, cluster_manager, node_name):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            cluster_manager.ip_for_node(node_name),
            key_filename=config['ssh']['path'],
            password=config['ssh']['password'],
            username='root',  # TODO this is clearly suboptimal
        )

        return super(NodeHandler, cls).__new__(cls, client, cluster_manager, node_name)

    def print_stdout(self, stdout):
        for line in stdout:
            print("NODE {}: {}".format(self.node_name, line), end="")

    def execute(self, command):
        """Execute an arbitrary command on the cluster"""
        print("Executing \"{}\" on {}".format(command, self.node_name))
        _, stdout, stderr = self.client.exec_command(command)
        self.print_stdout(stdout)

    def copy(self, src, dest, recursive=False):
        # Context manager doesnt work properly? try later -_-
        scp = SCPClient(self.client.get_transport())
        scp.put(src, dest, recursive=recursive)
