from utils import fetch_repositories, save_to_csv, get_issue_closure_ratio, get_primary_language_distribution, get_pull_requests_data, get_release_data, get_repository_age, get_update_frequency, load_data, plot_issue_closure_ratio, plot_primary_language_distribution, plot_pull_requests, plot_releases, plot_repository_age, plot_update_frequency

if __name__ == "__main__":

    option = input("Do you want to fetch repositories? (y/n): ").lower().strip()

    if(option == "y"):
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
    else:
        # Adjust the CSV file path as needed
        df = load_data("repositories.csv")
        
        # Pergunta 1
        print(get_repository_age(df))
        plot_repository_age(df)
        
        # Pergunta 2
        print(get_pull_requests_data(df))
        plot_pull_requests(df)
        
        # Pergunta 3
        print(get_release_data(df))
        plot_releases(df)
        
        # Pergunta 4
        print(get_update_frequency(df))
        plot_update_frequency(df)
        
        # Pergunta 5
        print(get_primary_language_distribution(df))
        plot_primary_language_distribution(df)
        
        # Pergunta 6
        print(get_issue_closure_ratio(df))
        plot_issue_closure_ratio(df)