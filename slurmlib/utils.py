"""Utils class to import settings and other.

Author: Diviyan Kalainathan.
"""
import os
import time
import yaml
import paramiko
import progressbar
from datetime import datetime


class SlurmSSHClient(paramiko.SSHClient):
    """Settings class."""

    def __init__(self):
        """Init and define the settings."""
        super(SlurmSSHClient, self).__init__()
        attributes = yaml.load(
            open(os.environ["HOME"] + "/.ssh/slurm_config.yml", "r"))
        self.dist_dir = attributes["distant_personal_folder"]
        if self.dist_dir[-1] != "/":
            self.dist_dir += "/"
        self.usr = attributes["username"]
        self.sshconfigfile = attributes["ssh_config_file"]
        self.sshkey = attributes["sshkey"]
        self.conda_path = attributes["conda_bin_path"]
        if self.conda_path[-1] != "/":
            self.conda_path += "/"

    def connect(self):
        """Connect to the SLURM master node."""
        config = paramiko.SSHConfig()
        config.parse(open(self.sshconfigfile))
        host = config.lookup("cluster")
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        proxy = paramiko.ProxyCommand(host['proxycommand'])
        super(SlurmSSHClient, self).connect(host['hostname'], 22, username=self.usr,
                                            key_filename=host["identityfile"], sock=proxy)

        return self

    def put_folder(self, source, target):
        """Send folder using scp."""
        for item in os.listdir(source):
            if os.path.isfile(os.path.join(source, item)):
                self.sftp.put(os.path.join(source, item),
                              '%s/%s' % (target, item))
                self.cpt += 1
                self.bar.update(self.cpt)
                time.sleep(0.1)
            else:
                self.mkdir('%s/%s' % (target, item), ignore_existing=True)
                self.put_folder(os.path.join(source, item),
                                '%s/%s' % (target, item))

    def mkdir(self, path, mode=511, ignore_existing=False):
        """Augment mkdir by adding an option to not fail if the folder exists."""
        try:
            self.sftp.mkdir(path, mode)
        except IOError:
            if ignore_existing:
                pass
            else:
                raise FileExistsError

    def send_files(self, folder, destination):
        """Send files using scp."""
        if self.get_transport().is_active():
            print("Sending bundle over ssh...")
            self.sftp = self.open_sftp()
            self.mkdir(destination, ignore_existing=True)
            print("ok")
            nfiles = sum(len(files)
                         for s, d, files in os.walk(os.path.dirname(folder)))
            self.bar = progressbar.ProgressBar(max_value=nfiles)
            self.cpt = 0
            self.put_folder(folder, destination)
            print("")  # cleanup the progressbar

        else:
            raise ConnectionError(
                "The client is not connected. use .connect to do it.")

    def rsync_upload(self, localdir, distantdir):
        """Rsync files from local folder to distant folder."""
        print("Sending bundle to SLURM master node...")
        x = 'rsync -az --info=progress2 -e "ssh -i {} -F {}" {} {}@cluster:{} '.format(self.sshkey,
                                                                                       self.sshconfigfile,
                                                                                       localdir, self.usr,
                                                                                       os.path.dirname(distantdir))
        os.system(x)

    def rsync_download(self, distantdir, localdir):
        """Rsync files from distant folder to local folder."""
        # print(localdir)
        x = 'rsync -az --info=progress2 -e "ssh -i {} -F {}" {}@cluster:{} {} '.format(self.sshkey,
                                                                                       self.sshconfigfile,
                                                                                       self.usr, distantdir,
                                                                                       os.path.dirname(localdir))
        os.system(x)
