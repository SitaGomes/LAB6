import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

GRAPHQL_URL = os.getenv("GITHUB_API_URL")

if __name__ == "__main__":
    print(ACCESS_TOKEN)
    print(GRAPHQL_URL)
    print("Hello World")