# Overview

This subordinate charm allows for the collection of system and application metrics.

# Usage

    juju deploy cabs
    juju deploy benchmark-collector
    juju add-relation cabs benchmark-collector

    juju deploy mysql
    juju deploy mediawiki

    juju add-relation mediawiki:db mysql:db
    juju add-relation collectd mysql
    juju add-relation collectd mediawiki


# Configuration

    juju set collectd plugins "cpu,memory,disk"
    juju set collectd extra-config="<Plugin disk>
        Disk "sda"
        IgnoreSelected false
        </Plugin>
    "

# Contact Information
