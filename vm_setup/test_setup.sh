#!/bin/bash

# exit when a command fails
set -e

# evaluate an experiment on each server
echo ">> Checking llvmmca measurement server for SKL..."
~/pmevo/pm-testbench/test_client.py --port 42001 --num 1 --length 1
echo ">> Done."

echo ">> Checking llvmmca measurement server for ZEN..."
~/pmevo/pm-testbench/test_client.py --port 42002 --num 1 --length 1
echo ">> Done."

echo ">> Checking llvmmca measurement server for A72..."
~/pmevo/pm-testbench/test_client.py --port 42003 --num 1 --length 1
echo ">> Done."

echo ">> Checking Ithemal measurement server for SKL..."
~/pmevo/pm-testbench/test_client.py --port 42010 --num 1 --length 1
echo ">> Done."

# infer a tiny port mapping
echo ">> Inferring a tiny port mapping..."
~/pmevo/evo-algo/build/default-pm-evo -e ~/pmevo/evo-algo/inputs/singleton_example.exps -c ~/pmevo/evo-algo/run_configs/small.cfg ~/pmevo/evo-algo/inputs/example.exps
echo ">> Done."

# evaluate results with bottleneck algorithm and z3

echo ">> Evaluating trivial experiments with the bottleneck algorithm..."
~/pmevo/evo-algo/build/default-pm-evo -m ~/pmevo/evo-algo/inputs/example.pmap ~/pmevo/evo-algo/inputs/singleton_example.exps
echo ">> Done."

echo ">> Evaluating trivial experiments with the linear program..."
~/pmevo/evo-algo/build/z3/pm-evo -m ~/pmevo/evo-algo/inputs/example.pmap ~/pmevo/evo-algo/inputs/singleton_example.exps
echo ">> Done."

echo "Setup tested successfully."
