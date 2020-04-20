# Artifact for "PMEvo: Portable Inference of Port Mappings for Out-of-Order Processors by Evolutionary Optimization"

## Getting Started Guide

### Setup

The artifact is provided as a Vagrant Virtual Machine using the Virtual Box
provider. To run it, you will need to install Vagrant as described here:

    https://www.vagrantup.com/intro/getting-started/install.html

and also Virtual Box as available here:

    https://www.virtualbox.org/

Depending on your hardware platform, it might be necessary to enable
virtualization options in your system's BIOS to use virtual box.

The VM is based on a 64-bit stock Debian 10 (Buster) image. Additionally to
common tools, we preinstalled tmux, vim, and nano for convenience.

In the provided archive, you will find the `pmevo-artifact.box` vagrant box and
a Vagrantfile for configuring your instance of the virtual machine. It comes
with defaults for the number of CPU cores and the available RAM, however the
performance of our tools can be improved by allocating more cores (with
corresponding RAM) if available. We recommend using 4 cores and the 8GBs of
RAM. Additionally, the Vagrantfile specifies a port on the host machine (8080
by default) that will be used to display evaluation results in the web browser
of the host machine.
Once you have adjusted the settings to your liking and installed vagrant and
virtualbox, use the following commands to make the box known to vagrant, to
start the VM, and to establish an SSH connection into the VM:

```
    vagrant box add --name pmevo-artifact pmevo-artifact.box
    vagrant up
    vagrant ssh
```

The VM can be shut down from the host via `vagrant halt` and, once it is no
longer used, deleted from vagrant with `vagrant destroy`.
The pmevo base box can then be removed with `vagrant box remove pmevo-artifact`.

If you are running this artifact on a machine that does not support the AVX2
vector instruction set extension (i.e. an Intel processor from a generation
before Haswell (2013) or an AMD processor older than Excavator (2015)), you
will need to disable the use of vectorized code in the evolutionary algorithm.
This can be done by executing `~/set_avx.sh off` in the VM. This will slow down
the evolution but improves compatibility.

### Content of the Artifact

Most relevant things in the VM are located in the home folder of the `vagrant`
user:
 * The `data` folder contains the measurements and inferred port mappings in
   json format that were used for the evaluation in the paper.
 * The `pmevo` folder contains our tool itself. It comes in three components,
   each located in its own subfolder:
    * `pm-testbench` contains python scripts that are used to drive PMEvo,
      these will be used for reproducing the paper results.
    * The implementation of the core evolutionary algorithm (in C++) is in
      `evo-algo`. It comes prebuilt in a configuration using the fast
      bottleneck algorithm as well as in a configuration using z3 to solve the
      linear program (for performance comparison). It is not necessary to call
      this explicitly as it is called through the scripts in `pm-testbench`.
    * In `measurement_server` is a python server that allows the scripts from
      `pm-testbench` to obtain throughputs for instruction sequences by
      executing them or by passing them to IACA, llvmmca, or Ithemal. The home
      folder includes a script for starting instances of this server for
      llvmmca and Ithemal.
  * In `foreign`, we package Ithemal for comparison. This is the docker
    container available from Ithemal's Github repository with small adjustments
    to run an instance of our measurement server inside the container. Direct
    interaction with the container is not necessary.
  * `website` contains a script to (re)generate the simple static result
    website that is a convenient way of viewing the evaluation results. When
    reports produced by scripts in `pmevo/pm-testbench` are placed in the
    `reports` folder (done implicitly by default), the `~/regen_website.sh`
    script can be used from anywhere within the VM to regenerate the website.
  * The `boostrap.sh` and `post_install.sh` scripts contain the commands that
    were used to set up the vagrant box for reference. They should not be
    executed for the artifact evaluation.

The llvmmca version used for comparison in the paper is located in /opt/deps.

Very recently, during the preparation of this artifact, we found that older
versions of llvmmca, e.g. the one in LLVM 8, performed substantially different
from the current version that is part of LLVM 9. For SKL, its results are close
to those of IACA. For ZEN+, results are more accurate than those of LLVM 9 (a
MAPE of 51.07% vs. the reported MAPE of 127.53%%), but still less accurate than
those of PMEvo. In the case of A72, LLVM 8 and 9 behave identical. Our claim to
have more accurate throughput estimates for port-mapping-bound experiments for
ZEN+ and A72 therefore remains valid. We are working on incorporating this
information into the camera-ready version of the paper and making the llvmmca
developers aware of this performance regression.


### Testing the Setup

To quickly verify that all components of the artifact are working, run the
following commands in the VM via the ssh connection in the home folder of the
default user `vagrant`:

```
./start_measurement_servers.sh
./test_setup.sh
```

The first script starts the measurement servers whereas the second one runs the
major components of the artifact with small inputs.
Both scripts should execute without error.

Lastly, access the results website in a browser on your host system under the
address http://127.0.0.1:8080 .
This should display a (so far) mostly empty website hosted in the VM.



## Scope of the Artifact

