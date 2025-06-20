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
import concurrent.futures
import ast


load_dotenv()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def execute_query(query, variables, max_retries=5, retry_delay=10, timeout=30):
    
    retries = 0
    
    while retries < max_retries:
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 403:
                reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                current_time = int(time.time())
                sleep_time = max(reset_time - current_time + 5, 60)
                
                print(f"API rate limit exceeded. Waiting for {sleep_time} seconds...")
                time.sleep(sleep_time)
                retries += 1
                continue
                
            elif 500 <= response.status_code < 600:
                sleep_time = retry_delay * (2 ** retries) 
                print(f"Server error {response.status_code}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                retries += 1
                continue
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Query failed: {e}")
            
            if retries >= max_retries - 1:
                print(f"Max retries ({max_retries}) exceeded. Giving up on this query.")
                return None
                
            retries += 1
            sleep_time = retry_delay * (2 ** retries)
            print(f"Retrying in {sleep_time} seconds... (Attempt {retries+1}/{max_retries})")
            time.sleep(sleep_time)
    
    return None

def fetch_top_repositories(first=100, cursor=None, timeout=30):
    from query import query_repositories
    variables = {
        "first": first,
        "cursor": cursor
    }
    return execute_query(query_repositories, variables, timeout=timeout)

def fetch_repository_pr_count(owner, name, timeout=30):
    from query import query_repository_pr_count
    variables = {
        "owner": owner,
        "name": name
    }
    result = execute_query(query_repository_pr_count, variables, timeout=timeout)
    return owner, name, result

def fetch_pull_requests(owner, name, first=100, cursor=None, timeout=30):
    from query import query_pull_requests
    variables = {
        "owner": owner,
        "name": name,
        "first": first,
        "cursor": cursor
    }
    return execute_query(query_pull_requests, variables, timeout=timeout)

def fetch_pull_request_details(owner, name, pr_number, timeout=30):
    from query import query_pull_request_details
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_details, variables, timeout=timeout)

def fetch_pull_request_review_count(owner, name, pr_number, timeout=30):
    
    from query import query_pull_request_review_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_review_count, variables, timeout=timeout)

def fetch_pull_request_comments_count(owner, name, pr_number, timeout=30):
    
    from query import query_pull_request_comments_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_comments_count, variables, timeout=timeout)

def fetch_pull_request_participants_count(owner, name, pr_number, timeout=30):
    
    from query import query_pull_request_participants_count
    variables = {
        "owner": owner,
        "name": name,
        "number": pr_number
    }
    return execute_query(query_pull_request_participants_count, variables, timeout=timeout)

def gather_repository_data(limit=200, timeout=30):
    
    cursor = None
    potential_repos = []

    print("Fetching potential repositories...")
    
    while len(potential_repos) < limit * 5 and len(potential_repos) < 1000: 
        batch_size = min(100, 1000 - len(potential_repos)) 
        result = fetch_top_repositories(batch_size, cursor, timeout=timeout)

        if not result or "data" not in result or "search" not in result["data"]:
            print("Failed to fetch repositories batch or received invalid response")
            if result:
                print(f"Response: {json.dumps(result, indent=2)}")
            time.sleep(30)
            continue

        page_info = result["data"]["search"]["pageInfo"]
        cursor = page_info["endCursor"]
        repo_nodes = result["data"]["search"]["nodes"]

        potential_repos.extend(r for r in repo_nodes if r and "owner" in r and r["owner"] and "login" in r["owner"])

        print(f"Gathered {len(potential_repos)} potential repositories...")

        if not page_info["hasNextPage"]:
            break
        time.sleep(2) 

    if not potential_repos:
        print("No potential repositories found.")
        return []

    print(f"Checking PR counts for {len(potential_repos)} potential repositories concurrently...")

    repositories = []
    tasks = []
    max_workers = 10 

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        for repo in potential_repos:
             try:
                owner = repo["owner"]["login"]
                name = repo["name"]
                tasks.append(executor.submit(fetch_repository_pr_count, owner, name, timeout))
             except (KeyError, TypeError) as e:
                 print(f"Skipping repo due to missing data: {e}")
                 continue


        progress_bar = tqdm(total=limit, desc="Filtering repositories by PR count")
        processed_count = 0

        for future in concurrent.futures.as_completed(tasks):
            if len(repositories) >= limit:
                
                for task in tasks:
                    if not task.done():
                        task.cancel()
                break 

            try:
                owner, name, pr_count_result = future.result()
                processed_count += 1

                if not pr_count_result or "data" not in pr_count_result or not pr_count_result["data"]["repository"]:
                    
                    continue

                pr_count = pr_count_result["data"]["repository"]["pullRequests"]["totalCount"]

                if pr_count >= 100:
                    
                    original_repo = next((r for r in potential_repos if r["owner"]["login"] == owner and r["name"] == name), None)
                    if original_repo:
                        original_repo["pullRequests"] = {"totalCount": pr_count}
                        repositories.append(original_repo)
                        
                        progress_bar.update(1)

                        
                        if len(repositories) % 10 == 0:
                           try:
                               temp_df = pd.DataFrame(repositories)
                               temp_df.to_csv(f'Projects/S3/data/repositories_temp_{len(repositories)}.csv', index=False)
                               
                           except Exception as save_e:
                               print(f"Error saving temporary repository file: {save_e}")

            except concurrent.futures.CancelledError:
                 
                 pass
            except Exception as exc:
                print(f'Repository check generated an exception: {exc}')

            
            progress_bar.set_description(f"Filtered {len(repositories)}/{limit} repos (checked {processed_count}/{len(tasks)})")


    progress_bar.close()

    if not repositories:
        print("Warning: No repositories matched the criteria after checking PR counts.")

    
    executor.shutdown(wait=False) 

    
    final_repositories = repositories[:limit]
    print(f"Selected {len(final_repositories)} repositories matching criteria.")
    return final_repositories


