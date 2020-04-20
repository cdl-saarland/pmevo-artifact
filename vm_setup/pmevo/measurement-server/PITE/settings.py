# vim: et:ts=4:sw=4:fenc=utf-8

import os

class Settings:
    def finalize(self):
        self.finalized = True

    def __setattr__(self, name, value):
        if hasattr(self, "finalized"):
            assert not self.finalized
        super().__setattr__(name, value)

    @property
    def benchmark_src(self):
        return os.path.join(self.output_dir, "benchmark.c")

    @property
    def benchmark_bin(self):
        return os.path.join(self.output_dir, "benchmark")

    @property
    def machine_dependent_params_file(self):
        return os.path.join(self.output_dir, "params.json")

    def __init__(self):
        self.finalized = False
        # command line arguments to specify how the setup is done and on which
        # core the experiments are executed
        self.preciseStart = None
        self.newSU = None
        self.core = None

        self.no_root = False

        # paths to the system files where the frequency is controlled
        cpufreq_path = "/sys/devices/system/cpu/cpu{core}/cpufreq/"
        self.scaling_gov = os.path.join(cpufreq_path, "scaling_governor")
        self.scaling_max_freq = os.path.join(cpufreq_path, "scaling_max_freq")
        self.scaling_min_freq = os.path.join(cpufreq_path, "scaling_min_freq")

        self.scaling_freq = os.path.join(cpufreq_path, "scaling_cur_freq")

        # variables necessary to compute the instruction-throughput from the
        # experiment result
        self.freq = None

        self.num_total_dynamic_insns = None
        self.num_insns_per_iteration = None

        self.default_num_repetitions = 5
        self.default_max_uncertainty = 0.05

        self.input_dir = os.path.join(os.path.dirname(__file__), "../input/")
        self.output_dir = os.path.join(os.path.dirname(__file__), "../output/")

        # XXX These paths might need adjustment for usage outside of the VM.
        self.cc = "/opt/deps/llvm-project/build/bin/clang"
        if not os.path.exists(self.cc):
            self.cc = "gcc"
        self.iaca_path = "/opt/deps/iaca"
        self.llvm_mca_path = "/opt/deps/llvm-project/build/bin/"

        # variables that are used for the setup phase, first for the precise
        # setup second for the fast setup
        # self.loop_min_time = 0.5
        # self.loop_max_time = 5
        self.loop_target_time = 0.4

        self.setup_configs = {
                "default": {
                    "start_loop_length": 100,
                    "end_loop_length": 10000,
                    "step_width": 1000,
                    "fine_grained_step_width": 500,
                    "num_samples": 5,
                    },
                "precise": {
                    "start_loop_length": 100,
                    "end_loop_length": 70000,
                    "step_width": 500,
                    "fine_grained_step_width": 25,
                    "num_samples": 11,
                    },
                }


