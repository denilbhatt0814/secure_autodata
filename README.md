# secure_autodata

## Setup

```bash
git clone https://github.com/hyperledger/fabric-samples.git
cd fabric-samples
curl -sSL https://bit.ly/2ysbOFE | bash -s
cd test-network
./network.sh up createChannel
```

## Packaging and installing smartcontract

```bash
cd fabric-samples/test-network
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
. ./scripts/envVar.sh
setGlobals 1
peer lifecycle chaincode package autodata_chaincode.tar.gz --path ../chaincode/autodata_chaincode/go/ --lang golang --label autodata_chaincode_1
peer lifecycle chaincode install autodata_chaincode.tar.gz
```

**Copy the packageID returned after installation**

```bash
➜ /workspaces/secure_autodata/fabric-samples/test-network (main) $ peer lifecycle chaincode install autodata_chaincode.tar.gz

2024-04-02 04:49:47.086 UTC 0001 INFO [cli.lifecycle.chaincode] submitInstallProposal -> Installed remotely: response:<status:200 payload:"\nUautodata_chaincode_1:472d7d4f835cf1568c5a07e69497de472048bf24912885f09502f40c5e4ae36f\022\024autodata_chaincode_1" >
2024-04-02 04:49:47.086 UTC 0002 INFO [cli.lifecycle.chaincode] submitInstallProposal -> Chaincode code package identifier: autodata_chaincode_1:472d7d4f835cf1568c5a07e69497de472048bf24912885f09502f40c5e4ae36f
```

_Chaincode code package identifier: autodata_chaincode_1:472d7d4f835cf1568c5a07e69497de472048bf24912885f09502f40c5e4ae36f_

```bash
cd fabric-samples/test-network
./network.sh deployCC -ccn autodata_chaincode -ccp ../chaincode/autodata_chaincode/go/ -ccl go
```

## Testing setup

```bash
cd fabric-samples/test-network
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile $ORDERER_CA --channelID mychannel --name autodata_chaincode -c '{"function":"AddIPFSHash","Args":["user1", "QmTzYXNzaGFzaEZvcklQRlM="]}' --peerAddresses localhost:7051 --tlsRootCertFiles $PEER0_ORG1_CA
peer chaincode query -C mychannel -n autodata_chaincode -c '{"function":"GetIPFSHashes","Args":["user1"]}'
```

## Monitoring

```bash
cd fabric-samples/test-network
./monitordocker.sh fabric_test
```

## client setup

```bash
git clone https://github.com/hyperledger/fabric-sdk-py.git
cd fabric-sdk-py
make install
```

## installs

```bash
pip install ipfs-api
```