def _process_single_repository(repo, repo_index, total_repos, max_prs_per_repo, timeout):
    
    owner = repo["owner"]["login"]
    name = repo["name"]
    repo_prs = []
    cursor = None
    repo_pr_count = 0
    processed_api_calls = 0 

    
    
    pbar_repo = tqdm(total=max_prs_per_repo, desc=f"Repo {repo_index+1}/{total_repos} ({owner}/{name})", leave=False, position=repo_index % 10) 

    try:
        while repo_pr_count < max_prs_per_repo:
            batch_size = min(10, max_prs_per_repo - repo_pr_count)
            result = fetch_pull_requests(owner, name, batch_size, cursor, timeout=timeout)
            processed_api_calls += 1

            if not result or "data" not in result or "repository" not in result["data"]:
                pbar_repo.set_description(f"Repo {repo_index+1}/{total_repos} ({owner}/{name}) - Fetch Error")
                break

            if result["data"]["repository"] is None:
                 pbar_repo.set_description(f"Repo {repo_index+1}/{total_repos} ({owner}/{name}) - Not Found")
                 break

            pr_data = result["data"]["repository"]["pullRequests"]
            page_info = pr_data["pageInfo"]
            cursor = page_info["endCursor"]

            if not pr_data["nodes"]:
                pbar_repo.set_description(f"Repo {repo_index+1}/{total_repos} ({owner}/{name}) - No More PRs")
                break

            for pr in pr_data["nodes"]:
                if not pr:
                    continue

                try:
                    created_at = datetime.fromisoformat(pr["createdAt"].replace('Z', '+00:00'))
                    if pr["state"] == "MERGED" and pr.get("mergedAt"):
                        end_time = datetime.fromisoformat(pr["mergedAt"].replace('Z', '+00:00'))
                    elif pr.get("closedAt"):
                        end_time = datetime.fromisoformat(pr["closedAt"].replace('Z', '+00:00'))
                    else:
                        continue

                    duration_hours = (end_time - created_at).total_seconds() / 3600

                    if duration_hours > 1:
                        pr_number = pr["number"]

                        
                        time.sleep(0.5)
                        review_result = fetch_pull_request_review_count(owner, name, pr_number, timeout=timeout)
                        processed_api_calls += 1
                        if not review_result or "data" not in review_result or not review_result["data"]["repository"] or not review_result["data"]["repository"]["pullRequest"]:
                            continue

                        reviews_count = review_result["data"]["repository"]["pullRequest"]["reviews"]["totalCount"]

                        if reviews_count >= 1:
                            time.sleep(0.5)
                            details_result = fetch_pull_request_details(owner, name, pr_number, timeout=timeout)
                            processed_api_calls += 1
                            if not details_result or "data" not in details_result or not details_result["data"]["repository"] or not details_result["data"]["repository"]["pullRequest"]:
                                continue
                            pr_details = details_result["data"]["repository"]["pullRequest"]
                            for key, value in pr_details.items():
                                pr[key] = value

                            time.sleep(0.5)
                            comments_result = fetch_pull_request_comments_count(owner, name, pr_number, timeout=timeout)
                            processed_api_calls += 1
                            if comments_result and "data" in comments_result and comments_result["data"]["repository"] and comments_result["data"]["repository"]["pullRequest"]:
                                comments_count = comments_result["data"]["repository"]["pullRequest"]["comments"]["totalCount"]
                                pr["comments"] = {"totalCount": comments_count}

                            time.sleep(0.5)
                            participants_result = fetch_pull_request_participants_count(owner, name, pr_number, timeout=timeout)
                            processed_api_calls += 1
                            if participants_result and "data" in participants_result and participants_result["data"]["repository"] and participants_result["data"]["repository"]["pullRequest"]:
                                participants_count = participants_result["data"]["repository"]["pullRequest"]["participants"]["totalCount"]
                                pr["participants"] = {"totalCount": participants_count}

                            pr["reviews"] = {"totalCount": reviews_count}
                            pr["repository"] = {"owner": owner, "name": name}
                            pr["duration_hours"] = duration_hours

                            repo_prs.append(pr)
                            repo_pr_count += 1
                            pbar_repo.update(1) 

                            if repo_pr_count >= max_prs_per_repo:
                                break 

                except (ValueError, KeyError, TypeError) as e:
                    
                    continue

            if not page_info["hasNextPage"] or repo_pr_count >= max_prs_per_repo:
                 break

            time.sleep(1) 

        pbar_repo.set_description(f"Repo {repo_index+1}/{total_repos} ({owner}/{name}) - Done ({len(repo_prs)} PRs)")
        pbar_repo.close()
        
        return repo_prs

    except Exception as e:
         pbar_repo.set_description(f"Repo {repo_index+1}/{total_repos} ({owner}/{name}) - Error: {e}")
         pbar_repo.close()
         print(f"Unhandled error processing repository {owner}/{name}: {e}")
         return [] 


