## Trace collector based on PADLL

### Setup Trace Collector

```shell
$ cd trace-collector
$ mkdir build; cd build;
$ cmake -DCMAKE_C_COMPILER=$(which gcc) -DCMAKE_CXX_COMPILER=$(which g++) 
$ cmake --build .
$ export PATH_PADLL=$PWD
```

**Note:** In Frontera you can use the script prep_frontera.sh to setup the trace collector. However, do not forget to run the command: 
*export PATH_PADLL=$PWD* 
outside of the script.
***