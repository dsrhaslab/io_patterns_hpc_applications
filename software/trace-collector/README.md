## Trace collector

### Setup

```shell
$ cd trace-collector
$ mkdir build
$ cmake -DCMAKE_C_COMPILER=$(which gcc) -DCMAKE_CXX_COMPILER=$(which g++) -B build
$ cd build
$ cmake --build .
```