def gather_pull_requests(repositories, timeout=30):
    
    all_prs = []
    max_prs_per_repo = 50
    max_workers = 5 

    print(f"Processing {len(repositories)} repositories concurrently (max workers: {max_workers})...")

    
    os.makedirs('Projects/S3/data', exist_ok=True)

    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        futures = {executor.submit(_process_single_repository, repo, i, len(repositories), max_prs_per_repo, timeout): repo
                   for i, repo in enumerate(repositories)}

        
        
        progress_bar = tqdm(concurrent.futures.as_completed(futures), total=len(repositories), desc="Overall PR Fetch Progress")

        for future in progress_bar:
            repo = futures[future]
            owner = repo["owner"]["login"]
            name = repo["name"]
            try:
                repo_prs = future.result()
                if repo_prs:
                    all_prs.extend(repo_prs)
                    progress_bar.set_description(f"Overall Progress ({len(all_prs)} PRs total)")

                    
                    if len(all_prs) > 0 and len(all_prs) % 50 == 0: 
                         try:
                            temp_df = pd.DataFrame(all_prs)
                            
                            temp_filename = f'Projects/S3/data/pull_requests_temp_{len(all_prs)}.csv'
                            temp_df.to_csv(temp_filename, index=False)
                            
                         except Exception as save_e:
                            print(f"Error saving temporary PR file: {save_e}")

            except Exception as exc:
                print(f'Repository {owner}/{name} generated an exception during PR fetch: {exc}')

    print(f"Finished processing all repositories. Total PRs gathered: {len(all_prs)}")

    
    if all_prs:
        try:
            final_df = pd.DataFrame(all_prs)
            final_filename = 'Projects/S3/data/pull_requests.csv'
            final_df.to_csv(final_filename, index=False)
            print(f"Final combined data saved to {final_filename}")
        except Exception as final_save_e:
            print(f"Error saving final combined PR file: {final_save_e}")


    return all_prs

def save_to_csv(data, filename):
    
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def safe_json_loads(s):
    try:
        
        return json.loads(s.replace("'", '"')) 
    except (json.JSONDecodeError, AttributeError):
        try:
            
            return ast.literal_eval(s)
        except (ValueError, SyntaxError, TypeError):
            
            return s

def load_from_csv(filename):
    
    
    potential_dict_cols = ['repository', 'reviews', 'comments', 'participants']

    
    try:
        header = pd.read_csv(filename, nrows=0).columns.tolist()
    except pd.errors.EmptyDataError:
         print(f"Warning: CSV file '{filename}' is empty.")
         return pd.DataFrame() 
    except FileNotFoundError:
         print(f"Error: CSV file '{filename}' not found.")
         return pd.DataFrame() 


    
    cols_to_convert = {col: safe_json_loads for col in potential_dict_cols if col in header}

    try:
        
        return pd.read_csv(filename, converters=cols_to_convert)
    except Exception as e:
        print(f"Error loading or converting CSV '{filename}': {e}")
        print("Attempting to load without converters...")
        
        return pd.read_csv(filename)

