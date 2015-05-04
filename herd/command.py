

class UbuntuCommand(object):

    @staticmethod
    def update():
        return 'apt-get update -y'

    @staticmethod
    def upgrade():
        return 'apt-get upgrade -y'

    @staticmethod
    def install(program_name):
        return 'sudo apt-get install -y {}'.format(program_name)

    @staticmethod
    def uninstall(program_name):
        return 'sudo apt-get remove -y {}'.format(program_name)

    @staticmethod
    def service_start(service_name):
        return 'service {} start'.format(service_name)

    @staticmethod
    def service_stop(service_stop):
        return 'service {} start'.format(service_stop)
