#!/bin/bash
[ -f target.luegg ] || (echo target.luegg not exist && exit 0)

worker_dir=pyd_output

[ -d $worker_dir ] && rm -r $worker_dir/* || mkdir $worker_dir

python build.py build_ext --inplace