def analyze_pr_status_vs_size(df):
    
    
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)

    
    df_cleaned = df.dropna(subset=['changedFiles', 'merged'])
    if df_cleaned.empty:
        print("Warning RQ01: No valid data after dropping NaNs for files vs status.")
        corr_files, p_value_files = np.nan, np.nan
    else:
        corr_files, p_value_files = stats.spearmanr(df_cleaned['changedFiles'], df_cleaned['merged'], nan_policy='omit')

    
    df['total_changes'] = df['additions'] + df['deletions']
    df_cleaned = df.dropna(subset=['total_changes', 'merged'])
    if df_cleaned.empty:
        print("Warning RQ01: No valid data after dropping NaNs for changes vs status.")
        corr_changes, p_value_changes = np.nan, np.nan
    else:
        corr_changes, p_value_changes = stats.spearmanr(df_cleaned['total_changes'], df_cleaned['merged'], nan_policy='omit')

    return {
        'files_correlation': corr_files if not np.isnan(corr_files) else 0, 
        'files_p_value': p_value_files if not np.isnan(p_value_files) else 1, 
        'changes_correlation': corr_changes if not np.isnan(corr_changes) else 0,
        'changes_p_value': p_value_changes if not np.isnan(p_value_changes) else 1
    }

def analyze_pr_status_vs_duration(df):
    
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    
    df_cleaned = df.dropna(subset=['duration_hours', 'merged'])
    if df_cleaned.empty:
        print("Warning RQ02: No valid data after dropping NaNs for duration vs status.")
        corr, p_value = np.nan, np.nan
    else:
        corr, p_value = stats.spearmanr(df_cleaned['duration_hours'], df_cleaned['merged'], nan_policy='omit')

    return {
        'correlation': corr if not np.isnan(corr) else 0,
        'p_value': p_value if not np.isnan(p_value) else 1
    }

def analyze_pr_status_vs_description(df):
    
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)
    
    df['description_length'] = df['bodyText'].fillna('').astype(str).apply(len)
    
    df_cleaned = df.dropna(subset=['description_length', 'merged'])
    if df_cleaned.empty:
         print("Warning RQ03: No valid data after dropping NaNs for description vs status.")
         corr, p_value = np.nan, np.nan
    else:
        corr, p_value = stats.spearmanr(df_cleaned['description_length'], df_cleaned['merged'], nan_policy='omit')

    return {
        'correlation': corr if not np.isnan(corr) else 0,
        'p_value': p_value if not np.isnan(p_value) else 1
    }


