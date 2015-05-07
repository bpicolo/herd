from herd import command
from herd.task import TaskRunner


def test_single_command():
    config = {
        'tasks': {
            'git': {'install': 'git'}
        },
    }
    expected = command.Install().command('git')

    assert TaskRunner(config).commands_for_task('git') == [expected]


def test_multiple_commands():
    config = {
        'tasks': {
            'git': {'install': ['git', 'nginx']}
        },
    }
    expected = command.Install().command(['git', 'nginx'])

    assert TaskRunner(config).commands_for_task('git') == [expected]


def test_with_dependencies():
    config = {
        'tasks': {
            'git': {
                'dependencies': ['nginx'],
                'install': ['git'],
            },
            'nginx': {
                'install': ['nginx'],
            },
        },
    }
    commands = TaskRunner(config).commands_for_task('git')

    assert command.Install().command('nginx') in commands
    assert command.Install().command('git') in commands


def test_with_multiple_dependencies():
    config = {
        'tasks': {
            'git': {
                'dependencies': ['nginx', 'nginx_start'],
                'install': ['git'],
            },
            'nginx': {
                'install': ['nginx'],
            },
            'nginx_start': {
                'start': 'nginx',
            },
        },
    }
    commands = TaskRunner(config).commands_for_task('git')

    assert command.Install().command('nginx') in commands
    assert command.Install().command('git') in commands
    assert command.Start().command('nginx') in commands
