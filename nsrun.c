#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define __USE_GNU 1
#include <sched.h>

#include <sys/capability.h>
#include <sys/prctl.h>

/*
 * nsrun - Runs the given program in a brand new network namespace with caps to administer the new network at will!
 */

int main(int argc, char ** argv, char ** envp)
{
	if (argc < 2) {
		fprintf(stderr, "usage: %s (target) [args...]\n", argv[0]);
		return 1;
	}

	// Create the new network namespace
	int res = unshare(CLONE_NEWNET);

	if (res == -1) {
		perror("unshare");
		return 1;
	}

	// Raise the inheritable flag for cap_net_admin
	cap_t caps = cap_get_proc();

	const cap_value_t net[1] = { CAP_NET_ADMIN };
	cap_set_flag(caps, CAP_INHERITABLE, 1, net, CAP_SET);
	cap_set_proc(caps);

	// Raise the ambient flag for cap_net_admin, so it passes through exec
	res = prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, CAP_NET_ADMIN, 0, 0);
	
	if (res == -1) {
		perror("prctl");
		return 1;
	}

	// Execute the target program
	res = execve(argv[1], argv + 1, envp);

	if (res == -1) {
		perror("execve");
		return 1;
	}

	// Shouldn't return
	return 0;
}
