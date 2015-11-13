#!/usr/bin/python
import os
import sys
import subprocess
import shlex

sys.path.insert(0, os.path.join(os.environ['CHARM_DIR'], 'lib'))

from charmhelpers.core import (
    hookenv,
    host,
    unitdata,
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
COLLECT_PROFILE_DATA = '/usr/local/bin/collect-profile-data'


def install():
    log('Installing collectd')
    install_packages()
    config_changed()
    write_collect_profile_data_script()


def collector_changed():
    """
    Connect connectd to the upstream graphite server
    """
    hostname = hookenv.relation_get('hostname')
    port = hookenv.relation_get('port')
    api_port = hookenv.relation_get('api_port')

    if not hostname:
        return

    config = hookenv.config()
    config['collector-web-host'] = hostname
    config['collector-web-port'] = api_port
    config.save()

    # We need to get the name of the unit in the collectd relation
    if 'JUJU_UNIT_NAME' in os.environ:
        log('Setting up graphite on %s' % os.environ['JUJU_UNIT_NAME'])

        relation_data = hookenv.relations_of_type('benchmark')
        if relation_data:
            relation = relation_data[0]["__unit__"]
            unit_name = "unit-{0}".format(
                relation.replace('/', '-')
            )

            if hostname and port:
                log('Enabling graphite for %s on %s:%s' % (
                    unit_name, hostname, port))
                enable_graphite(hostname, port, unit_name)

                # Trigger profile collection
                write_collect_profile_data_script()
                collect_profile_data()

                start()
    else:
        log('Unable to get JUJU_UNIT_NAME')


def collector_departed():
    if os.path.exists('/etc/collectd/collectd.conf.d/graphite.conf'):
        os.remove('/etc/collectd/collectd.conf.d/graphite.conf')
        start()


def benchmark_changed():
    set_action_id(hookenv.relation_get('action_id'))

    config = hookenv.config()
    config['remote-unit'] = os.environ['JUJU_REMOTE_UNIT']
    config.save()

    # Trigger profile collection
    write_collect_profile_data_script()
    collect_profile_data()


def set_action_id(action_id):
    if unitdata.kv().get('action_id') == action_id:
        # We've already seen this action_id
        return

    unitdata.kv().set('action_id', action_id)

    if not action_id:
        return

    # Broadcast action_id to our peers, then
    # do a profile collection on this unit
    for rid in hookenv.relation_ids('peer'):
        hookenv.relation_set(relation_id=rid, relation_settings={
            'action_id': action_id
        })
    collect_profile_data(action_id=action_id)


def peer_changed():
    """One of our peers is telling us to do a profile data
    collection and tag it with the provided ``action_id``.

    """
    action_id = hookenv.relation_get('action_id')
    if action_id:
        collect_profile_data(action_id=action_id)


def write_collect_profile_data_script():
    """
    (re)generate the script to collect profile data and send it
    to the collector api
    """
    config = hookenv.config()

    if (
        config.get('collector-web-host') is not None and
        config.get('collector-web-port') is not None and
        config.get('remote-unit') is not None
    ):

        template_path = "{0}/templates/collect-profile-data.tmpl".format(
            hookenv.charm_dir())

        host.write_file(
            COLLECT_PROFILE_DATA,
            Template(
                open(template_path).read(),
                keep_trailing_newline=True
            ).render(
                host=config.get('collector-web-host'),
                port=config.get('collector-web-port'),
                unit=config.get('remote-unit')
            )
        )

        os.chmod(COLLECT_PROFILE_DATA, 0755)
    else:
        # Remove the file if the relation is broken
        if os.path.exists(COLLECT_PROFILE_DATA):
            os.remove(COLLECT_PROFILE_DATA)


def collect_profile_data(action_id=None):
    """
    Run the previously-generated collection script
    """
    log('Collecting profile data (action: {})'.format(action_id))

    if os.path.exists(COLLECT_PROFILE_DATA):
        cmd = COLLECT_PROFILE_DATA
        if action_id:
            cmd += ' {}'.format(action_id)
        run_command(cmd)


def run_command(cmd):
    output = None
    try:
        output = subprocess.check_output(shlex.split(cmd))
        log(output)
    except subprocess.CalledProcessError:
        log('Could not execute command: %s' % cmd)
    except IOError:
        log('Could not execute command: %s' % cmd)
    except OSError:
        log('Could not execute command: %s' % cmd)
    return output


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
            Template(
                open(template_path).read(),
                keep_trailing_newline=True
            ).render(plugins=plugins)
        )
    if config.changed('extra-config'):
        host.write_file(
            '/etc/collectd/collectd.conf.d/extra.conf',
            "%s\n" % config['extra-config']
        )

    config.save()
    start()


def upgrade_charm():
    log('Upgrading collectd')
    install_packages()
    config_changed()


def start():
    host.service_restart(SERVICE) or host.service_start(SERVICE)


def stop():
    host.service_stop(SERVICE)


def install_packages():
    apt_update(fatal=True)
    apt_install(packages=['collectd', 'python-setuptools'], fatal=True)


def enable_graphite(hostname, port, unit_name):
    # Enable/configure whisper plugin
    template_path = "{0}/templates/graphite.tmpl".format(
        hookenv.charm_dir())

    host.write_file(
        '/etc/collectd/collectd.conf.d/graphite.conf',
        Template(
            open(template_path).read(),
            keep_trailing_newline=True
        ).render(
            host=hostname,
            port=port,
            unit=unit_name
        )
    )


if __name__ == "__main__":
    # execute a hook based on the name the program is called by
    hooks.execute(sys.argv)
