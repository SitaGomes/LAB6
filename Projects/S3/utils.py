import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import time
from tqdm import tqdm
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def execute_query(query, variables, max_retries=5, retry_delay=10, timeout=30):
    """Execute a GraphQL query against GitHub's API with improved error handling"""
    retries = 0
    
    while retries < max_retries:
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=timeout
            )
            
            # Handle rate limiting (403)
            if response.status_code == 403:
                reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                current_time = int(time.time())
                sleep_time = max(reset_time - current_time + 5, 60)
                
                print(f"API rate limit exceeded. Waiting for {sleep_time} seconds...")
                time.sleep(sleep_time)
                retries += 1
                continue
                
            # Handle server errors (5xx)
            elif 500 <= response.status_code < 600:
                sleep_time = retry_delay * (2 ** retries)  # Exponential backoff
                print(f"Server error {response.status_code}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                retries += 1
                continue
            
            # For other errors, raise the exception
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Query failed: {e}")
            
            # If we've exhausted retries, return None
            if retries >= max_retries - 1:
                print(f"Max retries ({max_retries}) exceeded. Giving up on this query.")
                return None
                
            # Otherwise increment retry counter and try again
            retries += 1
            sleep_time = retry_delay * (2 ** retries)
            print(f"Retrying in {sleep_time} seconds... (Attempt {retries+1}/{max_retries})")
            time.sleep(sleep_time)
    
    return None

def fetch_top_repositories(first=100, cursor=None, timeout=30):
    """Fetch top GitHub repositories based on stars"""
    from query import query_repositories
    variables = {
        "first": first,
        "cursor": cursor
    }
    return execute_query(query_repositories, variables, timeout=timeout)

def fetch_repository_pr_count(owner, name, timeout=30):
    """Fetch pull request count for a specific repository"""
    from query import query_repository_pr_count
    variables = {
        "owner": owner,
        "name": name
    }
    return execute_query(query_repository_pr_count, variables, timeout=timeout)

def fetch_pull_requests(owner, name, first=100, cursor=None, timeout=30):
    """Fetch pull requests for a specific repository"""
    from query import query_pull_requests
    variables = {
        "owner": owner,
        "name": name,
        "first": first,
        "cursor": cursor
    }
    return execute_query(query_pull_requests, variables, timeout=timeout)

def fetch_pull_request_details(owner, name, pr_number, timeout=30):
    """Fetch details for a specific pull request"""
    from query import query_pull_request_details
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_details, variables, timeout=timeout)

def fetch_pull_request_review_count(owner, name, pr_number, timeout=30):
    """Fetch review count for a specific pull request"""
    from query import query_pull_request_review_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_review_count, variables, timeout=timeout)

def fetch_pull_request_comments_count(owner, name, pr_number, timeout=30):
    """Fetch comments count for a specific pull request"""
    from query import query_pull_request_comments_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_comments_count, variables, timeout=timeout)

def fetch_pull_request_participants_count(owner, name, pr_number, timeout=30):
    """Fetch participants count for a specific pull request"""
    from query import query_pull_request_participants_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_participants_count, variables, timeout=timeout)

def gather_repository_data(limit=200, timeout=30):
    """Gather top repositories data according to criteria"""
    repositories = []
    cursor = None
    
    progress_bar = tqdm(total=limit, desc="Fetching repositories")
    
    while len(repositories) < limit:
        batch_size = min(10, limit - len(repositories))  # Reduced batch size further to 10
        result = fetch_top_repositories(batch_size, cursor, timeout=timeout)
        
        if not result or "data" not in result or "search" not in result["data"]:
            print("Failed to fetch repositories or received invalid response")
            if result:
                print(f"Response: {json.dumps(result, indent=2)}")
            time.sleep(30)  # Wait before trying again
            continue
        
        page_info = result["data"]["search"]["pageInfo"]
        cursor = page_info["endCursor"]
        
        repo_nodes = result["data"]["search"]["nodes"]
        
        # Check PR counts in a separate step
        for repo in repo_nodes:
            if not repo:
                continue
                
            try:
                owner = repo["owner"]["login"]
                name = repo["name"]
                
                print(f"Checking PR count for {owner}/{name}")
                
                # Fetch PR count separately
                time.sleep(1)  # Add a delay to avoid rate limiting
                pr_count_result = fetch_repository_pr_count(owner, name, timeout=timeout)
                
                if not pr_count_result or "data" not in pr_count_result or not pr_count_result["data"]["repository"]:
                    print(f"Failed to fetch PR count for {owner}/{name}")
                    continue
                
                pr_count = pr_count_result["data"]["repository"]["pullRequests"]["totalCount"]
                
                # Add PR count to repository data
                repo["pullRequests"] = {"totalCount": pr_count}
                
                if pr_count >= 100:
                    repositories.append(repo)
                    print(f"Found suitable repository: {owner}/{name} with {pr_count} PRs")
                    progress_bar.update(1)
                    
                    # Save incrementally to avoid losing data
                    if len(repositories) % 10 == 0:
                        temp_df = pd.DataFrame(repositories)
                        temp_df.to_csv(f'Projects/S3/data/repositories_temp_{len(repositories)}.csv', index=False)
                        print(f"Saved {len(repositories)} repositories to temporary file")
                    
                    if len(repositories) >= limit:
                        break
            except (KeyError, TypeError) as e:
                print(f"Error processing repository: {e}")
                continue
        
        if not page_info["hasNextPage"] or len(repositories) >= limit:
            break
            
        # Add a longer delay between repository batches
        time.sleep(5)
            
    progress_bar.close()
    
    if not repositories:
        print("Warning: No repositories matched the criteria. Check query or increase stars threshold.")
    
    # Trim to exact limit
    return repositories[:limit]

