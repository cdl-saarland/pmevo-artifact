#!/bin/bash

LLVMMCA_SKL=42001
LLVMMCA_ZEN=42002
LLVMMCA_A72=42003

ITHEMAL_SKL=42010

echo "Starting server for llvmmca for SKL at ${LLVMMCA_SKL} (tmux session llvmmca-SKL)."
tmux new-session -d -s llvmmca-SKL \
    pmevo/measurement-server/start_server.py --numports 9 --isa LLVMMCA_SKLx86_64 --noroot --sslpath pmevo/ssl --port ${LLVMMCA_SKL}

echo "Starting server for llvmmca for ZEN at ${LLVMMCA_ZEN} (tmux session llvmmca-ZEN)."
tmux new-session -d -s llvmmca-ZEN \
    pmevo/measurement-server/start_server.py --numports 10 --isa LLVMMCA_ZENPx86_64 --noroot --sslpath pmevo/ssl --port ${LLVMMCA_ZEN}

echo "Starting server for llvmmca for A72 at ${LLVMMCA_A72} (tmux session llvmmca-A72)."
tmux new-session -d -s llvmmca-A72 \
    pmevo/measurement-server/start_server.py --numports 7 --isa LLVMMCA_A72_ARM --noroot --sslpath pmevo/ssl --port ${LLVMMCA_A72}


echo "Starting server for Ithemal for SKL at ${ITHEMAL_SKL} (tmux session ithemal-SKL)."
tmux new-session -d -s ithemal-SKL \
    foreign/Ithemal/docker/my_docker_start.sh

