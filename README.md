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

## tonto_hpc.py

1. Download this script, modify your CrystalExplorer settings (under the 'Expert' tab) to point the 'tonto executable' at this script.
It should just normally run like tonto with the exception of interaction energy calculations.
2. Calculate the B3LYP 6-31G(d,p) wavefunction, and **save the cxp here**. *Do NOT save after calculating placeholder interaction energies or you'll have to recalculate the wavefunction, as CrystalExplorer will think it already has the energies, which will all be zero*.
3. Run the interaction energies calculation out to the desired radius etc. You'll get zero for the energies, but the script will populate a directory (in the same location as the CIF/CXP file) called 'tonto_hpc_files'. 
4. For each of the subdirectories in here, run a tonto job wherever (on HPC etc.) They should all be single core jobs, give them as long as you need since there's no restart capability.
5. Once all of those are calculated, place their output files 'stdout' in the corresponding subdirectories on your local machine, and calculate a interaction energies as you would normally. It should just copy the corresponding stdouts and the energies should appear.
