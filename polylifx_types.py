from polyglot.nodeserver_api import Node
import lifxlan
from lifxlan.device import WorkflowException
import time
import random
import errno
from socket import error as socket_error

# LIFX Color Capabilities Table per device. True = Color, False = Not
LIFX_BULB_TABLE = {
                                1: True, # LIFX Original 1000
                                3: True, # LIFX Color 650
                                10: False, # LIFX White 800(Low Voltage)
                                11: False, # LIFX White 800(High Voltage)
                                18: False, # LIFX White 900 BR30(Low Voltage)
                                20: True, # LIFX Color 1000 BR30
                                22: True, # LIFX Color 1000
                                27: True, # LIFX A19
                                28: True, # LIFX BR30
                                29: True, # LIFX + A19
                                30: True, # LIFX + BR30
                                31: True # LIFX Z
                                }

DEFAULT_DURATION = 0

# Changing these will not update the ISY names and labels, you will have to edit the profile.
COLORS = {
	0: ['RED', [62978, 65535, 65535, 3500]],
	1: ['ORANGE', [5525, 65535, 65535, 3500]],
	2: ['YELLOW', [7615, 65535, 65535, 3500]],
	3: ['GREEN', [16173, 65535, 65535, 3500]],
	4: ['CYAN', [29814, 65535, 65535, 3500]],
	5: ['BLUE', [43634, 65535, 65535, 3500]],
	6: ['PURPLE', [50486, 65535, 65535, 3500]],
	7: ['PINK', [58275, 65535, 47142, 3500]],
	8: ['WHITE', [58275, 0, 65535, 5500]],
	9: ['COLD_WHTE', [58275, 0, 65535, 9000]],
	10: ['WARM_WHITE', [58275, 0, 65535, 3200]],
	11: ['GOLD', [58275, 0, 65535, 2500]]
}

def myfloat(value, prec=1):
    """ round and return float """
    return round(float(value), prec)

def nanosec_to_hours(ns):
    return ns/(1000000000.0*60*60)

class LIFXControl(Node):

    def __init__(self, *args, **kwargs):
        self.lifx_connector = lifxlan.LifxLAN(None)
        super(LIFXControl, self).__init__(*args, **kwargs)

    def _discover(self, *args, **kwargs):
        manifest = self.parent.config.get('manifest', {})
        devices = self.lifx_connector.get_lights()
        self.logger.info('%i bulbs found. Checking status and adding to ISY', len(devices))
        for d in devices:
            name = 'LIFX ' + str(d.get_label())
            address = d.get_mac_addr().replace(':', '').lower()
            lnode = self.parent.get_node(address)
            if not lnode:
                # Instead of Checking the bulb array and breaking when new bulb types come out,
                # We will assume the bulb is colored unless it is one of the 3 known white only bulbs.
                hasColor = True if d.get_product() not in [10, 11, 18] else False
                if hasColor:
                    self.logger.info('Adding new LIFX Color Bulb: %s(%s)', name, address)
                    self.parent.bulbs.append(LIFXColor(self.parent, self.parent.get_node('lifxcontrol'), address, name, d, hasColor, manifest))
                else:
                    self.logger.info('Adding new LIFX Non-Color Bulb: %s(%s)', name, address)
                    self.parent.bulbs.append(LIFXWhite(self.parent, self.parent.get_node('lifxcontrol'), address, name, d, hasColor, manifest))
            gid, glabel, gupdatedat = d.get_group_tuple()
            #Make a new group
            gaddress = glabel.replace("'", "").replace(' ', '').lower()[:12]
            lnode = self.parent.get_node(gaddress)
            if not lnode:
                self.logger.info('Adding new LIFX Group: %s ', glabel)
                self.parent.groups.append(LIFXGroup(self.parent, self, self.parent.get_node('lifxcontrol'), gaddress, gid, glabel, gupdatedat, manifest))
        return True

    def query(self, **kwargs):
        self.parent.report_drivers()
        return True

    _drivers = {}

    _commands = {'DISCOVER': _discover}

    node_def_id = 'lifxcontrol'

