Acheron
=======

In Ancient Greek mythology, [Acheron is "the river of
pain,"](https://en.wikipedia.org/wiki/Acheron) and supposedly joined with the
Styx in the underworld.

Acheron is a pure-python daemon that configures Strongswan to provide IPSec
support for [Contrail](http://contrail.ow2.org) with help from
[GroupVPN](http://www.grid-appliance.org/wiki/index.php/GroupVPN) (As the
underlying transport) and Contrail's own Styx JSON RPC subproject.

Using Acheron
-------------

Acheron isn't intended to be used on its own, but rather with many other system
components. If you want to try it out right now, you can use our
[Vagrant](http://www.vagrantup.com/) scripts
[on Gitorious](https://gitorious.org/groupvpn-strongswan/vbox-setup-tool).

This will configure two VMs, "Alice" and "Bob", which should be able to
communicate with each other via GroupVPN. All traffic should be encrypted
automatically by Strongswan.

Contrail
--------

From the official wiki:

> Contrail is a complete Cloud platform which integrates a full
> Infrastructure-as-a-Service and Platform-as-a-Service facilities. It allows
> Cloud providers to seamlessly integrate resources from other Clouds with
> their own infrastructure, and breaks the current customer lock-in situation
> by allowing live application migration from one cloud to another.
