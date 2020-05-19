# Lace

A network simulator designed for teaching networks. Uses modern Linux features such as namespaces and caps (so only works on Linux, unfortunately).

## Building and Setup

The program is split into three components: `nsrun`, `vsetup` and `lace`. `nsrun` is a C program which needs to be built, using the provided makefile. However, `libcap-dev` needs to be installed first:

```sh
sudo apt install libcap-dev
make
```

The makefile will also require admin access to grant the necessary caps to `nsrun`, and so will also run sudo.

Python 3, and `xterm` are also required to run `lace`, but these should already be installed on most Linux systems.

## Usage

First you'll need to setup a network config file, a sample config file `config.json` is provided which sets up three hosts.

Each host should at least be given an IP address *with* the block (this is passed directly into `ip addr`), and exactly one host should be marked as the switch host. The switch host will have a bridge interface connecting the veth devices in the other hosts.

Once the config file is created, you can run Lace like so:

```sh
./lace.py (config file)
```

This spawns several `xterm` windows running a `bash` shell in the new network namespace, with the network interfaces setup already. If you used the sample config file, you can try something like `ping 192.168.5.2`, or using `nc` on two of the hosts.

Because of the way the caps are set, each shell has control over its own network namespace, so you can run more network setup commands (e.g. `ip addr` to configure more IP addresses).
