nsrun: nsrun.c
	clang -o nsrun nsrun.c -lcap
	@echo "We need admin access to set the caps on the nsrun command"
	sudo setcap 'cap_sys_admin=ep cap_net_admin=iep' nsrun