def gather_pull_requests(repositories, timeout=30):
    """Gather pull requests from selected repositories that meet criteria"""
    all_prs = []
    
    for repo in tqdm(repositories, desc="Processing repositories"):
        owner = repo["owner"]["login"]
        name = repo["name"]
        
        print(f"\nProcessing repository: {owner}/{name}")
        
        prs = []
        cursor = None
        
        # Limit PRs per repository to avoid excessive API calls
        max_prs_per_repo = 50  # Reduced from 100 to 50
        repo_pr_count = 0
        
        # Step 1: Fetch basic PR data (timestamps, state)
        while repo_pr_count < max_prs_per_repo:
            batch_size = min(10, max_prs_per_repo - repo_pr_count)  # Reduced batch size to 10
            result = fetch_pull_requests(owner, name, batch_size, cursor, timeout=timeout)
            
            if not result or "data" not in result or "repository" not in result["data"]:
                print(f"Failed to fetch PRs for {owner}/{name} or received invalid response")
                if result:
                    print(f"Response: {json.dumps(result, indent=2)}")
                break
                
            if result["data"]["repository"] is None:
                print(f"Repository {owner}/{name} not found or not accessible")
                break
                
            pr_data = result["data"]["repository"]["pullRequests"]
            page_info = pr_data["pageInfo"]
            cursor = page_info["endCursor"]
            
            if not pr_data["nodes"]:
                print(f"No more PRs found for {owner}/{name}")
                break
            
            # Process fetched PRs
            for pr in pr_data["nodes"]:
                if not pr:
                    continue
                
                try:
                    # Calculate analysis duration in hours
                    created_at = datetime.fromisoformat(pr["createdAt"].replace('Z', '+00:00'))
                    
                    # Use appropriate end time based on PR state
                    if pr["state"] == "MERGED" and pr.get("mergedAt"):
                        end_time = datetime.fromisoformat(pr["mergedAt"].replace('Z', '+00:00'))
                    elif pr.get("closedAt"):
                        end_time = datetime.fromisoformat(pr["closedAt"].replace('Z', '+00:00'))
                    else:
                        continue  # Skip PRs without a proper end time
                    
                    # Calculate duration in hours
                    duration_hours = (end_time - created_at).total_seconds() / 3600
                    
                    # Only proceed with PRs reviewed for at least 1 hour
                    if duration_hours > 1:
                        pr_number = pr["number"]
                        
                        # Step 2: Check if PR has reviews (separately)
                        time.sleep(1)  # Add delay between requests
                        review_result = fetch_pull_request_review_count(owner, name, pr_number, timeout=timeout)
                        
                        if not review_result or "data" not in review_result or not review_result["data"]["repository"] or not review_result["data"]["repository"]["pullRequest"]:
                            print(f"Failed to fetch review count for PR #{pr_number}")
                            continue
                        
                        reviews_count = review_result["data"]["repository"]["pullRequest"]["reviews"]["totalCount"]
                        
                        # Only include PRs with at least one review
                        if reviews_count >= 1:
                            # Step 3: Fetch additional PR details
                            time.sleep(1)
                            details_result = fetch_pull_request_details(owner, name, pr_number, timeout=timeout)
                            
                            if not details_result or "data" not in details_result or not details_result["data"]["repository"] or not details_result["data"]["repository"]["pullRequest"]:
                                print(f"Failed to fetch details for PR #{pr_number}")
                                continue
                            
                            # Add details to PR data
                            pr_details = details_result["data"]["repository"]["pullRequest"]
                            for key, value in pr_details.items():
                                pr[key] = value
                            
                            # Step 4: Fetch comments count
                            time.sleep(1)
                            comments_result = fetch_pull_request_comments_count(owner, name, pr_number, timeout=timeout)
                            
                            if comments_result and "data" in comments_result and comments_result["data"]["repository"] and comments_result["data"]["repository"]["pullRequest"]:
                                comments_count = comments_result["data"]["repository"]["pullRequest"]["comments"]["totalCount"]
                                pr["comments"] = {"totalCount": comments_count}
                            
                            # Step 5: Fetch participants count
                            time.sleep(1)
                            participants_result = fetch_pull_request_participants_count(owner, name, pr_number, timeout=timeout)
                            
                            if participants_result and "data" in participants_result and participants_result["data"]["repository"] and participants_result["data"]["repository"]["pullRequest"]:
                                participants_count = participants_result["data"]["repository"]["pullRequest"]["participants"]["totalCount"]
                                pr["participants"] = {"totalCount": participants_count}
                            
                            # Add review count and repository info to PR data
                            pr["reviews"] = {"totalCount": reviews_count}
                            pr["repository"] = {"owner": owner, "name": name}
                            pr["duration_hours"] = duration_hours
                            
                            prs.append(pr)
                            repo_pr_count += 1
                            print(f"Added PR #{pr_number} with {reviews_count} reviews")
                            
                            # Break if we've reached the limit for this repository
                            if repo_pr_count >= max_prs_per_repo:
                                break
                except (ValueError, KeyError, TypeError) as e:
                    print(f"Error processing PR {pr.get('number')}: {e}")
                    continue
            
            if not page_info["hasNextPage"] or repo_pr_count >= max_prs_per_repo:
                break
                
            # Add a delay between PR batches
            time.sleep(3)
        
        print(f"Added {len(prs)} PRs from {owner}/{name}")
        all_prs.extend(prs)
        
        # Save incrementally to avoid losing all data if there's an error
        if len(all_prs) > 0:
            temp_df = pd.DataFrame(all_prs)
            temp_df.to_csv(f'Projects/S3/data/pull_requests_temp_{len(all_prs)}.csv', index=False)
            print(f"Saved {len(all_prs)} PRs to temporary file")
            
        # Add a delay between repositories to avoid hitting rate limits
        time.sleep(5)
    
    return all_prs

