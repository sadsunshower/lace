#!/usr/bin/env python3

# lace.py
# Co-ordinates running nsrun and vsetup in separate terminals

import json, os, subprocess, sys

if len(sys.argv) < 2:
    print(f'usage: {sys.argv[0]} (network config)')

# Load configuration
config = {}

with open(sys.argv[1], 'r') as f:
    config = json.loads(f.read())

# xterm command, run through nsrun
xterm = ['./nsrun', '/usr/bin/xterm', '-b', '5', '-fa', '"Monospace"', '-fs', '14', '-e', './vsetup.sh']

# Find the host designated to be the switch host
switch = -1
for host in range(len(config['hosts'])):
    if 'switch' in config['hosts'][host]:
        if master != -1:
            print(f'error: {config["hosts"][host]["ip"]} marked as switch host when {config["hosts"][master]["ip"]} is already switch host')
            sys.exit(1)

        switch = host

if switch == -1:
    print(f'error: no master host set')
    sys.exit(1)

# Create a temporary file containing all the non-switch hosts which have yet to be setup
os.makedirs(os.getenv('HOME') + '/.tmp/lace', exist_ok=True)

with open(os.getenv('HOME') + '/.tmp/lace/waithosts', 'w') as f:
    for host in range(len(config['hosts'])):
        if host == switch:
            continue

        f.write(f'{host}\n')

# Start the switch host first, record its PID
switchpid = subprocess.Popen(xterm + [str(switch), str(switch), str(len(config['hosts'])), '/dev/null', config['hosts'][switch]['ip']]).pid

# Start the other hosts
for host in range(len(config['hosts'])):
    if host == switch:
        continue

    subprocess.Popen(xterm + ['-e', './vsetup.sh', str(host), str(switch), str(len(config['hosts'])), f'/proc/{switchpid}/ns/net', config['hosts'][host]['ip']])
