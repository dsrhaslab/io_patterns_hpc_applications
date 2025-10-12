#!/bin/bash

module load openfoam

export FOAM_RUN=$SCRATCH/My_OpenFOAM/9.0/run
mkdir -p $FOAM_RUN

cd $FOAM_RUN

cp -r $FOAM_TUTORIALS/ .