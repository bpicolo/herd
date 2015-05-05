def parallel_connections(config):
    if 'herd' not in config:
        return None

    return config['herd'].get('concurrent_connections')
