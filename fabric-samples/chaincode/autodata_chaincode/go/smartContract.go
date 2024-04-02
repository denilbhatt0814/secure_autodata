package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Smart Contract structure
type IPFSContract struct {
    contractapi.Contract
}

type UserData struct {
    IPFSHashes []string `json:"ipfsHashes"`
}

// AddIPFSHash adds a new IPFS hash to the user's array of IPFS hashes
func (s *IPFSContract) AddIPFSHash(ctx contractapi.TransactionContextInterface, userId string, ipfsHash string) error {
	/**
	* KEY: userId
	* VAL: userData -> []ipfsHash
	*/
    userDataAsBytes, _ := ctx.GetStub().GetState(userId)

    var userData UserData
    if userDataAsBytes != nil {
        // Unmarshal the existing user data
        json.Unmarshal(userDataAsBytes, &userData)
    }

    // Add the new IPFS hash to the user's array of hashes
    userData.IPFSHashes = append(userData.IPFSHashes, ipfsHash)

    // Marshal the updated user data and save it on the ledger
    userDataAsBytes, _ = json.Marshal(userData)
    return ctx.GetStub().PutState(userId, userDataAsBytes)
}

func (s *IPFSContract) AddIPFSHashes(ctx contractapi.TransactionContextInterface, userId string, ipfsHashes []string) error {
	/**
	* KEY: userId
	* VAL: userData -> []ipfsHash
	*/
    userDataAsBytes, _ := ctx.GetStub().GetState(userId)

    var userData UserData
    if userDataAsBytes != nil {
        // Unmarshal the existing user data
        json.Unmarshal(userDataAsBytes, &userData)
    }

    // Add the new IPFS hash to the user's array of hashes
    userData.IPFSHashes = append(userData.IPFSHashes, ipfsHashes...)

    // Marshal the updated user data and save it on the ledger
    userDataAsBytes, _ = json.Marshal(userData)
    return ctx.GetStub().PutState(userId, userDataAsBytes)
}

// GetIPFSHashes retrieves the array of IPFS hashes for a given user
func (s *IPFSContract) GetIPFSHashes(ctx contractapi.TransactionContextInterface, userId string) (*UserData, error) {
    userDataAsBytes, err := ctx.GetStub().GetState(userId)
    if err != nil {
        return nil, fmt.Errorf("failed to read from world state: %v", err)
    }
    if userDataAsBytes == nil {
        return nil, fmt.Errorf("%s does not exist", userId)
    }

    var userData UserData
    json.Unmarshal(userDataAsBytes, &userData)
    return &userData, nil
}

func main() {
    chaincode, err := contractapi.NewChaincode(new(IPFSContract))

    if err != nil {
        fmt.Printf("Error creating IPFSContract chaincode: %s", err.Error())
        return
    }

    if err := chaincode.Start(); err != nil {
        fmt.Printf("Error starting IPFSContract chaincode: %s", err.Error())
    }
}
