#!/bin/bash

# Print usage
if [[ $# -ne 5 ]]; then
	echo "usage: $0 (my index) (switch index) (num of clients) (switch net ns) (my ip address)"
	exit 1
fi

# Create veth to bridge
ip link add "veth$1" type veth peer name "veth$1b"
ip link set "veth$1" up

# Set IP address
ip addr add "$5" dev "veth$1"
echo "This host is $(hostname -I)"

if [[ "$1" -eq "$2" ]]; then
	# If this is the switch, wait for the other hosts
	finished=0
	while [[ $finished -eq 0 ]]; do
		if flock ~/.tmp/lace/waithosts egrep -q . ~/.tmp/lace/waithosts; then
			sleep 1
		else
			finished=1
		fi
	done

	rm ~/.tmp/lace/waithosts

	# Create the bridge
	ip link add bridge type bridge
	ip link set bridge up
	
	# Connect all b interfaces to the bridge
	clients=$(( $3 - 1 ))
	for client in $(seq 0 "$clients"); do
		ip link set "veth${client}b" up
		ip link set "veth${client}b" master bridge
	done
else
	# If this is not the switch, move the b interface
	ip link set "veth$1b" netns "$4"

	# Remove this host
	flock ~/.tmp/lace/waithosts sed -i -re "s/^$1$//g" ~/.tmp/lace/waithosts
fi

# Run a sub-shell for running any programs
bash -i
