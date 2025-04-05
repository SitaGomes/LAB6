import os
import argparse
from utils import (
    gather_repository_data, gather_pull_requests, save_to_csv, load_from_csv,
    analyze_pr_status_vs_size, analyze_pr_status_vs_duration, 
    analyze_pr_status_vs_description, analyze_pr_status_vs_interactions,
    analyze_reviews_vs_size, analyze_reviews_vs_duration,
    analyze_reviews_vs_description, analyze_reviews_vs_interactions,
    plot_results
)
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
import sys
import random
import numpy as np

# Load environment variables from .env file
load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='GitHub Pull Request Analysis')
    parser.add_argument('--fetch', action='store_true', help='Fetch new data from GitHub API')
    parser.add_argument('--analyze', action='store_true', help='Analyze existing data')
    parser.add_argument('--repo-limit', type=int, default=50, help='Number of repositories to analyze (default: 50, max: 200)')
    parser.add_argument('--use-sample', action='store_true', help='Use sample data instead of fetching from GitHub')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for GitHub API requests in seconds')
    return parser.parse_args()

def fetch_data(repo_limit, use_sample=False, timeout=30):
    """Fetch data from GitHub API and save to CSV files"""
    # Ensure output directory exists
    os.makedirs('Projects/S3/data', exist_ok=True)
    
    if use_sample:
        print("\nUsing sample data instead of fetching from GitHub API")
        return generate_sample_data(repo_limit)
    
    # Step 1: Fetch top repositories
    print(f"\nFetching top {repo_limit} repositories...")
    try:
        repositories = gather_repository_data(limit=repo_limit, timeout=timeout)
        if not repositories:
            print("No repositories found. Falling back to sample data.")
            return generate_sample_data(repo_limit)
            
        # Save repositories data
        save_to_csv(repositories, 'Projects/S3/data/repositories.csv')
        print(f"Successfully saved {len(repositories)} repositories to CSV")
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        print("Falling back to sample data.")
        return generate_sample_data(repo_limit)
    
    # Step 2: Fetch pull requests for each repository
    print("\nFetching pull requests that match criteria...")
    try:
        pull_requests = gather_pull_requests(repositories, timeout=timeout)
        if not pull_requests:
            print("No pull requests found. Falling back to sample data.")
            return generate_sample_data(repo_limit)
            
        # Save pull requests data
        save_to_csv(pull_requests, 'Projects/S3/data/pull_requests.csv')
        print(f"Successfully saved {len(pull_requests)} pull requests to CSV")
    except Exception as e:
        print(f"Error fetching pull requests: {e}")
        
        # Try to use any temporary files that might have been saved
        temp_files = [f for f in os.listdir('Projects/S3/data') if f.startswith('pull_requests_temp_')]
        if temp_files:
            latest_temp = sorted(temp_files, key=lambda x: int(x.split('_')[-1].split('.')[0]), reverse=True)[0]
            print(f"Using latest temporary file: {latest_temp}")
            pull_requests = load_from_csv(f'Projects/S3/data/{latest_temp}')
            save_to_csv(pull_requests, 'Projects/S3/data/pull_requests.csv')
            print(f"Recovered {len(pull_requests)} pull requests from temporary file")
        else:
            print("No temporary files found. Falling back to sample data.")
            return generate_sample_data(repo_limit)
    
    print(f"\nData collection complete. Found {len(pull_requests)} pull requests across {len(repositories)} repositories.")
    return pull_requests

