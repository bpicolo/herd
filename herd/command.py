from herd import handler


class Command(object):
    """A command is a...command to run on a machine. It knows
    how to parse it's config line and returns a command to run
    on a machine
    """

    def __init__(self, sudo=False):
        self.sudo = sudo

    @property
    def format(self):
        return '{}{}'.format('sudo ' if self.sudo else '', self._format)

    def parse(self, to_parse):
        raise NotImplementedError()

    def run(self, node_handler):
        return handler.execute(node_handler, self.command)


class Install(Command):

    @property
    def _format(self):
        return "apt-get install -y {}"

    def parse(self, to_parse):
        if isinstance(to_parse, list):
            self.command = self.format.format(' '.join(str(s) for s in to_parse))
        else:
            self.command = self.format.format(to_parse)


class Uninstall(Command):

    @property
    def _format(self):
        return "apt-get remove -y {}"

    def parse(self, to_parse):
        if isinstance(to_parse, list):
            self.command = self.format.format(' '.join(str(s) for s in to_parse))
        else:
            self.command = self.format.format(to_parse)


class Upgrade(Command):

    @property
    def _format(self):
        return "apt-get upgrade -y"

    def parse(self):
        self.command = self._format


class Update(Command):

    @property
    def _format(self):
        if self.sudo:
            return "sudo apt-get update -y"
        return "apt-get update -y"

    def parse(self):
        self.command = self._format


class Start(Command):

    @property
    def _format(self):
        return "service {} start"

    def parse(self, to_parse):
        self.command = self.format.format(to_parse)


class Stop(Command):

    @property
    def _format(self):
        return "service {} stop"

    def parse(self, to_parse):
        self.command = self.format.format(to_parse)


class Copy(Command):
    """ A more unique command :D Copy files via scp"""

    @property
    def _format(self):
        raise NotImplementedError("""Copy via scp doesnt work this way""")

    def parse(self, to_parse):
        """
        :param to_parse: a dict with two properties: src and dest
        """
        self.src = to_parse['src']
        self.dest = to_parse['dest']
        self.recursive = to_parse.get('recursive', False)
        return self

    def run(self, node_handler):
        return handler.copy(node_handler, self.src, self.dest, self.recursive)


def parse_command(key, value, sudo=False):
    if key in ['update', 'upgrade']:
        command = COMMANDS[key](sudo)
        command.parse()
        return command
    if key in COMMANDS:
        command = COMMANDS[key](sudo)
        command.parse(value)
        return command
    else:
        print('Unrecognized command %s' % key)


COMMANDS = {
    'start': Start,
    'stop': Stop,
    'update': Update,
    'upgrade': Upgrade,
    'install': Install,
    'uninstall': Uninstall,
    'copy': Copy,
}
