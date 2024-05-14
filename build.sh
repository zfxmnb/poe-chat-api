# /usr/bin/env bash
cmd=$1
if [[ $cmd != "dev" ]]; then
    cmd='build'
fi
if [ -d "app/node_modules" ]; then
    yarn
fi
cd app/ && yarn $cmd