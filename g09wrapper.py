#!/usr/bin/env python
import subprocess
import sys
import logging
import argparse
import time

LOG = logging.getLogger('g09wrapper')
LOG.setLevel(logging.DEBUG)

class RemoteJob(object):
    commands = {
        'submit': 'qsub -N {job_name} {job_file}',
        'check_status': "qstat -f {job_id} | awk '/job_state/ {{print $NF}}' ",
    }

    job_script = """#!/bin/bash
#PBS -S /bin/bash
#PBS -l walltime=01:00:00
#PBS -l mem=32GB
#PBS -l nodes=1:ppn=16

# module load gaussian

export GAUSS_MDEF=30GB
export GAUSS_CDEF=0-15

cd {remote_wd}
pwd
{g09_command} {filename}
exit $?
"""

    config = {
        'remote_host': '',
        'remote_test_command': 'hostname',
        'remote_wd': '/scratch/$USER/{job_name}',
        'remote_wd_setup': 'mkdir -p {remote_wd}',
        'remote_job_submit': 'cd {remote_wd} && {submit_command}',
        'check_status_period': 30, # seconds between checking in
        'waiting_states': {'R', 'Q'},
        'complete_states': {'C', 'E'}
    }

    job_id = None
    job_name = "Unknown"
    job_status = None
    job_file = None
    job_inputs = []
    job_outputs = []
    working_directory = None

    def __init__(self, input_filename):

        if not self.config['remote_host']:
            LOG.error('Please edit the script file to set '
                      'variables such as remote host etc.')
            sys.exit(1)

        self.connection_valid = self.check_connection()
        self.job_name = input_filename[:-4] # remove suffix
        self.job_file = self.job_name+'.jobfile'
        self.working_directory = self.config['remote_wd'].format(job_name=self.job_name)
        self.job_inputs = [input_filename, self.job_file]
        self.setup_job_outputs()

        self.jobfile_contents = self.job_script.format(
                filename=input_filename,
                g09_command='g09',
                remote_wd=self.working_directory)
        with open(self.job_file, 'w') as f:
            f.write(self.jobfile_contents)
        self.submit_job()

    def setup_job_outputs(self):
        fmt_string = '{remote_host}:{remote_wd}/{{f}}'.format(
                remote_host=self.config['remote_host'],
                remote_wd=self.working_directory)
        self.job_outputs = [fmt_string.format(f=f) for f in (self.job_name+'.log', 'Test.FChk')]

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
        cmd = self.config['remote_wd_setup'].format(remote_wd=self.working_directory)
        ssh = self.connect_and_execute(cmd)

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


    def upload_files(self):
        cmd = ["scp"] + self.job_inputs + \
                [self.config['remote_host'] + ':' + self.working_directory]

        scp = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scp.wait()
        if not scp.returncode == 0:
            LOG.error("Copying files '%s' to remote host exit status = %d",
                      self.job_inputs,
                      scp.returncode)
            LOG.error("stderr:\n%s", ssh.stderr.read())
            sys.exit(ssh.returncode)

    def download_files(self):
        LOG.info('Downloading g09 log file')
        cmd = ["scp", self.job_outputs[0], './remote.log']
        scp = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scp.wait()
        if not scp.returncode == 0:
            LOG.error("Copying files '%s' from remote host exit status = %d",
                      self.job_outputs,
                      scp.returncode)
            LOG.error("stderr:\n%s", scp.stderr.read())
            sys.exit(scp.returncode)

        with open('remote.log') as f:
            contents = f.read()

        LOG.info('Log contents:\n%s', contents)

        LOG.info('Downloading Test.FChk')
        cmd = ["scp", self.job_outputs[1],  './']
        scp = subprocess.Popen(cmd, shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        scp.wait()
        if not scp.returncode == 0:
            LOG.error("Copying files '%s' from remote host exit status = %d",
                      self.job_outputs,
                      scp.returncode)
            LOG.error("stderr:\n%s", scp.stderr.read())
            sys.exit(scp.returncode)


    def submit_job(self):

        self.make_working_directory()
        self.upload_files()

        LOG.info('Submitting remote job from %s', self.job_file)
        submit_command = self.commands['submit'].format(job_name=self.job_name,
                                                        job_file=self.job_file)
        LOG.info('Submit command = `%s`', submit_command)
        job_submit = self.config['remote_job_submit'].format(remote_wd=self.working_directory,
                                                             submit_command=submit_command)
        ssh = self.connect_and_execute(job_submit)
        self.job_id = ssh.stdout.read().strip()
        LOG.info('Submitted job ID: %s', self.job_id)
        if not self.job_id:
            error_output = '\n'.join(ssh.stderr.readlines())
            LOG.error('Error submitting job (job_id = %s): %s', self.job_id, error_output)
            sys.exit(1)



def setup_logging(args):
    handler = logging.FileHandler(args.filename[:-4]+'.log')
    formatter = logging.Formatter('[%(name)-4s %(levelname)-3s %(asctime)s]: %(message)s')
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
    job.download_files()
    LOG.infor('Gaussian job %s complete', args.filename)
    sys.exit(0)
