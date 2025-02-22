import requests
import os
from querys import querys
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

GRAPHQL_URL = os.getenv("GITHUB_API_URL")

# Function to execute the GraphQL query
def fetch_repositories(owner, first, cursor):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    variables = {
        "first": first,
        "cursor": cursor,
        "owner": owner
    }

    response = requests.post(
        GRAPHQL_URL,
        json={"query": querys, "variables": variables},
        headers=headers,
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")