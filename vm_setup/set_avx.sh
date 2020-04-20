#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: './set_avx.sh on' or './set_avx.sh off'"
    exit 1
fi

if [ "$1" == "on" ]; then
    ln -sf fastest/pm-evo ${PMEVO_BASE}/evo-algo/build/default-pm-evo
    echo "AVX instuctions enabled."
elif [ "$1" == "off" ]; then
    ln -sf fastest_no_avx/pm-evo ${PMEVO_BASE}/evo-algo/build/default-pm-evo
    echo "AVX instuctions disabled."
else
    echo "Invalid argument."
    echo "Usage: './set_avx.sh on' or './set_avx.sh off'"
    exit 1
fi