### Supported Claims from the paper
  * The core of the evaluation, Section 5.3 can be reproduced with this
    artifact (with the exception of the IACA results, see below). This includes
    evaluating the experiments from the paper with llvmmca, Ithemal, the port
    mapping from uops.info and the one that we inferred with PMEvo for the
    evaluation. For llvmmca and Ithemal, we additionally provide our observed
    results since a full evaluation of our experiments with these tools
    requires considerable amounts of time.
  * Furthermore, the artifact can employ PMEvo to infer mappings from provided
    experiments with measurements for all three considered architectures. The
    results can be evaluated together with the other predictors.
  * The evaluation of the bottleneck simulation algorithm (Section 5.4) can be
    reproduced as well (however with the slower z3 instead of Gurobi as a
    reference solving the LP, see below).
  * For the validation of processor model and measurements as described in
    Section 5.2, we provide our experiments with observed and predicted
    throughputs.


### Not Supported Claims from the paper
  * The artifact is not intended to perform accurate throughput measurements as
    this is naturally a very hardware-sensitive process. Reproducing these
    measurements would require deep interaction with system settings and long
    running times that we consider outside the possibilities of this artifact
    evaluation. Instead, we provide our measurements from our hardware as used
    for the evaluation for Section 5.3. We additionally provide the tool that
    we used to perform these measurements for inspection.
  * The artifact does not include IACA, the Intel Architecture Code Analyzer,
    because of its restrictive license. Here, we also provide the results that
    we extracted from IACA for Section 5.3.
  * As a result of the former two points, the measurement data for Section 5.2
    will not be generated by this artifact.
  * The evaluation of the simulation algorithm (Section 5.4) includes a
    comparison to solving the linear program with Gurobi. Because of the
    restrictive licensing of Gurobi, we cannot provide a version of it for the
    artifact. We do however provide a similar implementation using the z3
    theorem prover for LP solving. This is expected to be substantially slower
    than Gurobi but can still be a helpful comparison.



## Step-by-Step Guide

For the following guide, notice that all python scripts contain a command line
help accessible via `./<cmd>.py --help`.

### Evaluating Prediction Accuracy

First, make sure that the measurement servers are started:
```
~/start_measurement_servers.sh
```
Then choose the experiment set to evaluate from the `data` subfolders. Each
subfolder comes with `exps_eval.json`, `exps_eval_small.json` and corresponding
`annotated` files. The `exps_eval.json` files each contain the 40,000
experiments that were used for the paper, whereas the `small` files contain
only the first 2,000 of these. All these files include the throughput
measurements performed on the actual hardware (and the IACA predictions for
SKL).
The annotated files additionally include the observed results from llvmmca and
(for SKL) Ithemal to allow skipping the evaluation of these tools. Using them
to evaluate 2,000 experiments takes a few hours per tool, 40,000 experiments
can require a few days.
Additionally, we provide tiny experiment sets, consisting only of the 20 first
experiments from the original sets. These are not sufficient for a meaningful
evaluation of the approaches, but may be used to investigate the evaluation on
small examples.

All following commands are expected to be executed from `~/pmevo/pm-testbench`.
If you decide to not use the annotated files, use the following commands to
evaluate the experiments:
```
./evaluate_experiments.py --port 42001 -x "llvmmca" --out ~/results/skl_eval00.json <SKL base experiment file>.json
./evaluate_experiments.py --port 42010 -x "Ithemal" --out ~/results/skl_eval01.json ~/results/skl_eval00.json
./evaluate_experiments.py --port 42002 -x "llvmmca" --out ~/results/zen_eval01.json <ZEN base experiment file>.json
./evaluate_experiments.py --port 42003 -x "llvmmca" --out ~/results/a72_eval01.json <A72 base experiment file>.json
```
These commands annotate the predicted throughputs of the tools that are
obtained via the measurement server instances to the experiment list (with the
given identifier) and store the resulting experiment list in the specified new
json files.
The measurement server generates input programs that are passed to the
respective tool. These can be found in `/tmp/pite_4200*/benchmark.c` for the
llvmmca servers and in the respective folder in the docker container for
Ithemal. To enter Ithemal's docker container, you can run the
`docker/docker_connect.sh` script in the Ithemal directory. It will open a tmux
session within the container.

To evaluate the provided port mappings (a matter of seconds for both input
sizes), use the same script with a mapping argument instead of the `--port`
argument on either the pre-annotated experiment files or the newly annotated
experiment files from above:
```
./evaluate_experiments.py -m ~/data/SKL/mapping_uops_info.json -x "uops.info" --out ~/results/skl_eval02.json <SKL experiment file>.json
./evaluate_experiments.py -m ~/data/SKL/mapping_pmevo.json -x "PMEvo" --out ~/results/skl_eval03.json ~/results/skl_eval02.json
./evaluate_experiments.py -m ~/data/ZEN/mapping_pmevo.json -x "PMEvo" --out ~/results/zen_eval02.json <ZEN experiment file>.json
./evaluate_experiments.py -m ~/data/A72/mapping_pmevo.json -x "PMEvo" --out ~/results/a72_eval02.json <A72 experiment file>.json
```

