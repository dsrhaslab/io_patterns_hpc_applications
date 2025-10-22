#!/bin/bash

rm -r build/

mkdir build; cd build

module load gcc/9.1.0 
export CC=`which gcc`
export CXX=`which g++`

cmake ..; cmake --build . 

#Run this command outside of this script.
#export PATH_PADLL=$PWD
