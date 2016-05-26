#!/usr/bin/python
""" LIFX Node Server for Polyglot 
      by Einstein.42(James Milne)
      milne.james@gmail.com"""

from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector, Node
from polylifx_types import LIFXControl

VERSION = "0.1.1"

class LIFXNodeServer(SimpleNodeServer):
    """ LIFX Node Server """
    controller = []
    bulbs = []

    def setup(self):
        self.logger = self.poly.logger
        manifest = self.config.get('manifest',{})
        self.controller = LIFXControl(self, 'lifxcontrol', 'LIFX Control', True, manifest)
        self.controller._discover()
        self.update_config()
        
    def poll(self):
        if len(self.bulbs) >= 1:
            for i in self.bulbs:
                i.update_info()

    def long_poll(self):
        pass
        

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
