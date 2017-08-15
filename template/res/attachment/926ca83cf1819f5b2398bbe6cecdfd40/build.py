from distutils.core import setup
from Cython.Build import cythonize

import os
import sys

worker_dir = 'pyd_output'

def build_dir(dir):
	os.chdir(dir)
	files = os.listdir(os.getcwd())

	target = []
	for f in files:
		if f.endswith('.py') and os.path.isfile(f):
			target.append(f)
		elif os.path.isdir(f):
			build_dir(f)

	if target:
		setup(
			ext_modules = cythonize(target)
		)
	os.system('rm *.c')
	os.system('rm *.py')
	os.system('rm -r build')
	os.chdir('..')


fid = open('target.luegg')
data = fid.read()
fid.close()

dirs = data.split('\n')

for dir in dirs:
	if not dir or not os.path.isdir(dir):
		continue
	cmd = 'cp -r %s %s/' % (dir, worker_dir)
	print cmd
	os.system(cmd)
	os.chdir(worker_dir)
	build_dir(dir)
	os.chdir('..')

