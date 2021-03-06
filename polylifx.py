#!/usr/bin/python
""" LIFX Node Server for Polyglot
      by Einstein.42(James Milne)
      milne.james@gmail.com"""

from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector, Node
from polylifx_types import LIFXControl
# Test for PyYaml config file.
#import yaml

VERSION = "0.1.6"

class LIFXNodeServer(SimpleNodeServer):
    """ LIFX Node Server """
    controller = []
    bulbs = []
    groups = []

    def setup(self):
        self.logger = self.poly.logger
        self.logger.info('Config File param: %s', self.poly.configfile)
        manifest = self.config.get('manifest', {})
        self.controller = LIFXControl(self, 'lifxcontrol', 'LIFX Control', True, manifest)
        self.controller.discover()
        self.update_config()

    def poll(self):
        if len(self.bulbs) >= 1:
            for i in self.bulbs:
                i.update_info()

    def long_poll(self):
        if len(self.groups) >= 1:
            for g in self.groups:
                g.update_info()

    def report_drivers(self):
        if len(self.bulbs) >= 1:
            for i in self.bulbs:
                i.report_driver()
        if len(self.groups) >= 1:
            for grp in self.groups:
                grp.report_driver()

def main():
    # Setup connection, node server, and nodes
    poly = PolyglotConnector()
    # Override shortpoll and longpoll timers to 5/30, once per second is unnessesary
    nserver = LIFXNodeServer(poly, 5, 30)
    poly.connect()
    poly.wait_for_config()
    poly.logger.info("LIFX Node Server Interface version " + VERSION + " created. Initiating setup.")
    nserver.setup()
    poly.logger.info("Setup completed. Running Server.")
    nserver.run()

if __name__ == "__main__":
    main()
