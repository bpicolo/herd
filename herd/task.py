from herd.command import COMMANDS


class TaskRunner(object):

    def __init__(self, config):
        self.config = config
        self.tasks = self.config.get('tasks', {})

    def task_config(self, task_name):
        return self.tasks[task_name]

    def commands_for_task(self, task_name, sudo=False):
        config = self.task_config(task_name)
        dependencies = config.pop('dependencies', [])
        commands = []
        for key, value in config.items():
            if key in COMMANDS:
                commands.append(COMMANDS[key](sudo).command(value))
            else:
                print('Unrecognized command %s' % key)

        if isinstance(dependencies, str):
            dependencies = [dependencies]

        for dep in dependencies:
            assert dep != task_name, "%s depends on itself" % task_name
            commands += self.commands_for_task(dep, sudo)

        return commands
