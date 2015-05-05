
class UbuntuCommand(object):

    @staticmethod
    def command(command, sudo=False):
        return '{}{}'.format('sudo ' if sudo else '', command)

    @staticmethod
    def update(sudo=False):
        return UbuntuCommand.command('apt-get update -y', sudo)

    @staticmethod
    def upgrade(sudo=False):
        return UbuntuCommand.command('apt-get upgrade -y', sudo)

    @staticmethod
    def install(program_name, sudo=False):
        return UbuntuCommand.command(
            'sudo apt-get install -y {}'.format(program_name),
            sudo,
        )

    @staticmethod
    def uninstall(program_name, sudo=False):
        return UbuntuCommand.command(
            'sudo apt-get remove -y {}'.format(program_name),
            sudo
        )

    @staticmethod
    def service_start(service_name, sudo=False):
        return UbuntuCommand.command(
            'service {} start'.format(service_name),
            sudo
        )

    @staticmethod
    def service_stop(service_stop, sudo=False):
        return UbuntuCommand.command(
            'service {} start'.format(service_stop),
            sudo
        )
