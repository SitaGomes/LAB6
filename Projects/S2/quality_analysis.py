import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np
import os

def load_data():
    """Load and prepare the data from both CSV files"""
    # Load repository data
    repo_data = pd.read_csv('./repository_data.csv')
    
    # Extract repository name from repo_data
    repo_data['repo_name'] = repo_data['name'].str.lower()
    
    # Load class metrics data
    class_data = pd.read_csv('./class.csv')
    
    # Extract repository name from file path in class_data
    class_data['repo_name'] = class_data['file'].apply(lambda x: x.split('/')[-4] if len(x.split('/')) > 3 else None)
    
    # Calculate average metrics per repository
    metrics = ['cbo', 'wmc', 'dit', 'rfc', 'lcom', 'totalMethodsQty', 
              'totalFieldsQty', 'loc', 'returnQty', 'variablesQty']
    
    class_metrics = class_data.groupby('repo_name')[metrics].mean().reset_index()
    
    # Merge repository data with class metrics
    combined_data = pd.merge(class_metrics, repo_data, on='repo_name', how='inner')
    
    # Convert stargazers from dict to int
    combined_data['stars'] = combined_data['stargazers'].str.extract(r"'totalCount': (\d+)").astype(float)
    
    return combined_data

def analyze_popularity_vs_quality(data):
    """RQ 01: Relationship between repository popularity and quality metrics"""
    metrics = ['cbo', 'wmc', 'rfc', 'lcom', 'loc']
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Repository Popularity vs Quality Metrics')
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics):
        sns.scatterplot(data=data, 
                       x='stars', 
                       y=metric,
                       ax=axes[i])
        axes[i].set_xlabel('Stars')
        axes[i].set_ylabel(metric.upper())
        
        # Calculate correlation
        correlation = stats.spearmanr(data['stars'], data[metric])
        axes[i].set_title(f'Correlation: {correlation.correlation:.2f}')
    
    plt.tight_layout()
    plt.savefig('./popularity_vs_quality.png')
    plt.close()

def analyze_maturity_vs_quality(data):
    """RQ 02: Relationship between repository maturity and quality metrics"""
    # Calculate repository age
    current_time = pd.Timestamp.now(tz='UTC')
    data['createdAt'] = pd.to_datetime(data['createdAt'])  # Convert to datetime
    
    # Convert to UTC if not already
    if data['createdAt'].dt.tz is None:
        data['createdAt'] = data['createdAt'].dt.tz_localize('UTC')
    else:
        data['createdAt'] = data['createdAt'].dt.tz_convert('UTC')
    
    data['age'] = current_time - data['createdAt']
    data['age_years'] = data['age'].dt.total_seconds() / (365.25 * 24 * 60 * 60)
    
    metrics = ['cbo', 'wmc', 'rfc', 'lcom', 'loc']
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Repository Maturity vs Quality Metrics')
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics):
        sns.scatterplot(data=data, 
                       x='age_years', 
                       y=metric,
                       ax=axes[i])
        axes[i].set_xlabel('Age (years)')
        axes[i].set_ylabel(metric.upper())
        
        correlation = stats.spearmanr(data['age_years'], data[metric])
        axes[i].set_title(f'Correlation: {correlation.correlation:.2f}')
    
    plt.tight_layout()
    plt.savefig('./maturity_vs_quality.png')
    plt.close()

def analyze_activity_vs_quality(data):
    """RQ 03: Relationship between repository activity and quality metrics"""
    # Extract numeric values from dictionary strings
    data['prs'] = data['pullRequests'].str.extract(r"'totalCount': (\d+)").astype(float)
    data['issues'] = data['allIssues'].str.extract(r"'totalCount': (\d+)").astype(float)
    data['release_count'] = data['releases'].str.extract(r"'totalCount': (\d+)").astype(float)
    
    # Calculate activity score
    data['activity_score'] = (data['prs'] + data['issues'] + data['release_count']) / data['age_years']
    
    metrics = ['cbo', 'wmc', 'rfc', 'lcom', 'loc']
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Repository Activity vs Quality Metrics')
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics):
        sns.scatterplot(data=data, 
                       x='activity_score', 
                       y=metric,
                       ax=axes[i])
        axes[i].set_xlabel('Activity Score')
        axes[i].set_ylabel(metric.upper())
        
        correlation = stats.spearmanr(data['activity_score'], data[metric])
        axes[i].set_title(f'Correlation: {correlation.correlation:.2f}')
    
    plt.tight_layout()
    plt.savefig('./activity_vs_quality.png')
    plt.close()

def analyze_size_vs_quality(data):
    """RQ 04: Relationship between repository size and quality metrics"""
    metrics = ['cbo', 'wmc', 'rfc', 'lcom']
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Repository Size (LOC) vs Other Quality Metrics')
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics):
        sns.scatterplot(data=data, 
                       x='loc', 
                       y=metric,
                       ax=axes[i])
        axes[i].set_xlabel('Lines of Code')
        axes[i].set_ylabel(metric.upper())
        
        correlation = stats.spearmanr(data['loc'], data[metric])
        axes[i].set_title(f'Correlation: {correlation.correlation:.2f}')
    
    plt.tight_layout()
    plt.savefig('./size_vs_quality.png')
    plt.close()

def generate_summary_report(data):
    """Generate a summary report with key findings"""
    metrics = ['cbo', 'wmc', 'rfc', 'lcom', 'loc']
    
    with open('./analysis_report.txt', 'w') as f:
        f.write("Quality Analysis Report\n")
        f.write("======================\n\n")
        
        # Popularity correlations
        f.write("RQ 01: Repository Popularity vs Quality Metrics\n")
        f.write("--------------------------------------------\n")
        for metric in metrics:
            corr = stats.spearmanr(data['stars'], data[metric])
            f.write(f"{metric.upper()}: Correlation = {corr.correlation:.3f}, p-value = {corr.pvalue:.3f}\n")
        f.write("\n")
        
        # Maturity correlations
        f.write("RQ 02: Repository Maturity vs Quality Metrics\n")
        f.write("--------------------------------------------\n")
        for metric in metrics:
            corr = stats.spearmanr(data['age_years'], data[metric])
            f.write(f"{metric.upper()}: Correlation = {corr.correlation:.3f}, p-value = {corr.pvalue:.3f}\n")
        f.write("\n")
        
        # Activity correlations
        f.write("RQ 03: Repository Activity vs Quality Metrics\n")
        f.write("--------------------------------------------\n")
        for metric in metrics:
            corr = stats.spearmanr(data['activity_score'], data[metric])
            f.write(f"{metric.upper()}: Correlation = {corr.correlation:.3f}, p-value = {corr.pvalue:.3f}\n")
        f.write("\n")
        
        # Size correlations
        f.write("RQ 04: Repository Size vs Quality Metrics\n")
        f.write("----------------------------------------\n")
        for metric in metrics:
            if metric != 'loc':
                corr = stats.spearmanr(data['loc'], data[metric])
                f.write(f"{metric.upper()}: Correlation = {corr.correlation:.3f}, p-value = {corr.pvalue:.3f}\n")

def main():
    # Load and combine data
    combined_data = load_data()
    
    # Run analyses
    analyze_popularity_vs_quality(combined_data)
    analyze_maturity_vs_quality(combined_data)
    analyze_activity_vs_quality(combined_data)
    analyze_size_vs_quality(combined_data)
    
    # Generate summary report
    generate_summary_report(combined_data)
    
    print("Analysis complete. Check the generated plots and analysis_report.txt for results.")

if __name__ == "__main__":
    main() 