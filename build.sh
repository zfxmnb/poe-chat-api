# /usr/bin/env bash
cmd=$1
if [[ $cmd != "dev" ]]; then
    cmd='build'
fi
cd app/
if [ ! -d "node_modules" ]; then
    yarn
fi
yarn $cmd