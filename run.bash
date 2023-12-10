#!/usr/bin/env bash

# usage: ./run.bash -s euw amatria

set -e

dir=$(dirname -- "$( readlink -f -- "$0"; )";)

python -m venv $dir/env
source $dir/env/bin/activate

python -m pip install --upgrade pip
python -m pip install -r $dir/requirements.txt

date="2023-01-01"
until [[ $date > "2023-12-31" ]]; do
       python $dir/src/crawler.py -d $(date -d "$date" "+%d/%m/%Y") $@
       date=$(date -I -d "$date +1 day")
done
