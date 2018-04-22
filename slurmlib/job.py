"""Job class for executing jobs on slurm.

Author : Diviyan Kalainathan
"""
import os
import time
import inspect
import progressbar
from datetime import datetime
from shutil import copy2
from .utils import SlurmSSHClient


class Job(object):
    """Job class to directly execute scripts on SLURM."""
    def __init__(self, interactive=True, gpu=0, gputype=None, cpu=None,
                 nodelist=None, time="2:00:00", queue="priority", environment=None,
                 request_node=False, folder_to_send=".", ignore_files20MB=True,
                 destination_folder="new", keep_bundle=True):
        """Init the job class."""
        super(Job, self).__init__()
        self.args = locals()
        self.client = SlurmSSHClient()

    def run(self, f, *args, **kwargs):
        """Execute the job."""
        frame = inspect.stack()[1]
        filename = os.path.abspath(inspect.getmodule(frame[0]).__file__)
        print("File to be executed: {}".format(filename))
        bundle = self.build_bundle(filename, f, *args, **kwargs)
        targetdir = "{}bundle_slurm_{}".format(self.client.dist_dir, self.id)
        self.client.connect()

        try:
            # Send bundle
            if self.args['destination_folder'] != 'new':
                raise NotImplementedError('Rsync like feature not available yet.')
            else:
                self.client.rsync_upload(bundle, targetdir)

            # Change permissions ?
            # Run job:
            if self.args['interactive']:
                print("Running script as interactive...")

                cmd = "cd {}; srun {} {} {} {} -p {} -t {} --no-kill --unbuffered {}; cd ~ ".format(targetdir,
                                                                                                    "" if not self.args["gpu"] else "--gres=gpu:{}".format(self.args['gpu']),
                                                                                                    "" if self.args['gputype'] is None else "-C {}".format(self.args['gputype']),
                                                                                                    "" if self.args['cpu'] is None else "-c {}".format(self.args['cpu']),
                                                                                                    "" if self.args['nodelist'] is None else "-w {}".format(self.args['nodelist']),
                                                                                                    self.args['queue'],
                                                                                                    self.args['time'],
                                                                                                    targetdir + "/execution_script.sh")
                print("Command to be executed: {}".format(cmd))
                stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=True)
                stdin.close()

                for line in iter(stdout.readline, ""):
                    print(line, end="")
                for line in iter(stderr.readline, ""):
                    print(line, end="")

                # # print(stderr.read())

            else:
                print("Running script as batch job...")
                cmd = "cd {}; sbatch {} {} {} {} -p {} -t {} --no-kill {}; cd ~".format(targetdir,
                                                                                        "" if not self.args["gpu"] else "--gres=gpu:{}".format(self.args['gpu']),
                                                                                        "" if self.args['gputype'] is None else "-C {}".format(self.args['gputype']),
                                                                                        "" if self.args['cpu'] is None else "-c {}".format(self.args['cpu']),
                                                                                        "" if self.args['nodelist'] is None else "-w {}".format(self.args['nodelist']),
                                                                                        self.args['queue'],
                                                                                        self.args['time'],
                                                                                        targetdir + "/execution_script.sh")
                stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=True)
        except KeyboardInterrupt:
            stdin, stdout, stderr = self.client.exec_command(b'\x003')
            stdin, stdout, stderr = self.client.exec_command(b'\x003')
            stdin, stdout, stderr = self.client.exec_command(b'\x04')
            stdin, stdout, stderr = self.client.shutdown_write()

            # for line in iter(stdout.readline, ""):
            #         print(line, end="")
            # for line in iter(stderr.readline, ""):
            #         print(line, end="")

        except Exception as e:
            print(e)
            pass

        # Retrieve results.
        if self.args['interactive']:
            print("Retrieving results...")
            self.client.rsync_download(targetdir, bundle)
            if not self.args["keep_bundle"]:
                print("Option not supported yet.")
        self.client.close()

        return stdin, stdout, stderr

    def build_bundle(self, filename, function, *args, **kwargs):
        """Build the bundle that is going to be sent to the master node."""
        self.id = datetime.now().isoformat()[:-10]  # Date index for execution
        print("Job Execution ID : {}".format(self.id))
        if self.args["ignore_files20MB"]:
            path = "{}/bundle_slurm_{}".format(os.path.dirname(filename), self.id)
            os.makedirs(path)
            # fill the bundle
            nfiles = sum([len(files) for s, d, files in os.walk(os.path.dirname(filename)) if "bundle_slurm" not in s])
            bar = progressbar.ProgressBar(max_value=nfiles)
            cpt = 0
            print("Building slurm bundle...")
            for subdir, dirs, files in os.walk(os.path.dirname(filename)):
                if "bundle_slurm" not in subdir:
                    s = subdir.replace(os.path.dirname(filename), path)
                    for d in dirs:
                        if "bundle_slurm" not in d:
                            os.makedirs(s + "/" + d)
                    for f in files:
                        cpt += 1
                        # print(cpt, f)
                        if os.path.getsize(f)/1024**2 < 20:
                            copy2(subdir + "/" + f, s + "/" + f)
                        bar.update(cpt)
                        time.sleep(0.1)

            print("")  # cleanup the progressbar

        else:
            path = os.path.dirname(filename)

        # Execution script
        exec_command = "python -c 'from {} import *; output={}({},{}); print(output)'".format(os.path.splitext(os.path.basename(filename))[0],
                                                                                              function.__name__,
                                                                                              ", ".join([str(i) for i in args]),
                                                                                              ", ".join(["{}={}".format(i, kwargs[i]) for i in kwargs]))
        f = open("{}/execution_script.sh".format(path), 'w+')
        f.write("#!/bin/bash\n")
        if self.args["environment"] is not None:
            f.write('source {}activate {}\n'.format(self.client.conda_path, self.args["environment"]))
        f.write('echo "$@"\n')
        f.write(exec_command)
        f.close()
        os.chmod("{}/execution_script.sh".format(path), 0o777)
        return path
