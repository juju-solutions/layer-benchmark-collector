# Overview

This subordinate charm allows for the collection of system and application metrics.

# Usage

    juju deploy benchmark-gui
    juju deploy benchmark-collector
    juju add-relation benchmark-gui benchmark-collector

    juju deploy mysql
    juju deploy mediawiki
    juju add-relation mediawiki:db mysql:db

    juju add-relation benchmark-collector:beats-host mysql
    juju add-relation benchmark-collector:beats-host mediawiki
