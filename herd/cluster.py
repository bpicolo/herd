import re
import time
from operator import attrgetter

from cached_property import cached_property
import digitalocean


# Represents the configuration options to create a server
class ServerConfig(object):
    pass


class ClusterManager(object):

    def best_node_match(self):
        raise NotImplementedError("")

    def launch_nodes(self):
        pass

    def create(self):
        raise NotImplementedError("")

    def list_nodes(self):
        raise NotImplementedError("")

    def shutdown_node(self):
        raise NotImplementedError("")

    def shutdown_all_nodes(self):
        raise NotImplementedError("")

    def list_regions(self):
        raise NotImplementedError("")

    def sync(self):
        """Sync the config state with cluster state"""
        raise NotImplementedError("")


class DigitalOceanNodeConfig(ServerConfig):

    def __init__(
        self, name, region, size, ssh_keys, image, backups=False, ipv6=False,
        private_networking=False
    ):
        self.name = name
        self.region = region
        self.size = size
        self.image = image
        self.ssh_keys = ssh_keys
        self.backups = backups
        self.ipv6 = ipv6
        self.private_networking = private_networking

    def as_kwargs_dict(self):
        kwargs = {}
        if self.name is not None:
            kwargs['name'] = self.name
        if self.region is not None:
            kwargs['region'] = self.region
        if self.size is not None:
            kwargs['size'] = self.size
        if self.image is not None:
            kwargs['image'] = self.image
        if self.ssh_keys is not None:
            kwargs['ssh_keys'] = self.ssh_keys
        if self.backups is not None:
            kwargs['backups'] = self.backups
        if self.ipv6 is not None:
            kwargs['ipv6'] = self.ipv6
        if self.private_networking is not None:
            kwargs['private_networking'] = self.private_networking

        return kwargs


class ClusterSyncException(Exception):
    pass


