#!/bin/bash

cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/junofs/users/ybzhang/CCSNMonitor/InstallArea
make
make install
cd ..
