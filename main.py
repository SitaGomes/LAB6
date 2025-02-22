from utils import fetch_repositories, save_to_csv

if __name__ == "__main__":
    owner = "sitagomes"
    
    response_data = []
    
    cursor = None
    
    for i in range(1000):  
        result = fetch_repositories(owner, 1, cursor)
        response_data.append(result)
        
        page_info = result.get("data", {}).get("search", {}).get("pageInfo", {})
        cursor = page_info.get("endCursor")
        
        if not page_info.get("hasNextPage"):
            break
    
    mapped_data = []

    for repo_data in response_data:
        mapped_data.extend(repo_data.get("data", {}).get("search", {}).get("nodes", []))

    save_to_csv(mapped_data, "repositories.csv")
