#!/usr/bin/env python
import subprocess
import sys
import logging
import argparse
import time

LOG = logging.getLogger('g09wrapper')
LOG.setLevel(logging.INFO)

class RemoteJob(object):
    commands = {
        'submit': 'qsub -q test -N {job_name}',
        'check_status': "qstat -f {job_id} | awk '/job_state/ {{print $NF}}' ",
    }

    job_script = """#!/bin/bash
PBS -S /bin/bash
PBS -l walltime=00:10:00
PBS -l nodes=1:ppn=16

# module load gaussian

cd $PBS_O_WORKDIR
pwd
{g09_command} {filename}
"""

    config = {
        'remote_host': 'localhost',
        'remote_test_command': 'hostname',
        'remote_wd_setup': 'mkdir -p /tmp/$USER/{job_name}',
        'remote_job_submit': 'qsub -N {job_name}',
        'check_status_period': 1,
        'waiting_states': {'R', 'Q'},
        'complete_states': {'C', 'E'}
    }

    def __init__(self, input_filename):

        if not self.config['remote_host']:
            LOG.error('Please edit the script file to set '
                      'variables such as remote host etc.')
            sys.exit(1)

        self.job_id = None
        self.connection_valid = self.check_connection()
        self.job_status = None
        self.jobfile_contents = self.job_script.format(filename=input_filename,
                                                 g09_command='cat')
        self.job_name = input_filename[:-4] # remove suffix
        LOG.info('')
        with open(self.job_name+'.jobfile', 'w') as f:
            f.write(self.jobfile_contents)


    def connect_and_execute(self, command):
        cmd = ["ssh", self.config['remote_host'], command]
        ssh = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ssh.wait()
        if not ssh.returncode == 0:
            LOG.error("Remote command '%s' exit status = %d", command, ssh.returncode)
            LOG.error("stderr:\n%s", ssh.stderr.read())
            sys.exit(ssh.returncode)
        return ssh


    def running(self):
        return ((self.job_status not in self.config['complete_states']) 
                and (self.connection_valid))


    def check_status(self):
        cmd = self.commands['check_status'].format(job_id=self.job_id)
        ssh = self.connect_and_execute(cmd)
        self.job_status = ssh.stdout.read().strip()
        if not self.job_status:
            self.job_status = 'Unknown'
        time.sleep(self.config['check_status_period'])


    def make_working_directory(self):
        cmd = self.commands['remote_wd_setup'].format(job_name=self.job_name)
        ssh = self.connect_and_execute(cmd)
        result = ssh.stdout.read().strip()
        if not self.job_status:
            self.job_status = 'Unknown'

    def check_connection(self):
        LOG.debug("Testing connection to remote host '%s'", self.config['remote_host'])
        ssh = self.connect_and_execute(self.config['remote_test_command'])
        result = ssh.stdout.readlines()
        if not result:
            error_output = '\n'.join(ssh.stderr.readlines())
            LOG.error('Error connecting to host %s', error_output)
            return False
        result_string = '\n'.join(result).strip()
        LOG.debug("Command '%s' on %s yielded '%s'",
                  self.config['remote_test_command'],
                  self.config['remote_host'],
                  result_string)
        LOG.debug('Connection successful')
        return True


    def submit_job(self):
        LOG.info("Connecting to remote host '%s'", self.config['remote_host'])
        ssh = self.connect_and_execute(self.config['remote_test_command'])
        LOG.info("Done")
        self.job_id = ssh.stdout.read().strip()
        if not self.job_id:
            error_output = '\n'.join(ssh.stderr.readlines())
            LOG.error('Error submitting job (job_id = %s): %s', self.job_id, error_output)



def setup_logging(args):
    handler = logging.FileHandler('test.log')
    formatter = logging.Formatter('[%(name)-4s %(levelname)-3s]: %(msg)s')
    handler.setFormatter(formatter)
    LOG.addHandler(handler)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str,
                        help='Input filename for gaussian job')
    args = parser.parse_args()
    setup_logging(args)
    job = RemoteJob(args.filename)

    while job.running():
        job.check_status()
        LOG.info('Status for job_id=%s: %s', job.job_id, job.job_status)
