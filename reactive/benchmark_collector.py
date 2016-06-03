import os
import sys
import subprocess
import shlex

from charms.reactive import hook

from charmhelpers.core import (
    hookenv,
    host,
)

from charmhelpers.fetch import (
    apt_update,
    apt_install,
)

from charmhelpers.core.templating import render


hooks = hookenv.Hooks()
log = hookenv.log

COLLECT_PROFILE_DATA = '/usr/local/bin/collect-profile-data'


@hook("install")
def install():
    log('Installing collector')
    install_packages()
    config_changed()
    write_collect_profile_data_script()


@hook("collector-relation-changed")
def collector_changed(collector):
    hostname = hookenv.relation_get('hostname')
    port = hookenv.relation_get('port')
    api_port = hookenv.relation_get('api_port')
    action_id = hookenv.relation_get('action_id')

    if not hostname:
        return

    config = hookenv.config()
    config['collector-web-host'] = hostname
    config['collector-web-port'] = api_port
    config.save()

    if 'JUJU_UNIT_NAME' not in os.environ:
        log('Unable to get JUJU_UNIT_NAME')
        return

    relation_data = hookenv.relations_of_type('benchmark')
    if relation_data and hostname and port:
        write_collect_profile_data_script()
        collect_profile_data(action_id=action_id)


@hook("benchmark-relation-changed")
def benchmark_changed(benchmark):
    config = hookenv.config()
    config['remote-unit'] = os.environ['JUJU_REMOTE_UNIT']
    config.save()
    write_collect_profile_data_script()
    collect_profile_data()


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
        render(
            source="collect-profile-data.tmpl",
            target=COLLECT_PROFILE_DATA,
            perms=0o755,
            context={
                "host": config.get("collector-web-host"),
                "port": config.get("collector-web-port"),
                "unit": config.get("remote-unit")
            }
        )
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


@hook("config-changed")
def config_changed():
    config = hookenv.config()
    for key in config:
        if config.changed(key):
            log("config['{}'] changed from {} to {}".format(
                key, config.previous(key), config[key]))
    config.save()


@hook("upgrade-charm")
def upgrade_charm():
    log('Upgrading benchmark-collector')
    install_packages()
    config_changed()


def install_packages():
    apt_update(fatal=True)
    apt_install(packages=['python-setuptools'], fatal=True)
