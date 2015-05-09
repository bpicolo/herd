from herd.command import parse_command
from herd.handler import ClusterExecutor


class TaskRunner(object):

    def __init__(self, config):
        self.config = config
        self.tasks = self.config.get('tasks', {})

    def task_config(self, task_name):
        return self.tasks[task_name]

    def commands_for_task(self, task_name, sudo=False):
        config = self.task_config(task_name)
        dependencies = config.pop('dependencies', [])
        commands = list(filter(
            None,
            [
                parse_command(key, value, sudo)
                for key, value in config.items()
            ]
        ))

        if isinstance(dependencies, str):
            dependencies = [dependencies]

        for dep in dependencies:
            assert dep != task_name, "%s depends on itself" % task_name
            commands += self.commands_for_task(dep, sudo)

        return commands

    def execute_task(self, task, cluster, sudo=False):
        commands = self.commands_for_task(task, sudo=sudo)
        ClusterExecutor.execute_parallel(self.config, commands, cluster)
