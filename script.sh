#!/bin/bash
cd fabric-samples/test-network
./network.sh down
./network.sh up createChannel
./network.sh deployCC -ccn autodata_chaincode -ccp ../chaincode/autodata_chaincode/go/ -ccl go
./monitordocker.sh fabric_test