To generate statistics and histograms from these annotated experiment files,
run the following commands:
```
./gen_histograms.py ~/skl_eval03.json
./gen_histograms.py ~/zen_eval02.json
./gen_histograms.py ~/a72_eval02.json
```
These produce report files in the `~/reports/` folder that can be translated
into the website as follows:
```
~/regen_website.sh
```
The resulting website can be viewed by default on the host machine in a web
browser under the address `http://127.0.0.1:8080`. It should include heatmaps
and accuracy metrics similar to those in Section 5.3 of the paper (only less
dense if the small input size was chosen).


### Inferring Port Mappings

In the previous section, we have evaluated the provided mappings produced by
PMEvo. Here, we will use PMEvo to infer similar mappings.

Again, all following commands are expected to be executed from
`~/pmevo/pm-testbench`.
You can use the following commands to infer mappings for all three evaluated
architectures:
```
./infer.py --out ~/results/new_pmevo_skl.json --singletonexps ~/data/SKL/exps_singletons.json infer_configs/<config>.json ~/data/SKL/exps_pairs.json
./infer.py --out ~/results/new_pmevo_zen.json --singletonexps ~/data/ZEN/exps_singletons.json infer_configs/<config>.json ~/data/ZEN/exps_pairs.json
./infer.py --out ~/results/new_pmevo_a72.json --singletonexps ~/data/A72/exps_singletons.json infer_configs/<config>.json ~/data/A72/exps_pairs.json
```
These commands use the provided throughput measurements that are pre-annotated
to the singleton and pair experiment sets.
The time required by these commands depends on many factors:
 * The configuration used. These are in `~/pmevo/pm-testbench/infer_configs/`
   and reference corresponding configurations in
   `~/pmevo/evo-algo/run_configs`. The paper evaluation used the `default`
   configuration, the others are adjusted to require less time and compute
   resources. It is to be expected that the reduced configurations lead to not
   quite as accurate mappings as the default one.
 * The resources available in the VM. PMEvo's evolutionary algorithm is at its
   core embarrassingly parallel and therefore parallelized with OpenMP to use
   all CPU cores available.
 * Whether you disabled the AVX2-vectorization, since our fastest
   implementation of the bottleneck simulation algorithm is vectorized.
 * Chance, since PMEvo uses a randomized algorithm (eventual termination is
   however enforced).

We found that with 4 cores supporting AVX2 and 8GB of RAM, the medium
configuration terminated within 15-45 minutes with reasonable results. We
therefore recommend it for the artifact evaluation.
Even using the default configuration, the inferred mappings will very likely
not be identical to the provided ones due to the randomized nature of the
algorithm.

The resulting mappings can be evaluated on the provided experiments as
described in the previous section. Evaluation results are expected to look
similar to those of the provided mappings.


### Evaluating the Bottleneck Simulation Algorithm

This part of the evaluation (Section 5.4) is performed with a different set of
scripts. Data for the performance with varying number of ports and length of
experiments is collected as follows:
```
./compare_sim_time.py --out ~/results/cmp_sim_time_num_ports.json ~/pmevo/evo-algo/build/
./compare_sim_time.py --out ~/results/cmp_sim_time_exp_len.json --explen ~/pmevo/evo-algo/build/
```
Since the settings used for the paper require several hours to complete, these
scripts use smaller loads that run in a few minutes by default. If desired, the
original settings can be used with the `--full` argument for both calls.

The reports for both evaluations can be produced as follows:
```
./compare_sim_time_plot.py ~/results/cmp_sim_time_num_ports.json
./compare_sim_time_plot.py --explen ~/results/cmp_sim_time_exp_len.json
```
These commands again create reports in the `~/reports/` folder that can be
incorporated into the website as follows:
```
~/regen_website.sh
```
While the resources available to the VM should not influence the results, the
use of AVX2 instructions does, we found a speedup of 4-6x using vectorized
code. Since the Gurobi license is too restrictive for providing it in this
artifact, we use z3 here to solve the LP as a baseline. We found z3 to be
substantially slower than Gurobi, however generally similar when compared to
the performance of the bottleneck simulation algorithm.


### Processor Model and Measurements
Since Section 5.2 of the paper compares observations whose generation is
outside of the scope of this artifact, we only provide our gathered data here
together with a script to generate the corresponding plot.
These numbers are available in the `~/data/SKL/varying_length/` folder.
The plot for the website can be produced out of these as follows:
```
./gen_varying_len_plot.py ~/data/SKL/varying_length/*.json
```


### Measuring Throughput
We decided against including throughput measurements in the artifact evaluation
since it is very time consuming and requires settings in the BIOS and operating
system of the System under Test that cannot be reasonably expected in an
artifact evaluation process.
Nevertheless, we include the tools we used to measure the throughputs for
inspection by the interested reader. Experiments (both for evaluation and for
inference training data) are produced with the `gen_experiments.py` script.
It samples/generates the experiments accordingly and uses a measurement server
on the System under Test to measure their throughput.

