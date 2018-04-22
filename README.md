# The python interface for clusters under SLURM: running jobs on a cluster easily.

## Sending code over ssh to the Cluster ; create an interactive job (option for batching).
1. Define a user config.
2. Check if the job is runnable : if yes, run it ; else: ask for queuing.
3. Send back the print out of the script.
4. Clean everything after the job has been successfully terminated, get back all output data over ssh.


Example of what it would be :

```python
import slurmlib
import torch
import pandas


# define a job here:
def Net(torch.nn.Module):
    ...
# define a function to run here.
def train(arg1, arg2, kwarg1=v, kwarg2=v2):
    net = Net()
    for i in ...
    	...
    output.to_csv("results.csv")

if __name__ == '__main__':
   slurmlib.Job('gpu'=1, 'feature'='tesla')
   slurmlib.run(train, arg1, arg2, kwarg1=v, kwarg2=v2)
   # Function has to save results in file for them to be pulled back from slurm.
   output = pandas.read_csv("results.csv")

```


## Installation:

You need to have a setup with the cluster which works first by using ssh !

```sh
git clone https://github.com/Diviyan-Kalainathan/slurmlib.git
cd slurmlib
python setup.py install
cd ~/.ssh  # Configure files default_ssh_config and slurm_config.yml
```