class DigitalOceanClusterManager(ClusterManager):

    def __init__(self, config):
        self.token = config['providers']['digitalocean']['token']
        self.manager = digitalocean.Manager(token=self.token)
        self.config = config

    @property
    def provider(self):
        return 'digitalocean'

    def parse_config(self):
        pass

    def default_region(self):
        return 'sfo1'

    def parse_node_size_config(self, cfg):
        return {
            'min_cores': cfg.get('min_cores', 1),
            'min_ram': cfg.get('min_ram', 256),
            'min_disk': cfg.get('min_disk', 10),
            'max_monthly_cost': cfg.get('max_monthly_cost', 20),
        }

    def size_for_slug(self, slug):
        return next(
            (
                size for size in self.sizes_list
                if size.slug == slug
            ),
            None,
        )

    def size_meets_requirements(self, size, min_cores, min_ram, min_disk, max_monthly_cost):
        return all((
            size.vcpus >= min_cores,
            size.memory >= min_ram,
            size.disk >= min_disk,
            size.price_monthly <= max_monthly_cost,
        ))

    def best_node_size_match(self, min_cores, min_ram, min_disk, max_monthly_cost):
        """
        :param min_cores: int Fewest cores allowable for machine (aka vcpu) default = 1
        :param min_ram: int Least memory allowed (in MB) default = 512
        :param min_disk: int Least disk allowed (in GB) default = 20
        :param max_monthly_cost: int Highest monthly price allowed default = 5

        :return: digitalocean.Size.Size
        """
        all_matching = [
            size for size in self.sizes_list
            if self.size_meets_requirements(size, min_cores, min_ram, min_disk, max_monthly_cost)
        ]

        return next(iter(sorted(all_matching, key=attrgetter("price_monthly"))), None)

    def rename_node(self, node, new_name):
        node.rename(new_name)

    def launch_node(self, node_configuration):
        """
        :param size: digitalocean.Size.Size
        """
        print("Launching node {}".format(node_configuration.name))
        droplet = digitalocean.Droplet(
            token=self.token,
            **node_configuration.as_kwargs_dict()
        )

        droplet.create()
        return droplet

    def destroy_node(self, node):
        if node.status == 'new':
            print("Can't destroy node {} yet, it's currently being created".format(node.name))

        print("Destroying node id:{} name:{}".format(node.id, node.name))
        node.destroy()

    def destroy_nodes(self, nodes):
        for node in nodes:
            self.destroy_node(node)

    def shutdown(self, node):
        node.shutdown()

    def node_in_cluster(self, cluster):
        cluster_name_scheme = '{}\d+'.format(cluster)
        return [
            n for n in self.nodes_list
            if re.match(cluster_name_scheme, n.name)
        ]

    def node_index(self, cluster_name, node_name):
        cluster_name_scheme = '{}(\d+)'.format(cluster_name)
        return int(re.findall(cluster_name_scheme, node_name)[0])

    @cached_property
    def nodes_list(self):
        return self._nodes_list()

    def _nodes_list(self):
        return self.manager.get_all_droplets()

    @cached_property
    def regions_list(self):
        return self.manager.get_all_regions()

    @cached_property
    def sizes_list(self):
        return self.manager.get_all_sizes()

    @cached_property
    def images_list(self):
        return self.manager.get_all_images()

    def list_clusters(self, cluster_name):
        pass

    def destroy_cluster(self, cluster_name):
        nodes_in_cluster = self.node_in_cluster(cluster_name)

        if not nodes_in_cluster:
            print("No nodes found in cluster {}, taking no action.".format(cluster_name))
            return

        self.destroy_nodes(nodes_in_cluster)

    def cluster_info(self, cluster_name):
        nodes_in_cluster = self.node_in_cluster(cluster_name)

        if not nodes_in_cluster:
            print("No nodes found in cluster {}".format(cluster_name))
            return

        return [
            {
                'name': node.name,
                'public_ips': node.ip_address,
                'private_ips': node.private_ip_address,
                'status': node.status
            }
            for node in nodes_in_cluster
        ]

    def cluster_status(self, cluster_name):
        nodes = self._nodes_list()

        def filter_nodes(status):
            def filter_node(node):
                return (
                    node.status == status and
                    re.match('{}\d+'.format(cluster_name), node.name)
                )

            return filter_node

        return {
            'active': list(filter(filter_nodes('active'), nodes)),
            'new': list(filter(filter_nodes('new'), nodes)),
            'off': list(filter(filter_nodes('off'), nodes)),
            'archive': list(filter(filter_nodes('archive'), nodes)),
        }

    def node_names(self, cluster_name):
        return [c['name'] for c in self.cluster_info(cluster_name)]

    def name_for_node(self, cluster_name, idx):
        return '{}{}'.format(cluster_name, idx)

    def ip_for_node(self, node_name):
        return next(
            (
                node.ip_address
                for node in self.nodes_list
                if node.name == node_name
            ),
            None
        )

    def stop_cluster(self, cluster_name, cluster_config):
        nodes_in_cluster = self.node_in_cluster(cluster_name)
        for node in nodes_in_cluster:
            self.shutdown(node)

    def start_cluster(self, cluster_name, cluster_config):
        """Refactor this. Gross"""
        print('Syncing cluster: {}'.format(cluster_name))
        nodes_in_cluster = self.node_in_cluster(cluster_name)
        node_size_config = self.parse_node_size_config(cluster_config)
        node_size = self.best_node_size_match(**node_size_config)
        desired_count = cluster_config['server_count']

        if any(node.status == 'new' for node in nodes_in_cluster):
            print(
                'Can\'t modify cluster {} right now, '
                'nodes currently spawning'.format(cluster_name)
            )

        if not node_size:
            raise ClusterSyncException(
                (
                    'No valid node was found matching cores: {min_cores}, '
                    'ram: {min_ram}mb, disk: {min_disk}gb, cost: ${max_monthly_cost}'
                ).format(**node_size_config)
            )

        def destroy_nonmatching_node(node):
            meets_size_requirements = self.size_meets_requirements(
                self.size_for_slug(node.size_slug), **node_size_config
            )
            if not meets_size_requirements:
                print(
                    'Destroying node {} - doesn\'t meet size requirement'.format(
                        node.name,
                    )
                )
                self.destroy_node(node)

            return meets_size_requirements

        # Remove nodes if they dont match size config & sort by name
        nodes_in_cluster = list(sorted(
            filter(destroy_nonmatching_node, nodes_in_cluster),
            key=attrgetter('name'),
        ))

        if len(nodes_in_cluster) > desired_count:
            print('Destroying extraneous nodes')
            for node in nodes_in_cluster[desired_count:]:
                self.destroy_node(node)
            nodes_in_cluster == nodes_in_cluster[:desired_count]

        # Rename nodes if nonsequential
        for idx, node in enumerate(nodes_in_cluster, start=1):
            name_for_node = self.name_for_node(cluster_name, idx)
            if name_for_node != node.name:
                self.rename_node(node, name_for_node)

        for idx in range(len(nodes_in_cluster), desired_count):
            node_configuration = DigitalOceanNodeConfig(
                name=self.name_for_node(cluster_name, idx + 1),
                region=cluster_config.get('region', self.default_region()),
                size=self.best_node_size_match(**node_size_config).slug,
                image=cluster_config.get('image', None),
                ssh_keys=cluster_config.get('ssh_keys', None),
                backups=cluster_config.get('backups', False),
                ipv6=cluster_config.get('ipv6', False),
                private_networking=cluster_config.get('private_networking', False),
            )
            self.launch_node(node_configuration)

        print('Cluster %s is operational!' % cluster_name)

    def start(self, cluster_name):
        cluster_config = self.config['clusters'].get(cluster_name)
        if not cluster_config:
            print('Config not found for cluster %s ' % cluster_name)
        elif cluster_config['provider'] != self.provider:
            print('The provider for %s is not %s' % (cluster_name, self.provider))
        else:
            self.start_cluster(cluster_name, cluster_config)

    def stop(self, cluster_name):
        cluster_config = self.config['clusters'].get(cluster_name)
        if not cluster_config:
            print('Config not found for cluster %s ' % cluster_name)
        elif cluster_config['provider'] != self.provider:
            print('The provider for %s is not %s' % (cluster_name, self.provider))
        else:
            self.stop_cluster(cluster_name, cluster_config)

    def wait_for_ready(self, cluster_name):
        cluster_status = self.cluster_status(cluster_name)
        waited = False
        while(len(cluster_status['new']) > 0):
            waited = True
            print('Waiting for nodes to come online: {}'.format(
                [n.name for n in cluster_status['new']]
            ))
            time.sleep(10)
            cluster_status = self.cluster_status(cluster_name)

        if waited:
            print('Giving the cluster 15 seconds to cool down')
            time.sleep(15)

        if len(cluster_status['off']) or len(cluster_status['archive']):
            nodes = [
                n.name
                for n in cluster_status['off'] + cluster_status['archive']
            ]
            print(
                'WARNING: Some nodes are NOT online, and commands cannot ',
                'be run on them'
            )
            print('Offline nodes: {}'.format(nodes))


PROVIDER_TO_CLUSTER_MANAGER = {
    'digitalocean': DigitalOceanClusterManager
}


def cluster_manager_for_provider(provider):
    if provider not in PROVIDER_TO_CLUSTER_MANAGER:
        raise ValueError('provider must be one of {}'.format(PROVIDER_TO_CLUSTER_MANAGER.keys()))
    return PROVIDER_TO_CLUSTER_MANAGER[provider]


def manager_for_cluster(config, cluster_name):
    return cluster_manager_for_provider(
        config['clusters'][cluster_name]['provider']
    )(config)
