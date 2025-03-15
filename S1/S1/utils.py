import requests
import os
from querys import querys
from dotenv import load_dotenv
import csv
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import ast

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

def save_to_csv(data, filename):
    with open(filename,
              mode='w',
              newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data[0].keys())
        for item in data:
            writer.writerow(item.values())
    print(f"Data saved to {filename}")

def load_data(csv_file):
    df = pd.read_csv(csv_file)

    def parse_dict(val):
        try:
            if pd.isna(val):
                return None
            return ast.literal_eval(val)
        except Exception:
            return None

    json_columns = ['owner', 'stargazers', 'pullRequests', 'allIssues', 'closedIssues', 'primaryLanguage', 'releases']
    for col in json_columns:
        df[col] = df[col].apply(parse_dict)
        
    df['stargazers_count'] = df['stargazers'].apply(lambda d: d.get('totalCount') if d else None)
    df['pull_requests']    = df['pullRequests'].apply(lambda d: d.get('totalCount') if d else None)
    df['all_issues_count'] = df['allIssues'].apply(lambda d: d.get('totalCount') if d else None)
    df['closed_issues_count'] = df['closedIssues'].apply(lambda d: d.get('totalCount') if d else None)
    df['release_count']    = df['releases'].apply(lambda d: d.get('totalCount') if d else None)
    
    df['language'] = df['primaryLanguage'].apply(lambda d: d.get('name') if d else "Unknown")
    
    df['createdAt'] = pd.to_datetime(df['createdAt'], utc=True)
    df['updatedAt'] = pd.to_datetime(df['updatedAt'], utc=True)
    
    return df

def get_repository_age(df):
    now = pd.Timestamp(datetime.datetime.utcnow(), tz='UTC')
    df['age_days'] = (now - df['createdAt']).dt.days
    df['age_years'] = df['age_days'] / 365
    return df[['name', 'age_days', 'age_years']]

def plot_repository_age(df):
    age_df = get_repository_age(df)
    plt.figure(figsize=(10, 6))
    plt.bar(age_df['name'], age_df['age_years'], color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Repository")
    plt.ylabel("Age (years)")
    plt.title("RQ 01: Repository Age (years)")
    plt.savefig("repository_age.png")

def get_pull_requests_data(df):
    return df[['name', 'pull_requests']]

def plot_pull_requests(df):
    pr_data = get_pull_requests_data(df)
    plt.figure(figsize=(10, 6))
    plt.bar(pr_data['name'], pr_data['pull_requests'], color='orange')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Repository")
    plt.ylabel("Total Pull Requests Accepted")
    plt.title("RQ 02: Pull Requests Accepted by Repository")
    plt.savefig("pull_requests.png")



def get_release_data(df):
    return df[['name', 'release_count']]

def plot_releases(df):
    release_data = get_release_data(df)
    plt.figure(figsize=(10, 6))
    plt.bar(release_data['name'], release_data['release_count'], color='purple')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Repository")
    plt.ylabel("Total Releases")
    plt.title("RQ 03: Releases Count by Repository")
    plt.savefig("releases.png")



def get_update_frequency(df):
    now = pd.Timestamp(datetime.datetime.utcnow(), tz='UTC')
    df['days_since_update'] = (now - df['updatedAt']).dt.days
    return df[['name', 'days_since_update']]

def plot_update_frequency(df):
    update_data = get_update_frequency(df)
    plt.figure(figsize=(10, 6))
    plt.bar(update_data['name'], update_data['days_since_update'], color='red')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Repository")
    plt.ylabel("Days Since Last Update")
    plt.title("RQ 04: Days Since Last Update by Repository")
    plt.savefig("update_frequency.png")


def get_primary_language_distribution(df):
    return df['language'].value_counts()

def plot_primary_language_distribution(df):
    lang_counts = get_primary_language_distribution(df)
    plt.figure(figsize=(8,8))
    plt.pie(lang_counts, labels=lang_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title("RQ 05: Primary Language Distribution")
    plt.savefig("language_distribution.png")



def get_issue_closure_ratio(df):
    def calc_ratio(row):
        if row['all_issues_count'] and row['all_issues_count'] > 0:
            return row['closed_issues_count'] / row['all_issues_count']
        else:
            return None
    df['issue_closure_ratio'] = df.apply(calc_ratio, axis=1)
    return df[['name', 'issue_closure_ratio']]


def plot_issue_closure_ratio(df):
    ratio_data = get_issue_closure_ratio(df)
    plt.figure(figsize=(10, 6))
    plt.bar(ratio_data['name'], ratio_data['issue_closure_ratio'] * 100, color='green')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Repository")
    plt.ylabel("Issue Closure Ratio (%)")
    plt.title("RQ 06: Issue Closure Ratio by Repository")
    plt.ylim(0, 110)
    plt.savefig("issue_closure_ratio.png")

