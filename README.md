[![Build Status](https://travis-ci.org/bpicolo/herd.svg?branch=master)](https://travis-ci.org/bpicolo/herd)

# Herd

Herd is an in-progress, easy-to-use framework for management
of small-scale server clusters in pure python.
Tools like puppet, chef, ansible seem to target more large-scale systems, and in my
experience aren't great for getting some small, dead simple machines and apps
going.

In addition, Herd aims to provide a simple framework for creating and handling
your nodes across multiple cloud providers, to help limit and manage your
server costs. :)

While in theory, Herd can do anything SSH can manage, it aims to provide
one good strategy for everything, to eliminate complicated configs.

## Getting started

* pip install herd
* Create a basic config file:
        [ssh]
        path = "/path/to/rsaprivatekey"
        password = 'rsa_key_passphrase'

        [providers.digitalocean]
        token = "MY_PRIVATE_TOKEN"

        [clusters.cluster_name]
        provider = 'digitalocean'
        server_count = 1
        max_monthly_cost = 5
        ssh_keys = ["RSA_KEY_FINGERPRINT"]
        region = 'sfo1'
        image = 'ubuntu-14-04-x64'

* herd syncall --config path/to/config  (default ./config.toml)
* herd info cluster_name
* herd install git
