from utils import fetch_repositories

if __name__ == "__main__":
    owner = "sitagomes"
    
    response_data = []
    
    # Start with no cursor for the first page
    cursor = None
    
    # Increase the index by iterating through pages
    for i in range(5):  # For example, fetch 5 repositories one at a time
        result = fetch_repositories(owner, 1, cursor)
        response_data.append(result)
        
        # Retrieve the endCursor for pagination
        page_info = result.get("data", {}).get("search", {}).get("pageInfo", {})
        cursor = page_info.get("endCursor")
        
        # If there's no next page, break out of the loop
        if not page_info.get("hasNextPage"):
            break

    for repo_data in response_data:
        print(repo_data)
