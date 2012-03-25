from socket import *
from struct import pack, unpack
from time import sleep
from pprint import pprint
import re

USER_REGEX = re.compile('^# +([0-9]+) "([^"]+)" +([^ ]+) +([0-9:]+) +([0-9]+) +([0-9]+) ([^ ]+) (.+)$')
USER_KEYS = ('user_id', 'name', 'steam_id', 'connected', 'ping', 'loss', 'state', 'adr')

class RCONClient:

    def __init__(self, password, host, port=27016):
        self._players = None
        self._status = None
        self._cvars = None
        self._commands = None
        self._maplist = None
        self.server = (host, port)
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect(self.server)
        self.auth(password)

    def auth(self, password):
        self.send_command(password, is_auth=True)

    def read_packet(self):
        data_len = unpack('<L', self.socket.recv(4))[0]
        data = ''
        while len(data) < data_len:
            data += self.socket.recv(data_len-len(data))
        clen = len(data)-10
        keys = ['id','flag','data','null1','null2']
        fmt = '<2L%ssBB' % clen
        parsed = unpack(fmt, data)
        return dict(zip(keys,parsed))

    def send_command(self, command, is_auth=False):
        command += '\x00'

        clen = len(command)
        fmt = '<3L%ssB' % clen
        auth_flag = 3 if is_auth else 2
        packet = pack(fmt, *(clen+9, 0, auth_flag, command, 0))
        self.socket.send(packet)

        packet = self.read_packet()
        if not packet['data']:
            " this was an auth attempt "
            packet = self.read_packet()
            if packet['flag'] != 2:
                raise Exception('Expected flag value of 2, got %s' \
                    % packet['flag'])
            if packet['id'] == 0xffffffff:
                raise Exception('Authentication Failed')
        return packet

    def get_status(self):
        packet = self.send_command('status')
        status = {}
        players = []
        for line in packet['data'].split('\n'):
            if not line.strip():
                continue
            if line[0] == '#':
                m = USER_REGEX.match(line)
                if m:
                    players.append(dict(zip(USER_KEYS, m.groups())))
            else:
                k,v = line.strip().split(':',1)
                status[k.strip()] = v.strip()
        return status, players

    def get_cvars(self):
        packet = self.send_command('cvarlist')
        data = packet['data']
        while True:
            packet = self.read_packet()
            data += packet['data']
            if data.endswith('total convars/concommands\n'):
                break

        cvars = []
        cmds = []
        for line in data.split('\n'):
            if line.find(':') == -1:
                continue
            cvar = [x.strip() for x in line.split(':',3)]
            if cvar[1] == 'cmd':
                cmds.append(cvar)
            else:
                cvars.append(cvar)
        return (cvars, cmds)

    def get_maplist(self):
        packet = self.send_command('maps *')
        maps = []
        data = packet['data']
        for line in data.split('\n'):
            if line.startswith('PENDING:   (fs)'):
                maps.append(line.split(' ')[-1])
        return maps

    @property
    def players(self):
        if self._players is None:
            self._status, self._players = self.get_status()
        return self._players

    @property
    def status(self):
        if self._status is None:
            self._status, self._players = self.get_status()
        return self._status

    @property
    def cvars(self):
        if self._cvars is None:
            self._cvars, self._commands = self.get_cvars()
        return self._cvars

    @property
    def commands(self):
        if self._commands is None:
            self._cvars, self._commands = self.get_cvars()
        return self._commands

    @property
    def maps(self):
        if self._maplist is None:
            self._maplist = self.get_maplist()
        return self._maplist
