#!/usr/bin/env bash

# generate initial website
~/regen_website.sh

# build and start the ithemal docker container
cd ~/foreign/Ithemal/docker
./docker_build.sh && ./my_docker_init.sh

