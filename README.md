# Artifact for "PMEvo: Portable Inference of Port Mappings for Out-of-Order Processors by Evolutionary Optimization"

Also see the [project website](https://compilers.cs.uni-saarland.de/projects/portmap/) and the [paper](https://compilers.cs.uni-saarland.de/papers/ritter_pmevo_pldi20.pdf).

A pre-built version of this VM is available [here](https://kingsx.cs.uni-saarland.de/owncloud/index.php/s/xXrXJdj7pSngfbS) for download.

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

