from pymongo import MongoClient
from dotenv import load_dotenv

import os

load_dotenv()

username = os.getenv("MONGO_USERNAME")
password = os.getenv("MONGO_PASSWORD")
cluster_name = os.getenv("MONGO_CLUSTER_NAME")
cluster_address = os.getenv("MONGO_CLUSTER_ADDRESS")

mongodb_uri = f"mongodb+srv://{username}:{password}@{cluster_address}/?retryWrites=true&w=majority&appName={cluster_name}"
port = 8000

client = MongoClient(mongodb_uri, port)

db = client["ProductScan_DB"]

user_data = db["Users_data"]
