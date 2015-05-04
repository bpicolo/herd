import pytoml

from herd.cluster import cluster_manager_for_provider
from herd.handler import NodeHandler


class Herd(object):

    def load_config(self, filepath):
        with open(filepath) as cfg:
            self.config = pytoml.load(cfg)
