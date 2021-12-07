# Artifact for "PMEvo: Portable Inference of Port Mappings for Out-of-Order Processors by Evolutionary Optimization"

Also see the [project website](https://compilers.cs.uni-saarland.de/projects/portmap/) and the [paper](https://compilers.cs.uni-saarland.de/papers/ritter_pmevo_pldi20.pdf).

A full pre-built version of this VM is available [here](https://kingsx.cs.uni-saarland.de/owncloud/index.php/s/xXrXJdj7pSngfbS) for download.
A smaller VM without pre-built Ithemal container is available [here](https://kingsx.cs.uni-saarland.de/owncloud/index.php/s/24cbEzjmGgKPm6n).

This artifact was created to be used as a Vagrant Virtual Machine.
Usage without the VM is possible, but might require you to apply some steps from `vm_setup/bootstrap.sh` and `vm_setup/post_install.sh`.
In particular, you need to set the `PMEVO_BASE` environment variable to the absolute path of the `vm_setup/pmevo` directory.

## Setting up the VM

The artifact is provided as a Vagrant Virtual Machine using the Virtual Box
provider. To run it, you will need to install Vagrant as described here:

    https://www.vagrantup.com/intro/getting-started/install.html

and also Virtual Box as available here:

    https://www.virtualbox.org/

Depending on your hardware platform, it might be necessary to enable
virtualization options in your system's BIOS to use virtual box.

Use the following command to build the VM:
```
cd vm_setup
vagrant up
```

Once this is done, ssh to the VM and run the post-install script:
```
vagrant ssh
./post_install.sh
```

Next, leave the VM and package it up:
```
exit
vagrant package --output ../pmevo-artifact.box
```

Take the resulting box and put it into an archive together with the shipping
vagrant file:
```
cd ..
tar -czvf pmevo-artifact.tgz Vagrantfile pmevo-artifact.box
```

Done!


# Using PMEvo without the VM, outside the scope of the Artifact

PMEvo is in the state of a research prototype, and the provided version is designed as a Vagrant VM to reproduce the port mapping inference on existing measurements.
If you want to try PMEvo to infer a port mapping for your own system, you can still use the code here.

The [`vm_setup` subdirectory](vm_setup) contains the scripts necessary to run PMEvo on a local machine. The [README there](vm_setup/README.md), which describes the artifact, can help in some ways.
To use PMEvo, you need to install and build most things as described in the [`bootstrap.sh`](vm_setup/bootstrap.sh) file (you do not need everything there, docker for example is only for the comparison to Ithemal).

For new measurements on a machine, which are not part of the artifact because reproducing them can be a bit fiddly, you will further need to start a measurement server on the machine you are testing.
That will be a command similar to those in [`start_measurement_servers.sh`](vm_setup/start_measurement_servers.sh), with the right `--isa`, without the `--noroot` (since we need to pin the measurement process to a specific core to get decent accuracy, which requires root privileges), a network port number of your choice (let's say 42042), and the number of out-of-order execution units your microarchitecture has for `--numports`.

There are [files per instruction set architecture](vm_setup/pmevo/measurement-server/input/) that determine what instructions are evaluated, you may adjust those.

You should then run the test client to check whether measurements can be done with your running measurement server:

```
    pmevo/pm-testbench/test_client.py --port 42042 --num 1 --length 1
```

(You might need to specify the `--ssl` argument with the path to the [SSL directory](vm_setup/pmevo/ssl) on your system.)

If it works, you can use the [`gen_experiments.py` script](vm_setup/pmevo/pm-testbench/gen_experiments.py) (with `--port ...` and `--ssl ...` as before, as well as the name of the json file to put the results to) to generate the benchmarks and perform the measurements.
This might take a while and provides several flags to adjust the measurements.
The defaults here and what is searched when first starting the measurement server might be okay for your system, or some playing around with the parameters might be required.
In any case, make sure that the system runs as few other jobs as possible and is configured to not do things like Turboboost or Simultaneous Multithreading (if that applies to your architecture) since these make measurements unstable.
Depending on the number of instructions considered, this might take some time, for the paper evaluation, this took 20-74 hours.

If successful, this gives you the benchmark results you need to follow the [`Inferring Port Mappings` section in the artifact README](vm_setup#inferring-port-mappings).


