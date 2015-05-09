import pytoml

from herd.role import get_role_config
from herd.task import TaskRunner


class Herd(object):

    def __init__(self, config_filepath=None):
        if config_filepath is not None:
            self.load_config(config_filepath)

    def load_config(self, filepath):
        with open(filepath) as cfg:
            self.config = pytoml.load(cfg)
            self.task_runner = TaskRunner(self.config)

    def deploy(self, role):
        """
        Given a role, execute commands on all machines as specified
        by definition
        """
        role = get_role_config(self.config, role)
        use_sudo = role.get('sudo', False)
        cluster = role.get('clusters')[0]
        for task in role.get('tasks'):
            self.task_runner.execute_task(task, cluster, use_sudo)
