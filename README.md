# CrystalExplorer Scripts

A useful collection of scripts to help crystalexplorer usage.

## g09wrapper.py

If you edit this script appropriately for your own cluster i.e. `remote_host`,
modification of g09 memory and thread usage, changes for slurm rather than torque.
You should be able to set this as your gaussian executable in crystalexplorer and
have the jobs run remotely on a cluster.

This assumes you have setup passwordless login (i.e. `ssh-copy-id` etc.) on the
remote host.

Further, since this script checks the job status every so often (30s by default),
it is a good idea to setup `ServerAliveInterval 300` or something similar so
that you do not startup a new ssh connection for each command.

Also be aware this script is a work in progress, and was hastily put together so
use at your own risk.
