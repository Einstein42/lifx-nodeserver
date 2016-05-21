# lifx-polyglot
This is the LIFX Node Server for the ISY Polyglot interface.  
(c) Einstein.42 aka James Milne.  
MIT license. 

#Requirements
`sudo pip install lifxlan`

Install:


I built this on ISY version 5.0.2 and the polyglot unstable-release version 0.0.1 from 
https://github.com/UniversalDevicesInc/Polyglot

# Notes
The Nest Polyglot polls the Nest API every 30 seconds due to Nest anti-flooding mechanisms that
temporarily disable queries to the API. So if anything is updated outside of ISY it could take
up to 30 seconds to be reflected in the ISY interface.

Nest only updates the structure api every 600 seconds (5 minutes). This only affects AWAY state
so if your device is set away or returned from away it will take up to 5 minutes to reflect in
your ISY node.