def analyze_pr_status_vs_interactions(df):
    
    df['merged'] = df['state'].apply(lambda x: 1 if x == 'MERGED' else 0)

    
    df['participants_count'] = df['participants'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    df['comments_count'] = df['comments'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )

    participants_col = 'participants_count'
    comments_col = 'comments_count'

    
    df_cleaned_p = df.dropna(subset=[participants_col, 'merged'])
    if df_cleaned_p.empty:
        print("Warning RQ04: No valid data after dropping NaNs for participants vs status.")
        corr_participants, p_value_participants = np.nan, np.nan
    else:
        corr_participants, p_value_participants = stats.spearmanr(df_cleaned_p[participants_col], df_cleaned_p['merged'], nan_policy='omit')

    
    df_cleaned_c = df.dropna(subset=[comments_col, 'merged'])
    if df_cleaned_c.empty:
         print("Warning RQ04: No valid data after dropping NaNs for comments vs status.")
         corr_comments, p_value_comments = np.nan, np.nan
    else:
        corr_comments, p_value_comments = stats.spearmanr(df_cleaned_c[comments_col], df_cleaned_c['merged'], nan_policy='omit')

    return {
        'participants_correlation': corr_participants if not np.isnan(corr_participants) else 0,
        'participants_p_value': p_value_participants if not np.isnan(p_value_participants) else 1,
        'comments_correlation': corr_comments if not np.isnan(corr_comments) else 0,
        'comments_p_value': p_value_comments if not np.isnan(p_value_comments) else 1
    }

def analyze_reviews_vs_size(df):
    
    
    df['reviews_count'] = df['reviews'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    reviews_col = 'reviews_count'

    
    df_cleaned_f = df.dropna(subset=['changedFiles', reviews_col])
    if df_cleaned_f.empty:
        print("Warning RQ05: No valid data after dropping NaNs for files vs reviews.")
        corr_files, p_value_files = np.nan, np.nan
    else:
        corr_files, p_value_files = stats.spearmanr(df_cleaned_f['changedFiles'], df_cleaned_f[reviews_col], nan_policy='omit')

    
    df['total_changes'] = df['additions'] + df['deletions']
    df_cleaned_c = df.dropna(subset=['total_changes', reviews_col])
    if df_cleaned_c.empty:
        print("Warning RQ05: No valid data after dropping NaNs for changes vs reviews.")
        corr_changes, p_value_changes = np.nan, np.nan
    else:
        corr_changes, p_value_changes = stats.spearmanr(df_cleaned_c['total_changes'], df_cleaned_c[reviews_col], nan_policy='omit')

    return {
        'files_correlation': corr_files if not np.isnan(corr_files) else 0,
        'files_p_value': p_value_files if not np.isnan(p_value_files) else 1,
        'changes_correlation': corr_changes if not np.isnan(corr_changes) else 0,
        'changes_p_value': p_value_changes if not np.isnan(p_value_changes) else 1
    }

def analyze_reviews_vs_duration(df):
    
    
    df['reviews_count'] = df['reviews'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    reviews_col = 'reviews_count'

    df_cleaned = df.dropna(subset=['duration_hours', reviews_col])
    if df_cleaned.empty:
        print("Warning RQ06: No valid data after dropping NaNs for duration vs reviews.")
        corr, p_value = np.nan, np.nan
    else:
        corr, p_value = stats.spearmanr(df_cleaned['duration_hours'], df_cleaned[reviews_col], nan_policy='omit')

    return {
        'correlation': corr if not np.isnan(corr) else 0,
        'p_value': p_value if not np.isnan(p_value) else 1
    }

def analyze_reviews_vs_description(df):
    
    
    df['reviews_count'] = df['reviews'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    reviews_col = 'reviews_count'

    
    df['description_length'] = df['bodyText'].fillna('').astype(str).apply(len)
    df_cleaned = df.dropna(subset=['description_length', reviews_col])
    if df_cleaned.empty:
         print("Warning RQ07: No valid data after dropping NaNs for description vs reviews.")
         corr, p_value = np.nan, np.nan
    else:
        corr, p_value = stats.spearmanr(df_cleaned['description_length'], df_cleaned[reviews_col], nan_policy='omit')

    return {
        'correlation': corr if not np.isnan(corr) else 0,
        'p_value': p_value if not np.isnan(p_value) else 1
    }

def analyze_reviews_vs_interactions(df):
    
    
    df['reviews_count'] = df['reviews'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    df['participants_count'] = df['participants'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )
    df['comments_count'] = df['comments'].apply(
        lambda x: x.get('totalCount', 0) if isinstance(x, dict) else 0
    )

    reviews_col = 'reviews_count'
    participants_col = 'participants_count'
    comments_col = 'comments_count'

    
    df_cleaned_p = df.dropna(subset=[participants_col, reviews_col])
    if df_cleaned_p.empty:
        print("Warning RQ08: No valid data after dropping NaNs for participants vs reviews.")
        corr_participants, p_value_participants = np.nan, np.nan
    else:
        corr_participants, p_value_participants = stats.spearmanr(df_cleaned_p[participants_col], df_cleaned_p[reviews_col], nan_policy='omit')

    
    df_cleaned_c = df.dropna(subset=[comments_col, reviews_col])
    if df_cleaned_c.empty:
         print("Warning RQ08: No valid data after dropping NaNs for comments vs reviews.")
         corr_comments, p_value_comments = np.nan, np.nan
    else:
        corr_comments, p_value_comments = stats.spearmanr(df_cleaned_c[comments_col], df_cleaned_c[reviews_col], nan_policy='omit')


    return {
        'participants_correlation': corr_participants if not np.isnan(corr_participants) else 0,
        'participants_p_value': p_value_participants if not np.isnan(p_value_participants) else 1,
        'comments_correlation': corr_comments if not np.isnan(corr_comments) else 0,
        'comments_p_value': p_value_comments if not np.isnan(p_value_comments) else 1
    }


def plot_results(results, title, x_label, y_label, filename):
    
    plt.figure(figsize=(10, 6))

    
    try:
        if isinstance(results, list):
            
            numeric_results = [float(r) if pd.notna(r) else 0 for r in results]
            bars = plt.bar(range(len(numeric_results)), numeric_results)
            plt.xticks(range(len(numeric_results)), x_label) 
        else:
            
            numeric_result = float(results) if pd.notna(results) else 0
            bars = plt.bar([0], [numeric_result])
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
        
    except Exception as e:
        print(f"Error generating plot '{title}': {e}")
        plt.close() 