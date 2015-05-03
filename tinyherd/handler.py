import paramiko

from tinyherd.command import UbuntuCommand


class NodeHandler:

    def __init__(self, config, cluster_manager):
        self.cluster_manager = cluster_manager
        self.config = config['ssh']
        self._connections = {}
        self.client = paramiko.SSHClient()
        # Not super safe but convenient for now
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect_to_node(self, node_name):
        self._connections[node_name] = paramiko.SSHClient()
        self._connections[node_name].set_missing_host_key_policy(
            paramiko.AutoAddPolicy(),
        )
        self._connections[node_name].connect(
            self.cluster_manager.ip_for_node(node_name),
            key_filename=self.config['path'],
            password=self.config['password'],
            username='root',  # TODO this is clearly suboptimal
        )

    def connection(self, node_name):
        if 'node_name' not in self._connections:
            self.connect_to_node(node_name)

        return self._connections[node_name]

    def print_stdout(self, stdout):
        for line in stdout:
            print(line, end="")

    def execute(self, cluster, command):
        """Execute an arbitrary command on the cluster"""
        for node_name in self.cluster_manager.node_names(cluster):
            print("Executing \"{}\" on {}".format(command, cluster))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(command)

            self.print_stdout(stdout)

    def install(self, cluster, program):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Installing {} on {}".format(program, node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.install(program))

            self.print_stdout(stdout)

    def uninstall(self, cluster, program):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Uninstalling {} on {}".format(program, node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.uninstall(program))

            self.print_stdout(stdout)

    def start(self, cluster, program):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Starting {} on {}".format(program, node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.service_start(program))

            self.print_stdout(stdout)

    def stop(self, cluster, program):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Stopping {} on {}".format(program, node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.service_stop(program))

            self.print_stdout(stdout)

    def update(self, cluster):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Updating {}".format(node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.update())

            self.print_stdout(stdout)

    def upgrade(self, cluster):
        for node_name in self.cluster_manager.node_names(cluster):
            print("Updating {}".format(node_name))
            connection = self.connection(node_name)
            _, stdout, stderr = connection.exec_command(UbuntuCommand.upgrade())

            self.print_stdout(stdout)
