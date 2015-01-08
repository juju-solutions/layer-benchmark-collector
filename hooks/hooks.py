#!/usr/bin/python

import os
import sys

sys.path.insert(0, os.path.join(os.environ['CHARM_DIR'], 'lib'))

from charmhelpers.core import (
    hookenv,
    host,
)

from charmhelpers.fetch import (
    apt_update,
    apt_install,
)

try:
    from jinja2 import Template
except ImportError:
    apt_update(fatal=True)
    apt_install(['python-jinja2'], fatal=True)
    from jinja2 import Template


hooks = hookenv.Hooks()
log = hookenv.log

SERVICE = 'collectd'


@hooks.hook('install')
def install():
    log('Installing collectd')
    install_packages()


@hooks.hook('config-changed')
def config_changed():
    config = hookenv.config()

    for key in config:
        if config.changed(key):
            log("config['{}'] changed from {} to {}".format(
                key, config.previous(key), config[key]))

    config.save()
    start()


@hooks.hook('upgrade-charm')
def upgrade_charm():
    log('Upgrading collectd')


@hooks.hook('start')
def start():
    host.service_restart(SERVICE) or host.service_start(SERVICE)


@hooks.hook('stop')
def stop():
    host.service_stop(SERVICE)


def install_packages():
    apt_update(fatal=True)
    apt_install(packages=['collectd'], fatal=True)


if __name__ == "__main__":
    # execute a hook based on the name the program is called by
    hooks.execute(sys.argv)