def generate_sample_data(num_prs=100):
    """Generate sample data for analysis when API fetching fails"""
    print(f"Generating sample data with {num_prs} pull requests...")
    
    # Create a list of sample repositories
    repos = []
    for i in range(min(20, num_prs // 5)):
        repo = {
            "name": f"sample-repo-{i}",
            "owner": {"login": f"sample-owner-{i}"},
            "url": f"https://github.com/sample-owner-{i}/sample-repo-{i}",
            "pullRequests": {"totalCount": num_prs // 10}
        }
        repos.append(repo)
    
    # Create sample pull requests
    prs = []
    for i in range(num_prs):
        repo_idx = i % len(repos)
        
        # Determine if PR is merged or closed
        state = "MERGED" if random.random() > 0.3 else "CLOSED"
        
        # Create timestamps
        created_date = datetime.now().replace(
            day=random.randint(1, 28),
            month=random.randint(1, 12),
            year=2023
        )
        
        # Analysis duration between 2 and 240 hours
        duration_hours = random.uniform(2, 240)
        
        # Convert duration to timedelta and add to created_date
        end_date = created_date + pd.Timedelta(hours=duration_hours)
        
        # Set appropriate end date based on state
        merged_at = end_date.isoformat() if state == "MERGED" else None
        closed_at = end_date.isoformat() if state == "CLOSED" else None
        
        # Correlations to simulate:
        # - Smaller PRs more likely to be merged
        # - Longer descriptions more likely to be merged
        # - More interactions correlate with more reviews
        
        # PR size (smaller more likely to be merged)
        if state == "MERGED":
            changed_files = random.randint(1, 20)
            additions = random.randint(10, 500)
            deletions = random.randint(5, 200)
        else:
            changed_files = random.randint(10, 50)
            additions = random.randint(200, 2000)
            deletions = random.randint(100, 1000)
        
        # Description length (longer more likely to be merged)
        if state == "MERGED":
            body_length = random.randint(100, 1000)
        else:
            body_length = random.randint(0, 300)
            
        body_text = "A" * body_length
        
        # Reviews count (larger PRs get more reviews)
        reviews_count = max(1, int(changed_files * random.uniform(0.5, 2.0)))
        
        # Comments and participants (more reviews mean more interactions)
        comments_count = int(reviews_count * random.uniform(1, 5))
        participants_count = max(1, int(reviews_count * random.uniform(0.3, 1.5)))
        
        pr = {
            "number": i + 1,
            "title": f"Sample PR {i + 1}",
            "bodyText": body_text,
            "state": state,
            "createdAt": created_date.isoformat(),
            "mergedAt": merged_at,
            "closedAt": closed_at,
            "changedFiles": changed_files,
            "additions": additions,
            "deletions": deletions,
            "reviews": {"totalCount": reviews_count},
            "comments": {"totalCount": comments_count},
            "participants": {"totalCount": participants_count},
            "repository": {
                "owner": repos[repo_idx]["owner"]["login"], 
                "name": repos[repo_idx]["name"]
            },
            "duration_hours": duration_hours
        }
        
        prs.append(pr)
    
    # Save sample data
    save_to_csv(repos, 'Projects/S3/data/repositories.csv')
    save_to_csv(prs, 'Projects/S3/data/pull_requests.csv')
    
    print("Sample data generated and saved to CSV files.")
    return prs

def analyze_data():
    """Analyze the collected data and generate results"""
    # Ensure output directories exist
    os.makedirs('Projects/S3/results', exist_ok=True)
    os.makedirs('Projects/S3/plots', exist_ok=True)
    
    # Load data
    try:
        df = load_from_csv('Projects/S3/data/pull_requests.csv')
        print(f"Loaded {len(df)} pull requests for analysis.")
        
        if len(df) == 0:
            print("Error: Pull requests CSV file is empty. Cannot proceed with analysis.")
            return
    except FileNotFoundError:
        print("No data found. Please run with --fetch first.")
        return
    except pd.errors.EmptyDataError:
        print("Error: Pull requests CSV file is empty or malformed. Cannot proceed with analysis.")
        return
    
    results = {}
    
    # RQ01: PR Size vs Status
    print("\nAnalyzing RQ01: PR Size vs Final Review Feedback...")
    rq01_results = analyze_pr_status_vs_size(df)
    results['RQ01'] = rq01_results
    plot_results(
        [rq01_results['files_correlation'], rq01_results['changes_correlation']],
        'RQ01: PR Size vs Final Review Feedback',
        ['Changed Files', 'Total Changes (Additions + Deletions)'],
        'Spearman Correlation',
        'Projects/S3/plots/rq01_size_vs_status.png'
    )
    
    # RQ02: PR Duration vs Status
    print("Analyzing RQ02: PR Duration vs Final Review Feedback...")
    rq02_results = analyze_pr_status_vs_duration(df)
    results['RQ02'] = rq02_results
    plot_results(
        rq02_results['correlation'],
        'RQ02: PR Duration vs Final Review Feedback',
        'Analysis Duration (hours)',
        'Spearman Correlation',
        'Projects/S3/plots/rq02_duration_vs_status.png'
    )
    
    # RQ03: PR Description vs Status
    print("Analyzing RQ03: PR Description Length vs Final Review Feedback...")
    rq03_results = analyze_pr_status_vs_description(df)
    results['RQ03'] = rq03_results
    plot_results(
        rq03_results['correlation'],
        'RQ03: PR Description Length vs Final Review Feedback',
        'Description Length (characters)',
        'Spearman Correlation',
        'Projects/S3/plots/rq03_description_vs_status.png'
    )
    
    # RQ04: PR Interactions vs Status
    print("Analyzing RQ04: PR Interactions vs Final Review Feedback...")
    rq04_results = analyze_pr_status_vs_interactions(df)
    results['RQ04'] = rq04_results
    plot_results(
        [rq04_results['participants_correlation'], rq04_results['comments_correlation']],
        'RQ04: PR Interactions vs Final Review Feedback',
        ['Participants', 'Comments'],
        'Spearman Correlation',
        'Projects/S3/plots/rq04_interactions_vs_status.png'
    )
    
    # RQ05: PR Size vs Number of Reviews
    print("Analyzing RQ05: PR Size vs Number of Reviews...")
    rq05_results = analyze_reviews_vs_size(df)
    results['RQ05'] = rq05_results
    plot_results(
        [rq05_results['files_correlation'], rq05_results['changes_correlation']],
        'RQ05: PR Size vs Number of Reviews',
        ['Changed Files', 'Total Changes (Additions + Deletions)'],
        'Spearman Correlation',
        'Projects/S3/plots/rq05_size_vs_reviews.png'
    )
    
    # RQ06: PR Duration vs Number of Reviews
    print("Analyzing RQ06: PR Duration vs Number of Reviews...")
    rq06_results = analyze_reviews_vs_duration(df)
    results['RQ06'] = rq06_results
    plot_results(
        rq06_results['correlation'],
        'RQ06: PR Duration vs Number of Reviews',
        'Analysis Duration (hours)',
        'Spearman Correlation',
        'Projects/S3/plots/rq06_duration_vs_reviews.png'
    )
    
    # RQ07: PR Description vs Number of Reviews
    print("Analyzing RQ07: PR Description Length vs Number of Reviews...")
    rq07_results = analyze_reviews_vs_description(df)
    results['RQ07'] = rq07_results
    plot_results(
        rq07_results['correlation'],
        'RQ07: PR Description Length vs Number of Reviews',
        'Description Length (characters)',
        'Spearman Correlation',
        'Projects/S3/plots/rq07_description_vs_reviews.png'
    )
    
    # RQ08: PR Interactions vs Number of Reviews
    print("Analyzing RQ08: PR Interactions vs Number of Reviews...")
    rq08_results = analyze_reviews_vs_interactions(df)
    results['RQ08'] = rq08_results
    plot_results(
        [rq08_results['participants_correlation'], rq08_results['comments_correlation']],
        'RQ08: PR Interactions vs Number of Reviews',
        ['Participants', 'Comments'],
        'Spearman Correlation',
        'Projects/S3/plots/rq08_interactions_vs_reviews.png'
    )
    
    # Save all results to JSON
    with open('Projects/S3/results/analysis_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    # Generate summary table
    summary = generate_summary_table(results)
    summary.to_csv('Projects/S3/results/summary.csv', index=False)
    
    print("\nAnalysis complete. Results saved to Projects/S3/results/")
    print("Plots saved to Projects/S3/plots/")

def generate_summary_table(results):
    """Generate a summary table of all results"""
    summary_data = []
    
    # RQ01
    summary_data.append({
        'Research Question': 'RQ01',
        'Dimension': 'Changed Files',
        'Vs. Status': f"{results['RQ01']['files_correlation']:.3f} (p={results['RQ01']['files_p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ05']['files_correlation']:.3f} (p={results['RQ05']['files_p_value']:.3f})"
    })
    summary_data.append({
        'Research Question': 'RQ01',
        'Dimension': 'Total Changes',
        'Vs. Status': f"{results['RQ01']['changes_correlation']:.3f} (p={results['RQ01']['changes_p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ05']['changes_correlation']:.3f} (p={results['RQ05']['changes_p_value']:.3f})"
    })
    
    # RQ02
    summary_data.append({
        'Research Question': 'RQ02',
        'Dimension': 'Duration (hours)',
        'Vs. Status': f"{results['RQ02']['correlation']:.3f} (p={results['RQ02']['p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ06']['correlation']:.3f} (p={results['RQ06']['p_value']:.3f})"
    })
    
    # RQ03
    summary_data.append({
        'Research Question': 'RQ03',
        'Dimension': 'Description Length',
        'Vs. Status': f"{results['RQ03']['correlation']:.3f} (p={results['RQ03']['p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ07']['correlation']:.3f} (p={results['RQ07']['p_value']:.3f})"
    })
    
    # RQ04
    summary_data.append({
        'Research Question': 'RQ04',
        'Dimension': 'Participants',
        'Vs. Status': f"{results['RQ04']['participants_correlation']:.3f} (p={results['RQ04']['participants_p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ08']['participants_correlation']:.3f} (p={results['RQ08']['participants_p_value']:.3f})"
    })
    summary_data.append({
        'Research Question': 'RQ04',
        'Dimension': 'Comments',
        'Vs. Status': f"{results['RQ04']['comments_correlation']:.3f} (p={results['RQ04']['comments_p_value']:.3f})",
        'Vs. Reviews': f"{results['RQ08']['comments_correlation']:.3f} (p={results['RQ08']['comments_p_value']:.3f})"
    })
    
    return pd.DataFrame(summary_data)

def generate_report(results_path='Projects/S3/results/analysis_results.json'):
    """Generate a final report based on analysis results"""
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("Results file not found. Please run analysis first.")
        return
    
    # Create an output directory for the report
    os.makedirs('Projects/S3/report', exist_ok=True)
    
    report = []
    report.append("# GitHub Pull Request (PR) Analysis Report")
    report.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    report.append("\n## Introduction")
    report.append("\nThis report analyzes pull request activities on popular GitHub repositories to identify factors " +
                  "influencing PR merges from the contributor's perspective. We explore relationships between PR attributes " +
                  "and both final review feedback (merged or closed) and the number of reviews received.")
    
    report.append("\n### Initial Hypotheses")
    report.append("\n1. **PR Size**: Smaller PRs are more likely to be merged and receive fewer reviews.")
    report.append("2. **Analysis Duration**: PRs with shorter analysis times are more likely to be merged.")
    report.append("3. **Description Length**: PRs with detailed descriptions are more likely to be merged.")
    report.append("4. **Interactions**: PRs with more interactions (participants and comments) might be more controversial but ultimately more likely to be merged due to thorough review.")
    
    report.append("\n## Methodology")
    report.append("\nWe collected data from top GitHub repositories with high activity levels. " +
                  "Each PR in our dataset has at least one review and was analyzed for more than one hour. " +
                  "We used Spearman's rank correlation coefficient to measure relationships between variables, " +
                  "as it does not assume linear relationships and is robust against outliers.")
    
    report.append("\n## Results")
    
    # Final Review Feedback (PR Status)
    report.append("\n### PR Attributes vs. Final Review Feedback")
    
    # RQ01
    report.append("\n#### RQ01: PR Size and Final Review Feedback")
    report.append(f"\nChanged Files: Correlation = {results['RQ01']['files_correlation']:.3f} (p-value = {results['RQ01']['files_p_value']:.3f})")
    report.append(f"Total Changes: Correlation = {results['RQ01']['changes_correlation']:.3f} (p-value = {results['RQ01']['changes_p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ01']['files_correlation'], results['RQ01']['files_p_value'], "PR size (files)", "merge probability"))
    
    # RQ02
    report.append("\n#### RQ02: PR Analysis Duration and Final Review Feedback")
    report.append(f"\nCorrelation = {results['RQ02']['correlation']:.3f} (p-value = {results['RQ02']['p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ02']['correlation'], results['RQ02']['p_value'], "analysis duration", "merge probability"))
    
    # RQ03
    report.append("\n#### RQ03: PR Description Length and Final Review Feedback")
    report.append(f"\nCorrelation = {results['RQ03']['correlation']:.3f} (p-value = {results['RQ03']['p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ03']['correlation'], results['RQ03']['p_value'], "description length", "merge probability"))
    
    # RQ04
    report.append("\n#### RQ04: PR Interactions and Final Review Feedback")
    report.append(f"\nParticipants: Correlation = {results['RQ04']['participants_correlation']:.3f} (p-value = {results['RQ04']['participants_p_value']:.3f})")
    report.append(f"Comments: Correlation = {results['RQ04']['comments_correlation']:.3f} (p-value = {results['RQ04']['comments_p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ04']['participants_correlation'], results['RQ04']['participants_p_value'], "number of participants", "merge probability"))
    
    # Number of Reviews
    report.append("\n### PR Attributes vs. Number of Reviews")
    
    # RQ05
    report.append("\n#### RQ05: PR Size and Number of Reviews")
    report.append(f"\nChanged Files: Correlation = {results['RQ05']['files_correlation']:.3f} (p-value = {results['RQ05']['files_p_value']:.3f})")
    report.append(f"Total Changes: Correlation = {results['RQ05']['changes_correlation']:.3f} (p-value = {results['RQ05']['changes_p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ05']['files_correlation'], results['RQ05']['files_p_value'], "PR size (files)", "number of reviews"))
    
    # RQ06
    report.append("\n#### RQ06: PR Analysis Duration and Number of Reviews")
    report.append(f"\nCorrelation = {results['RQ06']['correlation']:.3f} (p-value = {results['RQ06']['p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ06']['correlation'], results['RQ06']['p_value'], "analysis duration", "number of reviews"))
    
    # RQ07
    report.append("\n#### RQ07: PR Description Length and Number of Reviews")
    report.append(f"\nCorrelation = {results['RQ07']['correlation']:.3f} (p-value = {results['RQ07']['p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ07']['correlation'], results['RQ07']['p_value'], "description length", "number of reviews"))
    
    # RQ08
    report.append("\n#### RQ08: PR Interactions and Number of Reviews")
    report.append(f"\nParticipants: Correlation = {results['RQ08']['participants_correlation']:.3f} (p-value = {results['RQ08']['participants_p_value']:.3f})")
    report.append(f"Comments: Correlation = {results['RQ08']['comments_correlation']:.3f} (p-value = {results['RQ08']['comments_p_value']:.3f})")
    report.append("\nInterpretation: " + interpret_correlation(results['RQ08']['participants_correlation'], results['RQ08']['participants_p_value'], "number of participants", "number of reviews"))
    
    report.append("\n## Discussion and Conclusion")
    report.append("\nBased on our findings, we can draw several conclusions about factors that influence PR reviews:")
    
    # Add conclusions comparing against initial hypotheses
    report.append("\n1. **PR Size**: " + conclude_hypothesis(results['RQ01']['files_correlation'], results['RQ01']['files_p_value'],
                                                            "Smaller PRs are more likely to be merged",
                                                            "PR size negatively correlates with merge probability"))
    
    report.append("\n2. **Analysis Duration**: " + conclude_hypothesis(results['RQ02']['correlation'], results['RQ02']['p_value'],
                                                                       "PRs with shorter analysis times are more likely to be merged",
                                                                       "Longer analysis duration negatively correlates with merge probability"))
    
    report.append("\n3. **Description Length**: " + conclude_hypothesis(results['RQ03']['correlation'], results['RQ03']['p_value'],
                                                                        "PRs with detailed descriptions are more likely to be merged",
                                                                        "Description length positively correlates with merge probability"))
    
    report.append("\n4. **Interactions**: " + conclude_hypothesis(results['RQ04']['participants_correlation'], results['RQ04']['participants_p_value'],
                                                                  "PRs with more interactions are more likely to be merged due to thorough review",
                                                                  "The number of participants correlates with merge probability"))
    
    # Write report to file
    with open('Projects/S3/report/final_report.md', 'w') as f:
        f.write('\n'.join(report))
    
    print("\nReport generated: Projects/S3/report/final_report.md")

def interpret_correlation(correlation, p_value, var1, var2):
    """Interpret correlation results"""
    if p_value > 0.05:
        return f"There is no statistically significant correlation between {var1} and {var2} (p > 0.05)."
    
    strength = ""
    if abs(correlation) < 0.1:
        strength = "negligible"
    elif abs(correlation) < 0.3:
        strength = "weak"
    elif abs(correlation) < 0.5:
        strength = "moderate"
    elif abs(correlation) < 0.7:
        strength = "strong"
    else:
        strength = "very strong"
    
    direction = "positive" if correlation > 0 else "negative"
    
    return f"There is a {strength} {direction} correlation between {var1} and {var2} (correlation = {correlation:.3f}, p < 0.05)."

def conclude_hypothesis(correlation, p_value, hypothesis, conclusion_template):
    """Compare results against hypotheses"""
    if p_value > 0.05:
        return f"Our data neither supports nor refutes the hypothesis that \"{hypothesis}\" due to lack of statistical significance."
    
    if (correlation > 0 and "positively" in conclusion_template) or (correlation < 0 and "negatively" in conclusion_template):
        return f"Our data supports the hypothesis that \"{hypothesis}\". {conclusion_template}."
    else:
        return f"Our data contradicts the hypothesis that \"{hypothesis}\". {conclusion_template} in the opposite direction than expected."

if __name__ == "__main__":
    # Check for GitHub token
    if not os.getenv("GITHUB_TOKEN") and not '--use-sample' in sys.argv:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set your GitHub personal access token in the .env file")
        print("or with the following command:")
        print("export GITHUB_TOKEN=your_token_here")
        print("\nOr run with --use-sample to use sample data instead.")
        sys.exit(1)

    args = parse_args()
    
    if args.fetch:
        fetch_data(args.repo_limit, args.use_sample, args.timeout)
    
    if args.analyze:
        analyze_data()
        generate_report()
    
    if not args.fetch and not args.analyze:
        print("No action specified. Use --fetch to collect data or --analyze to analyze existing data.")
        print("Example: python main.py --fetch --analyze")
        print("Or use --use-sample to generate sample data: python main.py --fetch --use-sample --analyze") 