def save_to_csv(data, filename):
    """Save the collected data to a CSV file"""
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def load_from_csv(filename):
    """Load data from a CSV file"""
    return pd.read_csv(filename)

def analyze_pr_status_vs_size(df):
    """RQ01: Analyze relationship between PR size and final review feedback"""
    # Convert PR state to binary outcome (MERGED=1, CLOSED=0)
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    
    # Correlation analysis with changed files
    corr_files, p_value_files = stats.spearmanr(df['changedFiles'], df['merged'])
    
    # Correlation analysis with total changes (additions + deletions)
    df['total_changes'] = df['additions'] + df['deletions']
    corr_changes, p_value_changes = stats.spearmanr(df['total_changes'], df['merged'])
    
    return {
        'files_correlation': corr_files,
        'files_p_value': p_value_files,
        'changes_correlation': corr_changes,
        'changes_p_value': p_value_changes
    }

def analyze_pr_status_vs_duration(df):
    """RQ02: Analyze relationship between PR analysis duration and final review feedback"""
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    corr, p_value = stats.spearmanr(df['duration_hours'], df['merged'])
    
    return {
        'correlation': corr,
        'p_value': p_value
    }

def analyze_pr_status_vs_description(df):
    """RQ03: Analyze relationship between PR description length and final review feedback"""
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    df['description_length'] = df['bodyText'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
    corr, p_value = stats.spearmanr(df['description_length'], df['merged'])
    
    return {
        'correlation': corr,
        'p_value': p_value
    }

def analyze_pr_status_vs_interactions(df):
    """RQ04: Analyze relationship between interactions in PRs and final review feedback"""
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    
    # Rename columns if needed for compatibility with older data format
    if 'participants.totalCount' in df.columns:
        participants_col = 'participants.totalCount'
        comments_col = 'comments.totalCount'
    else:
        df['participants.totalCount'] = df['participants'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        df['comments.totalCount'] = df['comments'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        participants_col = 'participants.totalCount'
        comments_col = 'comments.totalCount'
    
    # Correlation with number of participants
    corr_participants, p_value_participants = stats.spearmanr(df[participants_col], df['merged'])
    
    # Correlation with number of comments
    corr_comments, p_value_comments = stats.spearmanr(df[comments_col], df['merged'])
    
    return {
        'participants_correlation': corr_participants,
        'participants_p_value': p_value_participants,
        'comments_correlation': corr_comments,
        'comments_p_value': p_value_comments
    }

def analyze_reviews_vs_size(df):
    """RQ05: Analyze relationship between PR size and the number of reviews"""
    # Rename columns if needed for compatibility with older data format
    if 'reviews.totalCount' in df.columns:
        reviews_col = 'reviews.totalCount'
    else:
        df['reviews.totalCount'] = df['reviews'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        reviews_col = 'reviews.totalCount'
    
    # Correlation analysis with changed files
    corr_files, p_value_files = stats.spearmanr(df['changedFiles'], df[reviews_col])
    
    # Correlation analysis with total changes (additions + deletions)
    df['total_changes'] = df['additions'] + df['deletions']
    corr_changes, p_value_changes = stats.spearmanr(df['total_changes'], df[reviews_col])
    
    return {
        'files_correlation': corr_files,
        'files_p_value': p_value_files,
        'changes_correlation': corr_changes,
        'changes_p_value': p_value_changes
    }

def analyze_reviews_vs_duration(df):
    """RQ06: Analyze relationship between PR analysis duration and the number of reviews"""
    # Rename columns if needed for compatibility with older data format
    if 'reviews.totalCount' in df.columns:
        reviews_col = 'reviews.totalCount'
    else:
        df['reviews.totalCount'] = df['reviews'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        reviews_col = 'reviews.totalCount'
        
    corr, p_value = stats.spearmanr(df['duration_hours'], df[reviews_col])
    
    return {
        'correlation': corr,
        'p_value': p_value
    }

def analyze_reviews_vs_description(df):
    """RQ07: Analyze relationship between PR description length and the number of reviews"""
    # Rename columns if needed for compatibility with older data format
    if 'reviews.totalCount' in df.columns:
        reviews_col = 'reviews.totalCount'
    else:
        df['reviews.totalCount'] = df['reviews'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        reviews_col = 'reviews.totalCount'
        
    df['description_length'] = df['bodyText'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
    corr, p_value = stats.spearmanr(df['description_length'], df[reviews_col])
    
    return {
        'correlation': corr,
        'p_value': p_value
    }

def analyze_reviews_vs_interactions(df):
    """RQ08: Analyze relationship between interactions in PRs and the number of reviews"""
    # Rename columns if needed for compatibility with older data format
    if 'reviews.totalCount' in df.columns:
        reviews_col = 'reviews.totalCount'
        participants_col = 'participants.totalCount'
        comments_col = 'comments.totalCount'
    else:
        df['reviews.totalCount'] = df['reviews'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        df['participants.totalCount'] = df['participants'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        df['comments.totalCount'] = df['comments'].apply(
            lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
        )
        reviews_col = 'reviews.totalCount'
        participants_col = 'participants.totalCount'
        comments_col = 'comments.totalCount'
    
    # Correlation with number of participants
    corr_participants, p_value_participants = stats.spearmanr(df[participants_col], df[reviews_col])
    
    # Correlation with number of comments
    corr_comments, p_value_comments = stats.spearmanr(df[comments_col], df[reviews_col])
    
    return {
        'participants_correlation': corr_participants,
        'participants_p_value': p_value_participants,
        'comments_correlation': corr_comments,
        'comments_p_value': p_value_comments
    }

def plot_results(results, title, x_label, y_label, filename):
    """Generate a plot for the analysis results"""
    plt.figure(figsize=(10, 6))
    
    # Check if results is a list or a single value
    if isinstance(results, list):
        bars = plt.bar(range(len(results)), results)
        plt.xticks(range(len(results)), x_label)
    else:
        bars = plt.bar([0], [results])
        plt.xticks([0], [x_label])
    
    plt.ylabel(y_label)
    plt.title(title)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{height:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(filename)
    plt.close() 