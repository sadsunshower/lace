#!/usr/bin/env python3

# lace.py
# Co-ordinates running nsrun and piprun in separate terminals, setting up hosts

import json, os, subprocess, sys

# xterm command, run through nsrun
XTERM = ['./nsrun', '/usr/bin/xterm', '-b', '5', '-fa', '"Monospace"', '-fs', '10', '-e', './piperun.sh']

# Represents a single host
class Host():
    def __init__(self, host_id):
        self._id = host_id
        self._interfaces = []
        self._fifo = None
        self._pid = None
    
    @property
    def pid(self):
        return self._pid

    def add_interface(self, lan, ip = None):
        self._interfaces.append({
            'lan' : lan,
            'ip' : ip
        })
    
    def start_host(self):
        os.mkfifo(os.getenv('HOME') + '/.tmp/lace/' + self._id)
        self._pid = subprocess.Popen(XTERM + [os.getenv('HOME') + '/.tmp/lace/' + self._id]).pid
        self._fifo = open(os.getenv('HOME') + '/.tmp/lace/' + self._id, 'w')
    
    def send_command(self, command):
        self._fifo.write(command + '\n')
    
    def finish_host(self):
        self.send_command(f'echo "This is {self._id}"')
        self._fifo.close()
        os.unlink(os.getenv('HOME') + '/.tmp/lace/' + self._id)
    
    def initialise_interfaces(self):
        for i in range(len(self._interfaces)):
            self.send_command(f'ip link add veth-{self._id}-{i} type veth peer name veth-{self._id}-{i}-b')
            self.send_command(f'ip link set veth-{self._id}-{i} up')

            if self._interfaces[i]['ip'] is not None:
                self.send_command(f'ip addr add {self._interfaces[i]["ip"]} dev veth-{self._id}-{i}')
    
    def move_bridge_interfaces(self, lan, ns):
        for i in range(len(self._interfaces)):
            if self._interfaces[i]['lan'] == lan:
                self.send_command(f'ip link set veth-{self._id}-{i}-b netns {ns}')
                lan.switch.send_command(f'ip link set veth-{self._id}-{i}-b up')
                lan.switch.send_command(f'ip link set veth-{self._id}-{i}-b master {lan.bridge}')

    def set_gateway(self, lan, gateway):
        for i in range(len(self._interfaces)):
            if self._interfaces[i]['lan'] == lan:
                self.send_command(f'ip route add default via {gateway} dev veth-{self._id}-{i}')

    def __repr__(self):
        text = f'Host {self._id}, with {len(self._interfaces)} interfaces:'
        for interface in self._interfaces:
            text += f'\n  Interface in {interface["lan"]}, IP {interface["ip"]}'
        return text

# Represents a LAN
class LAN():
    def __init__(self, net_id):
        self._id = net_id
        self._switch = None
        self._gateway = None
    
    @property
    def switch(self):
        return self._switch
    
    @switch.setter
    def switch(self, switch):
        self._switch = switch
    
    @property
    def gateway(self):
        return self._gateway
    
    @gateway.setter
    def gateway(self, gateway):
        self._gateway = gateway
    
    @property
    def bridge(self):
        return f'bridge-{self._id}'
    
    def __repr__(self):
        return f'LAN {self._id}'

if len(sys.argv) < 2:
    print(f'usage: {sys.argv[0]} (network config)')

# Load and parse configuration
config = {}

with open(sys.argv[1], 'r') as f:
    config = json.loads(f.read())

lans = {}
hosts = {}

# Load all the LANs from the config file
for lan in config['lans']:
    lans[lan] = LAN(lan)
    if 'gateway' in config['lans']:
        lans[lan].gateway = config['lans']['gateway']

# Load all the hosts and all the interfaces
for host in config['hosts']:
    hosts[host] = Host(host)
    for interface in config['hosts'][host]['interfaces']:
        if interface['lan'] not in lans:
            print(f'{sys.argv[0]}: host {host} has an interface in an unknown LAN {interface["lan"]}')
            sys.exit(1)
        if 'ip' in interface:
            hosts[host].add_interface(lans[interface['lan']], interface['ip'])
        else:
            hosts[host].add_interface(lans[interface['lan']], None)

# Assign all the LANs a switch host
for lan in config['lans']:
    if config['lans'][lan]['switch'] not in hosts:
        print(f'{sys.argv[0]}: LAN {lan} has an unknown switch host {config["lans"][lan]["switch"]}')
        sys.exit(1)
    lans[lan].switch = hosts[config['lans'][lan]['switch']]

# Start all hosts
for host in hosts:
    hosts[host].start_host()
    hosts[host].initialise_interfaces()

# Initialise the LANs
for lan in lans:
    # Create the bridge interface
    lans[lan].switch.send_command(f'ip link add {lans[lan].bridge} type bridge')
    lans[lan].switch.send_command(f'ip link set {lans[lan].bridge} up')

    # Move all the bridge interfaces to the switch
    ns = f'/proc/{lans[lan].switch.pid}/ns/net'
    for host in hosts:
        hosts[host].move_bridge_interfaces(lans[lan], ns)
    
    # If a default gateway was set, initialise it
    if lans[lan].gateway is not None:
        for host in hosts:
            hosts[host].set_gateway(lans[lan], lans[lan].gateway)

# Close the FIFOs, which will start an interactive shell
for host in hosts:
    hosts[host].finish_host()