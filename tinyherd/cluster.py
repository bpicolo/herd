import re
from operator import attrgetter

from cached_property import cached_property
import digitalocean


# Represents the configuration options to create a server
class ServerConfig:
    pass


class ClusterManager:

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
            return

        print("Destroying node id:{} name:{}".format(node.id, node.name))
        node.destroy()

    def destroy_nodes(self, nodes):
        for node in nodes:
            self.destroy_node(node)

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

    def drop_cluster(self, cluster_name):
        cluster_name_scheme = '{}\d+-'.format(cluster_name)
        nodes_in_cluster = [
            n for n in self.nodes_list
            if re.match(cluster_name_scheme, n.name)
        ]

        if not nodes_in_cluster:
            print("No nodes found in cluster {}, taking no action.".format(cluster_name))
            return

        self.destroy_nodes(nodes_in_cluster)

    def cluster_info(self, cluster_name):
        cluster_name_scheme = '{}\d+-'.format(cluster_name)
        nodes_in_cluster = [
            n for n in self.nodes_list
            if re.match(cluster_name_scheme, n.name)
        ]

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

    def node_names(self, cluster_name):
        return [c['name'] for c in self.cluster_info(cluster_name)]

    def ip_for_node(self, node_name):
        return next(
            (
                node.ip_address
                for node in self.nodes_list
                if node.name == node_name
            ),
            None
        )

    def sync_cluster(self, cluster_name, cluster_config):
        print("Syncing cluster: {}".format(cluster_name))
        region = cluster_config.get('region', self.default_region())
        cluster_name_scheme = '{}\d+-{}'.format(cluster_name, region)
        nodes_in_cluster = [
            n for n in self.nodes_list
            if re.match(cluster_name_scheme, n.name)
        ]

        node_size_config = self.parse_node_size_config(cluster_config)
        node_size = self.best_node_size_match(**node_size_config)
        if not node_size:
            raise ClusterSyncException(
                (
                    "No valid node was found matching cores: {min_cores}, "
                    "ram: {min_ram}mb, disk: {min_disk}gb, cost: ${max_monthly_cost}"
                ).format(
                    **node_size_config
                )
            )

        nodes_to_sync = [
            '{}{}-{}'.format(cluster_name, i, region)
            for i in range(1, 1 + cluster_config['server_count'])
        ]

        nodes_to_destroy = [
            node for node in nodes_in_cluster if not
            self.size_meets_requirements(self.size_for_slug(node.size_slug), **node_size_config)
        ]

        if nodes_to_destroy:
            print("Destroying nodes that don't meet new size requirements")
            self.destroy_nodes(nodes_to_destroy)

        destroyed_node_names = set(node.name for node in nodes_to_destroy)
        start_node_names = set(node.name for node in nodes_in_cluster)
        nodes_to_create = (
            set(nodes_to_sync) - set(start_node_names) |
            set(destroyed_node_names)
        )
        for node_name in nodes_to_create:
            node_configuration = DigitalOceanNodeConfig(
                name=node_name,
                region=region,
                size=self.best_node_size_match(**node_size_config).slug,
                image=cluster_config.get('image', None),
                ssh_keys=cluster_config.get('ssh_keys', None),
                backups=cluster_config.get('backups', False),
                ipv6=cluster_config.get('ipv6', False),
                private_networking=cluster_config.get('private_networking', False),
            )
            self.launch_node(node_configuration)

        print("Cluster %s is in sync!" % cluster_name)

    def sync(self):
        for cluster_name, cluster_config in self.config['clusters'].items():
            if cluster_config['provider'] == 'digitalocean':
                self.sync_cluster(cluster_name, cluster_config)


PROVIDER_TO_CLUSTER_MANAGER = {
    'digitalocean': DigitalOceanClusterManager
}


def cluster_manager_for_provider(provider):
    if provider not in PROVIDER_TO_CLUSTER_MANAGER:
        raise ValueError('provider must be one of {}'.format(PROVIDER_TO_CLUSTER_MANAGER.keys()))
    return PROVIDER_TO_CLUSTER_MANAGER[provider]
