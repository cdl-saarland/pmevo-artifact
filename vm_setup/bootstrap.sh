#!/usr/bin/env bash

apt-get update
apt-get install -y vim tmux htop
apt-get install -y python3 python3-pip python3-dev python3-pybind11
apt-get install -y git ninja-build libelf-dev libffi-dev cmake docker.io docker-compose

apt-get install -y apache2
mkdir -p /var/www/

pip3 install rpyc
pip3 install seaborn

# get clang+llvm 8.x (for llvm-mca and build jobs)
mkdir -p /opt/deps
cd /opt/deps
git clone --branch release/9.x https://github.com/llvm/llvm-project.git
cd llvm-project
mkdir -p build
cd build
cmake -G Ninja \
    -DLLVM_ENABLE_PROJECTS='clang' \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_TARGETS_TO_BUILD='X86;AArch64' \
    -DLLVM_PARALLEL_LINK_JOBS=1 \
    ../llvm
ninja

# build our own modern z3
cd /opt/deps
git clone --branch z3-4.8.7 https://github.com/Z3Prover/z3.git
cd z3
python scripts/mk_make.py
cd build
make -j4
make install

# copy everything to the homefolder so that it is persistent independent of the
# run folder.
cp -r /vagrant/* /home/vagrant/

# allow us to write the website
chmod 777 -R /var/www/html

# build evo-algo (order matters!)
cd /home/vagrant/pmevo/evo-algo
export CFG=z3
make
export CFG=fastest_no_avx
make
export CFG=fastest
make

# set the PMEVO_BASE environment variable
echo "export PMEVO_BASE=/home/vagrant/pmevo" > /etc/profile.d/pmevo.sh
export PMEVO_BASE=/home/vagrant/pmevo

# by default, use the faster AVX version of evo-algo
/home/vagrant/set_avx.sh on

# build cppfastproc
cd /home/vagrant/pmevo/pm-testbench/cppfastproc
make

# make everything owned by the default user instead of root
chown -R vagrant:vagrant /home/vagrant/*
