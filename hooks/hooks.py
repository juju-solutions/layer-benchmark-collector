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


@hooks.hook('collector-relation-joined', 'collector-relation-changed')
def collector_changed():
    hostname = hookenv.relation_get('hostname')
    port = hookenv.relation_get('port')

    if 'JUJU_UNIT_NAME' in os.environ:
        log('Setting up graphite')
        unit_name = "unit-{0}".format(
            os.environ['JUJU_UNIT_NAME'].replace('/', '-')
        )

        if hostname and port:
            enable_graphite(hostname, port, unit_name)
            start()
    else:
        log('Unable to get JUJU_UNIT_NAME ')

    # hostname = hookenv.relation_get('host')
    # port = hookenv.relation_get('port')
    # plugin = hookenv.relation_get('plugin')
    # config = hookenv.relation_get('config')
    #
    # if hostname and port and plugin and config:
    #     template_path = "{0}/templates/plugin.tmpl".format(
    #         hookenv.charm_dir())
    #
    #     host.write_file(
    #         '/etc/collectd/collectd.conf.d/{0}.conf'.format(plugin),
    #         Template(open(template_path).read()).render(
    #             plugin=plugin, config=config, host=host, port=port)
    #     )
    #


@hooks.hook('collector-relation-departed')
def collector_departed():
    if os.path.exists('/etc/collectd/collectd.conf.d/graphite.conf'):
        os.remove('/etc/collectd/collectd.conf.d/graphite.conf')
        start()
    # plugin = hookenv.relation_get('plugin')
    # os.remove('/etc/collectd/collectd.conf.d/{0}.conf'.format(plugin))


@hooks.hook('collectd-joined', 'collectd-changed')
def collectd_changed():
    pass


@hooks.hook('collectd-departed')
def collectd_departed():
    # os.remove('/etc/collectd/collectd.conf.d/graphite.conf')
    # start()
    pass


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


def enable_graphite(hostname, port, unit_name):
    # Enable/configure whisper plugin
    template_path = "{0}/templates/graphite.tmpl".format(
        hookenv.charm_dir())

    host.write_file(
        '/etc/collectd/collectd.conf.d/graphite.conf',
        Template(open(template_path).read(), keep_trailing_newline=True).render(
            host=hostname,
            port=port,
            unit=unit_name
        )
    )


if __name__ == "__main__":
    # execute a hook based on the name the program is called by
    hooks.execute(sys.argv)
