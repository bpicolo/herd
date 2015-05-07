

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

    def command(self, to_parse):
        raise NotImplementedError()


class Install(Command):

    @property
    def _format(self):
        return "apt-get install -y {}"

    def command(self, to_parse):
        if isinstance(to_parse, list):
            return self.format.format(' '.join(str(s) for s in to_parse))
        else:
            return self.format.format(to_parse)


class Uninstall(Command):

    @property
    def _format(self):
        return "apt-get remove -y {}"

    def command(self, to_parse):
        if isinstance(to_parse, list):
            return self.format.format(' '.join(str(s) for s in to_parse))
        else:
            return self.format.format(to_parse)


class Upgrade(Command):

    @property
    def _format(self):
        return "apt-get upgrade -y"

    def command(self):
        return self.format()


class Update(Command):

    @property
    def _format(self):
        if self.sudo:
            return "sudo apt-get update -y"
        return "apt-get update -y"

    def command(self):
        return self._format()


class Start(Command):

    @property
    def _format(self):
        return "service {} start"

    def command(self, to_parse):
        return self.format.format(to_parse)


class Stop(Command):

    @property
    def _format(self):
        return "service {} stop"

    def command(self, to_parse):
        return self.format.format(to_parse)


COMMANDS = {
    'start': Start,
    'stop': Stop,
    'update': Update,
    'upgrade': Upgrade,
    'install': Install,
    'uninstall': Uninstall
}
