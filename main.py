import pandas as pd
import os
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from typing import List
import asyncio
from hfc.fabric import Client
import time
import json
from io import StringIO
# import dotenv
# dotenv.load_dotenv()
# Placeholder for IPFS and smart contract interaction libraries

# Initialize the Hyperledger Fabric client
client = Client(net_profile="./network.json")
org1_admin = client.get_user(org_name='org1.example.com', name='Admin')
client.new_channel('mychannel')
channel_name = 'mychannel'
chaincode_name = 'autodata_chaincode'

# Global variables
SPLIT_SIZE = 50  # Number of rows per split
# JWT=os.getenv("JWT")
JWT="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI5ZGZhMjcwNi0zN2Q5LTRkNDEtODY1Ni04Njg3Zjg3NGRkZmMiLCJlbWFpbCI6ImRlbmlsYmhhdHQyMDA0QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImlkIjoiRlJBMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfSx7ImlkIjoiTllDMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI0ODY5NmE4MDJmYWQ1ODAxOGI2NyIsInNjb3BlZEtleVNlY3JldCI6IjRkYzEwZGI2MjZkODhlYTk5NzE0NmM3OGViNjdhODYxNTExNTc5OGIzOGIwNzkyMTc1ODI4N2Q3Njg1NzliNTIiLCJpYXQiOjE3MTE5OTI4OTB9.-htnX6xI8slvuJvRwW7OlfrTbk4xFtiAwPF-vrL66RY"

loop = asyncio.get_event_loop()

def wait(foo):
    return loop.run_until_complete(foo)

def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame.
    """
    return pd.read_csv(file_path)

def save_df(df: pd.DataFrame, file_path: str):
    df.to_csv(file_path, index=False)

def split_dataframe(df: pd.DataFrame, split_size: int) -> List[pd.DataFrame]:
    """
    Split a DataFrame into smaller DataFrames of specified size.
    """
    return [df.iloc[i:i + split_size] for i in range(0, df.shape[0], split_size)]

def dataframe_to_csv(df: pd.DataFrame, file_path: str):
    """
    Save a DataFrame to a CSV file.
    """
    df.to_csv(file_path, index=False)

def delete_file(file_path: str):
    """
    Delete file from the File System
    """
    os.remove(file_path)

def upload_to_ipfs(file_path: str) -> str:
    """
    Upload a file to IPFS via Pinata and return the IPFS hash.
    """
    file_name = os.path.basename(file_path)
    
    multipart_data = MultipartEncoder(
        fields={
            'file': (file_name, open(file_path, 'rb'), 'application/octet-stream'), 
            'pinataMetadata': '{"name": "' + file_name + '"}',
            'pinataOptions': '{"cidVersion": 0}'
        }
    )

    headers = {
        'Content-Type': multipart_data.content_type,
        'Authorization': f'Bearer {JWT}'
    }

    response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS', 
                             data=multipart_data, 
                             headers=headers)
    
    if response.status_code == 200:
        ipfs_hash = response.json()["IpfsHash"]
        print(f"File {file_name} successfully uploaded to IPFS with hash: {ipfs_hash}")
        return ipfs_hash
    else:
        print(f"Failed to upload file {file_name}: {response.text}")
        return ""

def fetch_from_ipfs(ipfs_hash: str) -> str:
    """
    Fetches content from an IPFS hash using the Pinata gateway (or any other IPFS gateway).
    """
    url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content.decode('utf-8')  # Assumes the content is text-based (e.g., CSV)
    else:
        raise Exception(f"Failed to fetch file from IPFS with hash: {ipfs_hash}")

def str_to_df(csv_content: str) -> pd.DataFrame:
    """
    Converts a CSV string to a pandas DataFrame.
    """
    csv_string_io = StringIO(csv_content)
    return pd.read_csv(csv_string_io)

def retrieve_data_from_hashes(ipfs_hashes: List[str]) -> pd.DataFrame:
    """
    Retrieves data from a list of IPFS hashes and concatenates it into a single DataFrame.
    """
    dfs = []  # List to store individual data frames
    for _hash in ipfs_hashes:
        data = fetch_from_ipfs(_hash)
        _df = str_to_df(data)
        dfs.append(_df)  # Append the DataFrame to the list
    
    if dfs:  # Check if the list is not empty
        df = pd.concat(dfs, ignore_index=True)  # Concatenate all DataFrames in the list
    else:
        df = pd.DataFrame()  # Return an empty DataFrame if no data was fetched
    return df

async def store_hash_on_contract(user_address: str, ipfs_hash: str):
    """
    Store a single IPFS hash on the blockchain via a smart contract function.
    """
    args = [user_address, ipfs_hash]
    response = await client.chaincode_invoke(
        requestor=org1_admin,
        channel_name=channel_name,
        peers=['peer0.org1.example.com', 'peer0.org2.example.com'],
        cc_name=chaincode_name,
        fcn='AddIPFSHash',
        args=args,
        cc_pattern=None
    )
    print(f"Added IPFS hash {ipfs_hash} on-chain")
    return response

def store_hashes_on_contract(user_address: str, ipfs_hashes: List[str]):
    """
    Stores the list of IPFS hashes on a blockchain via a smart contract
    """
    ipfs_hashes_str = json.dumps(ipfs_hashes)
    args = [user_address, ipfs_hashes_str]
    response = wait(client.chaincode_invoke(
        requestor=org1_admin,
        channel_name=channel_name,
        peers=['peer0.org1.example.com', 'peer0.org2.example.com'],
        cc_name=chaincode_name,
        fcn='AddIPFSHashes',
        args=args,
        cc_pattern=None
    ))
    print(f"Added IPFS hash {ipfs_hashes} on-chain")
    return response
    

async def retrieve_hashes_from_contract(user_address: str) -> List[str]:
    """
    Retrieve the list of IPFS hashes stored in a smart contract for a user.
    """
    # Implementation depends on the blockchain and contract
    args = [user_address]
    response = await client.chaincode_query(
        requestor=org1_admin,
        peers=['peer0.org1.example.com'],
        channel_name=channel_name,
        cc_name=chaincode_name,
        fcn='GetIPFSHashes',
        args=args
    )
    return json.loads(response)['ipfsHashes']

def main(file_path: str, user_address: str):
    # Load CSV
    df = load_csv(file_path)
    
    # Split DataFrame
    dfs = split_dataframe(df, SPLIT_SIZE)
    
    ipfs_hashes = []
    for i, split_df in enumerate(dfs, start=1):
        # Save split DataFrame to CSV
        split_file_path = f"{user_address}_split_{i}.csv"
        dataframe_to_csv(split_df, split_file_path)
        
        # Upload to IPFS
        ipfs_hash = upload_to_ipfs(split_file_path)
        ipfs_hashes.append(ipfs_hash)
        print(f"Uploaded split {i} to IPFS with hash: {ipfs_hash}")
        delete_file(split_file_path)

    # Store IPFS hashes on blockchain
    store_hashes_on_contract(user_address, ipfs_hashes)
    
    print(f"Stored IPFS hashes on blockchain for user: {user_address}")

if __name__ == "__main__":
    # Example usage
    file_path = "./data.csv"
    user_address = "user1"
    main(file_path, user_address)
    print("Sleeping...")
    time.sleep(10)
    ipfs_hashes = wait(retrieve_hashes_from_contract(user_address))
    print(ipfs_hashes)
    combined_df = retrieve_data_from_hashes(ipfs_hashes)
    save_df(combined_df, f"{user_address}_combined.csv")