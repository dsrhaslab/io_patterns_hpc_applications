#!/bin/bash

rm -r build/

mkdir build; cd build

cmake ..; cmake --build . 

#Run this command outside of this script.
#export PATH_PADLL=$PWD