class LIFXColor(Node):

    def __init__(self, parent, primary, address, name, device, hasColor, manifest=None):
        self.parent = parent
        self.address = address
        self.name = name
        self.device = device
        self.label = self.device.get_label()
        self.hasColor = hasColor
        self.connected = True
        self.uptime = 0
        self.power = False
        self.color = []
        self.duration = DEFAULT_DURATION
        super(LIFXColor, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()

    def update_info(self):
        try:
            self.power = True if self.device.get_power() == 65535 else False
            self.color = list(self.device.get_color())
            self.uptime = nanosec_to_hours(self.device.get_uptime())
            for ind, driver in enumerate(('GV1', 'GV2', 'GV3', 'CLITEMP')):
                self.set_driver(driver, self.color[ind])
            self.set_driver('ST', self.power)
            self.connected = True
        except (IOError, TypeError, IOError, socket_error) as e:
            if e.errno == errno.EBADF:
                pass
            elif self.connected:
                self.logger.error('During Query, device %s wasn\'t found. Marking as offline', self.name)
                self.logger.debug('update_info exception: %s', str(e))
                self.connected = False
                self.uptime = 0
        finally:
            self.set_driver('GV5', self.connected)
            self.set_driver('GV6', self.uptime)
            self.set_driver('RR', self.duration)
            return True

    def query(self, **kwargs):
        self.update_info()
        self.report_driver()
        return True

    def _seton(self, **kwargs):
        self.device.set_power(True)
        return True

    def _setoff(self, **kwargs):
        self.device.set_power(False)
        return True

    def _apply(self, **kwargs):
        self.logger.info('Received apply command: %s', str(kwargs))
        return True

    def _setcolor(self, **kwargs):
        if self.connected:
            _color = int(kwargs.get('value'))
            self.device.set_color(COLORS[_color][1], self.duration, True)
            self.logger.info('Received SetColor command from ISY. Changing color to: %s', COLORS[_color][0])
        else: self.logger.info('Received SetColor, however the bulb is in a disconnected state... ignoring')
        return True

    def _setmanual(self, **kwargs):
        if self.connected:
            _cmd = kwargs.get('cmd')
            _val = int(kwargs.get('value'))
            if _cmd == 'SETH': self.color[0] = _val
            if _cmd == 'SETS': self.color[1] = _val
            if _cmd == 'SETB': self.color[2] = _val
            if _cmd == 'SETK': self.color[3] = _val
            if _cmd == 'SETD': self.duration = _val
            self.device.set_color(self.color, self.duration, True)
            self.logger.info('Received manual change, updating the bulb to: %s duration: %i', str(self.color), self.duration)
        else: self.logger.info('Received manual change, however the bulb is in a disconnected state... ignoring')
        return True

    def _sethsbkd(self, **kwargs):
        try:
            color = [int(kwargs.get('H.uom56')), int(kwargs.get('S.uom56')), int(kwargs.get('B.uom56')), int(kwargs.get('K.uom26'))]
            duration = int(kwargs.get('D.uom42'))
            self.logger.info('Received manual change, updating the bulb to: %s duration: %i', str(self.color), duration)
        except TypeError:
            self.duration = 0
        self.device.set_color(color, self.duration, True)
        return True


    _drivers = {'ST': [0, 25, int], 'GV1': [0, 56, int], 'GV2': [0, 56, int],
                            'GV3': [0, 56, int], 'CLITEMP': [0, 26, int],
                            'GV5': [0, 25, int], 'GV6': [0, 20, myfloat],
                            'RR': [0, 42, int]}

    _commands = {'DON': _seton, 'DOF': _setoff, 'QUERY': query,
                            'APPLY': _apply, 'SET_COLOR': _setcolor, 'SETH': _setmanual,
                            'SETS': _setmanual, 'SETB': _setmanual, 'SETK': _setmanual, 'SETD': _setmanual,
                            'SET_HSBKD': _sethsbkd}

    node_def_id = 'lifxcolor'

class LIFXWhite(Node):

    def __init__(self, parent, primary, address, name, device, hasColor, manifest=None):
        self.parent = parent
        self.address = address
        self.name = name
        self.device = device
        self.label = self.device.get_label()
        self.hasColor = hasColor
        self.connected = True
        self.duration = DEFAULT_DURATION
        super(LIFXWhite, self).__init__(parent, address, self.name, primary, manifest)
        self.update_info()

    def update_info(self):
        try:
            self.power = True if self.device.get_power() == 65535 else False
            self.color = list(self.device.get_color())
            self.uptime = nanosec_to_hours(self.device.get_uptime())
            for ind, driver in enumerate(('GV1', 'GV2', 'GV3', 'CLITEMP')):
                self.set_driver(driver, self.color[ind])
            self.set_driver('ST', self.power)
            self.connected = True
        except (IOError, TypeError, WorkflowException, socket_error) as e:
            if e.errno == errno.EBADF:
                time.sleep(2)
                self.update_info()
            if self.connected:
                self.logger.error('During Query, device %s wasn\'t found. Marking as offline', self.name)
                self.logger.debug('update_info exception: %s', str(e))
                self.connected = False
                self.uptime = 0
        finally:
            self.set_driver('GV5', self.connected)
            self.set_driver('GV6', self.uptime)
            self.set_driver('RR', self.duration)
            return True

    def query(self, **kwargs):
        self.update_info()
        self.report_driver()
        return True

    def _seton(self, **kwargs):
        self.device.set_power(True)
        return True

    def _setoff(self, **kwargs):
        self.device.set_power(False)
        return True

    def _apply(self, **kwargs):
        self.logger.info('Received apply command: %s', str(kwargs))
        return True

    def _setcolor(self, **kwargs):
        if self.connected:
            _color = int(kwargs.get('value'))
            self.device.set_color(COLORS[_color][1], duration=self.duration, rapid=False)
            self.logger.info('Received SetColor command from ISY. Changing color to: %s', COLORS[_color][0])
            time.sleep(.2)
            self.update_info()
        else: self.logger.info('Received SetColor, however the bulb is in a disconnected state... ignoring')
        return True

    def _setmanual(self, **kwargs):
        if self.connected:
            _cmd = kwargs.get('cmd')
            _val = int(kwargs.get('value'))
            if _cmd == 'SETH': self.color[0] = _val
            if _cmd == 'SETS': self.color[1] = _val
            if _cmd == 'SETB': self.color[2] = _val
            if _cmd == 'SETK': self.color[3] = _val
            if _cmd == 'SETD': self.duration = _val
            self.device.set_color(self.color, self.duration, rapid=False)
            self.logger.info('Received manual change, updating the bulb to: %s duration: %i', str(self.color), self.duration)
            time.sleep(.2)
            self.update_info()
        else: self.logger.info('Received manual change, however the bulb is in a disconnected state... ignoring')
        return True

    def _sethsbkd(self, **kwargs): return True


    _drivers = {'ST': [0, 25, int], 'GV1': [0, 56, int], 'GV2': [0, 56, int],
                            'GV3': [0, 56, int], 'CLITEMP': [0, 26, int],
                            'GV5': [0, 25, int], 'GV6': [0, 20, myfloat],
                            'RR': [0, 42, int]}

    _commands = {'DON': _seton, 'DOF': _setoff, 'QUERY': query,
                            'APPLY': _apply, 'SET_COLOR': _setcolor, 'SETH': _setmanual,
                            'SETS': _setmanual, 'SETB': _setmanual, 'SETK': _setmanual, 'SETD': _setmanual,
                            'SET_HSBKD': _sethsbkd}

    node_def_id = 'lifxwhite'

class LIFXGroup(Node):

    def __init__(self, parent, control, primary, address, id, label, updated_at, manifest=None):
        self.parent = parent
        self.address = address
        self.control = control
        self.group = id
        self.label = label.replace("'", "")
        self.updated_at = updated_at
        self.members = None
        super(LIFXGroup, self).__init__(parent, address, 'LIFX Group ' + str(self.label), primary, manifest)
        self.update_info()

    def update_info(self):
        self.members = filter(lambda d: d.group == self.group, self.control.lifx_connector.get_lights())
        self.set_driver('ST', len(self.members))
        return True

    def query(self, **kwargs):
        self.update_info()
        self.report_driver()
        return True

    def _seton(self, **kwargs):
        self.logger.info('Received SetOn command for group %s from ISY. Setting all %i members to ON.', self.label, len(self.members))
        for d in self.members:
            d.set_power(True)
        return True

    def _setoff(self, **kwargs):
        self.logger.info('Received SetOff command for group %s from ISY. Setting all %i members to OFF.', self.label, len(self.members))
        for d in self.members:
            d.set_power(False)
        return True

    def _setcolor(self, **kwargs):
        _color = int(kwargs.get('value'))
        for d in self.members:
            d.set_color(COLORS[_color][1], 0, False)
        self.logger.info('Received SetColor command for group %s from ISY. Changing color to: %s for all %i members.', self.label, COLORS[_color][0], len(self.members))
        return True

    def _sethsbkd(self, **kwargs):
        try:
            color = [int(kwargs.get('H.uom56')), int(kwargs.get('S.uom56')), int(kwargs.get('B.uom56')), int(kwargs.get('K.uom26'))]
            duration = int(kwargs.get('D.uom42'))
        except TypeError:
            duration = 0
        for d in self.members:
            d.set_color(color, duration, False)
        self.logger.info('Recieved SetHSBKD command for group %s from ISY, Setting all members to Color %s, duration %i', self.label, color, duration)
        return True


    _drivers = {'ST': [0, 56, int]}

    _commands = {'DON': _seton, 'DOF': _setoff, 'QUERY': query,
                            'SET_COLOR': _setcolor, 'SET_HSBKD': _sethsbkd}

    node_def_id = 'lifxgroup'