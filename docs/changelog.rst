Changelog
=====

0.1.5
~~~~~

Resolved an issue where the ISY would reboot however the device fields would remain blank
util changed. These are now refreshed automatically upon the ISY booting up.

0.1.4
~~~~~

Fixed a bug on which the HSBDK and Status/State variables were not able to be viewed from
the 'if' portions of a program. This was a small bug in the editor.

0.1.3
~~~~~

Implemented a "Change HSBKD" for each node type (group and bulb) to allow you to change
all the values at once instead of making a step for each value. See the group documentation
for usage information.

0.1.2
~~~~~

Updated to include Group functionality. Currently only supports, On, Off and Change Color.
Membership is updated every 30 seconds, if you rename a group you will have to delete
it out of ISY and restart the LIFX node server to have it re-discover. ISY does not support
readdressing devices at this time.

0.1.1
~~~~~

Inital release.


