#!/usr/bin/python
""" LIFX Node Server for Polyglot 
      by Einstein.42(James Milne)
      milne.james@gmail.com"""

from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector
import lifxlan

VERSION = "0.1.1"

# LIFX Color Capabilities Table per device. True = Color, False = Not
LIFX_BULB_TABLE = {
                                1: True, # LIFX Original 1000
                                3: True, # LIFX Color 650
                                10: False, # LIFX White 800(Low Voltage)
                                11: False, # LIFX White 800(High Voltage)
                                18: False, # LIFX White 900 BR30(Low Voltage)
                                20: True, # LIFX Color 1000 BR30
                                22: True, # LIFX Color 1000
                                }


def nanosec_to_hours(ns):
    return ns/(1000000000.0*60*60)
    
class LIFXNodeServer(SimpleNodeServer):
    """ LIFX Node Server """
    lifx_connector = lifxlan.LifxLAN(None)
    bulbs = []

    def setup(self):
        self.logger = self.poly.logger
        manifest = self.config.get('manifest',{})
        self._discover()
        self.update_config()
        
    def poll(self):
        pass

    def long_poll(self):
        pass
        
    def _discover():
        devices = lifx_connector.get_lights()
        self.logger.info('%i bulbs found. Checking status and adding to ISY', len(devices))
        for d in devices:
            name = 'LIFX ' + str(d.get_label())
            address = d.get_mac_addr().replace(':', '').lower()
            lnode = self.get_node(address)
            if not lnode:
                hasColor = LIFX_BULB_TABLE[d.get_product()]
                if hasColor:
                    self.logger.info('Adding new LIFX Color Bulb: %s(%s)', name, address)
                    self.bulbs.append(LiFXBulb(self, address, name, d, hasColor, manifest)
                else:
                    self.logger.info('Adding new LIFX Non-Color Bulb: %s(%s)', name, address)
                    self.bulbs.append(LiFXBulb(self, address, name, d, hasColor, manifest)


class LiFXBulb(Node):
    
    def __init__(self, parent, address, name, device, hasColor, manifest=None):
        self.parent = parent
        self.logger = self.parent.poly.logger
        self.address = address
        self.name = name
        self.device = device
        self.hasColor = hasColor
        super(LiFXBulb, self).__init__(parent, address, name, primary=True, manifest)
        self.update_info()
        
    def update_info(self):
        self.power = True if self.device.get_power() == 65535 else False
        self.color = self.device.get_color()
        self.uptime = nanosec_to_hours(self.device.get_uptime())
        self.label = self.device.get_label()

    def query(self, **kwargs):
        self.update_info()
        return True

    if hasColor:
        _drivers = {'GV1': [0, 56, int], 'GV2': [0, 56, int],
                                'GV3': [0, 56, int], 'GV4': [0, 56, int]}

        _commands = {'DON': _on,
                                'DOF': _off,
                                'COLOR': _volume}
        node_def_id = 'lifxcolor'
    else:
        _drivers = {'GV1': [0, 56, int], 'GV2': [0, 56, int],
                                'GV3': [0, 56, int], 'GV4': [0, 56, int]}

        _commands = {'DON': _on,
                                'DOF': _off}
        node_def_id = 'lifxwhite'
                
def main():
    # Setup connection, node server, and nodes
    poly = PolyglotConnector()
    # Override shortpoll and longpoll timers to 5/30, once per second in unnessesary 
    nserver = LIFXNodeServer(poly, 5, 30)
    poly.connect()
    poly.wait_for_config()
    poly.logger.info("LIFX Node Server Interface version " + VERSION + " created. Initiating setup.")
    nserver.setup()
    poly.logger.info("Setup completed. Running Server.")
    nserver.run()
    
if __name__ == "__main__":
    main()
