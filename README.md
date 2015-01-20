# Overview

This subordinate charm allows for the collection of system and application metrics.

# Usage

    juju deploy collectd
    juju deploy mysql
    juju deploy mediawiki

    juju set collectd collector-web-host=10.0.3.1

    juju add-relation collectd:juju-info mysql:juju-info
    juju add-relation collectd:juju-info mediawiki:juju-info
    juju set collectd plugins "cpu,memory,disk,dbi,apache"
    juju set collectd extra-config "..."

# Configuration

    juju set collectd plugins "cpu,memory,disk"
    juju set collectd extra-config="<Plugin disk>
        Disk "sda"
        IgnoreSelected false
        </Plugin>
    "

# Contact Information
