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
    config_changed()


@hooks.hook('cabs-metrics-joined', 'cabs-metrics-changed')
def cabs_metrics_changed():
    hostname = hookenv.relation_get('host')
    port = hookenv.relation_get('port')
    plugin = hookenv.relation_get('plugin')
    config = hookenv.relation_get('config')

    if hostname and port and plugin and config:
        template_path = "{0}/templates/plugin.tmpl".format(
            hookenv.charm_dir())

        host.write_file(
            '/etc/collectd/collectd.conf.d/{0}.conf'.format(plugin),
            Template(open(template_path).read()).render(
                plugin=plugin, config=config, host=host, port=port)
        )


@hooks.hook('cabs-metrics-departed')
def cabs_metrics_departed():
    plugin = hookenv.relation_get('plugin')
    os.remove('/etc/collectd/collectd.conf.d/{0}.conf'.format(plugin))


@hooks.hook('collectd-joined', 'collectd-changed')
def collectd_changed():
    hostname = hookenv.relation_get('host')
    port = hookenv.relation_get('port')
    if hostname and port:
        enable_graphite(hostname, port)
        start()


@hooks.hook('collectd-departed')
def collectd_departed():
    os.remove('/etc/collectd/collectd.conf.d/graphite.conf')
    start()


@hooks.hook('config-changed')
def config_changed():
    config = hookenv.config()

    for key in config:
        if config.changed(key):
            log("config['{}'] changed from {} to {}".format(
                key, config.previous(key), config[key]))

    # Write active plugins
    if config.changed('plugins'):
        plugins = []
        for plugin in config['plugins'].split(','):
            if len(plugin.strip()):
                plugins.append(plugin)
        template_path = "{0}/templates/plugins.tmpl".format(
            hookenv.charm_dir())

        host.write_file(
            '/etc/collectd/collectd.conf.d/plugins.conf',
            Template(open(template_path).read()).render(plugins=plugins)
        )
    if config.changed('extra-config'):
        host.write_file(
            '/etc/collectd/collectd.conf.d/extra.conf',
            config['extra-config']
        )

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


def enable_graphite(host, port):
    # Enable/configure whisper plugin
    template_path = "{0}/templates/plugin-graphite.tmp".format(
        hookenv.charm_dir())

    host.write_file(
        '/etc/collectd/collectd.conf.d/graphite.conf',
        Template(open(template_path).read()).render(host=host, port=port)
    )


if __name__ == "__main__":
    # execute a hook based on the name the program is called by
    hooks.execute(sys.argv)
