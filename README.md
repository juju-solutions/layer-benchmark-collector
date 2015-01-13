# Overview

This subordinate charm allows for the collection of system and application metrics.

# Usage

    juju deploy collectd
    juju deploy mysql
    juju deploy mediawiki
    juju add-relation collectd:juju-info mysql:juju-info
    juju add-relation collectd:juju-info mediawiki:juju-info
    juju set plugins "cpu,memory,disk,dbi,apache"
    juju set extra-config "..."

# Configuration

    juju set plugins "cpu,memory,disk"
    juju set extra-config="<Plugin disk>
        Disk "sda"
        IgnoreSelected false
        </Plugin>
    "

# Contact Information
