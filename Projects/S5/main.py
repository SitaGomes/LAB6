import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import numpy as np
import json
import os
import sys
import requests
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class GitHubAPIPerformanceStudy:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token or self.github_token == 'your_github_token_here':
            print("❌ Please set your GitHub personal access token in the .env file")
            print("Create a .env file in this directory with:")
            print("GITHUB_TOKEN=your_actual_token_here")
            sys.exit(1)
        
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-API-Performance-Study'
        }
        
        self.graphql_headers = {
            'Authorization': f'bearer {self.github_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'GitHub-API-Performance-Study'
        }
        
        self.rest_url = 'https://api.github.com/search/repositories'
        self.graphql_url = 'https://api.github.com/graphql'
        
        self.results = {
            'rest': {'times': [], 'data': [], 'requests': []},
            'graphql': {'times': [], 'data': [], 'requests': []}
        }

    def make_rest_request(self, page=1, per_page=100):
        """Make a REST API request to get repositories"""
        params = {
            'q': 'stars:>1',
            'sort': 'stars',
            'order': 'desc',
            'page': page,
            'per_page': per_page
        }
        
        start_time = time.time()
        response = requests.get(self.rest_url, headers=self.headers, params=params)
        end_time = time.time()
        
        if response.status_code != 200:
            raise Exception(f"REST API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        request_time = end_time - start_time
        
        return data, request_time

    def make_graphql_request(self, cursor=None, first=100):
        """Make a GraphQL API request to get repositories"""
        after_clause = f', after: "{cursor}"' if cursor else ''
        
        query = f"""
        {{
          search(query: "stars:>1", type: REPOSITORY, first: {first}{after_clause}) {{
            repositoryCount
            pageInfo {{
              endCursor
              hasNextPage
            }}
            edges {{
              node {{
                ... on Repository {{
                  name
                  owner {{
                    login
                  }}
                  stargazerCount
                  forkCount
                  createdAt
                  updatedAt
                  primaryLanguage {{
                    name
                  }}
                  description
                  url
                  isPrivate
                  licenseInfo {{
                    name
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        
        start_time = time.time()
        response = requests.post(
            self.graphql_url,
            headers=self.graphql_headers,
            json={'query': query}
        )
        end_time = time.time()
        
        if response.status_code != 200:
            raise Exception(f"GraphQL API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL Query Error: {data['errors']}")
        
        request_time = end_time - start_time
        
        return data, request_time

    def fetch_repos_via_rest(self, target_repos=1000):
        """Fetch repositories using REST API"""
        print(f"🔄 Fetching {target_repos} repositories via REST API...")
        
        repos = []
        page = 1
        per_page = 100  # GitHub's max for REST API
        
        with tqdm(total=target_repos, desc="REST API Progress") as pbar:
            while len(repos) < target_repos:
                try:
                    data, request_time = self.make_rest_request(page=page, per_page=per_page)
                    
                    self.results['rest']['times'].append(request_time)
                    self.results['rest']['requests'].append({
                        'page': page,
                        'per_page': per_page,
                        'time': request_time,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if 'items' not in data or not data['items']:
                        break
                    
                    for repo in data['items']:
                        if len(repos) >= target_repos:
                            break
                        
                        repos.append({
                            'name': repo['name'],
                            'owner': repo['owner']['login'],
                            'stars': repo['stargazers_count'],
                            'forks': repo['forks_count'],
                            'created_at': repo['created_at'],
                            'updated_at': repo['updated_at'],
                            'language': repo.get('language'),
                            'description': repo.get('description'),
                            'url': repo['html_url'],
                            'private': repo['private'],
                            'license': repo.get('license', {}).get('name') if repo.get('license') else None
                        })
                        pbar.update(1)
                    
                    page += 1
                    time.sleep(0.1)  # Rate limiting courtesy
                    
                except Exception as e:
                    print(f"❌ REST API Error on page {page}: {e}")
                    break
        
        self.results['rest']['data'] = repos
        print(f"✅ REST API: Fetched {len(repos)} repositories in {len(self.results['rest']['times'])} requests")
        return repos

    def fetch_repos_via_graphql(self, target_repos=1000):
        """Fetch repositories using GraphQL API"""
        print(f"🔄 Fetching {target_repos} repositories via GraphQL API...")
        
        repos = []
        cursor = None
        first = 100  # Items per request
        
        with tqdm(total=target_repos, desc="GraphQL API Progress") as pbar:
            while len(repos) < target_repos:
                try:
                    data, request_time = self.make_graphql_request(cursor=cursor, first=first)
                    
                    self.results['graphql']['times'].append(request_time)
                    self.results['graphql']['requests'].append({
                        'cursor': cursor,
                        'first': first,
                        'time': request_time,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    search_data = data['data']['search']
                    
                    if not search_data['edges']:
                        break
                    
                    for edge in search_data['edges']:
                        if len(repos) >= target_repos:
                            break
                        
                        repo = edge['node']
                        repos.append({
                            'name': repo['name'],
                            'owner': repo['owner']['login'],
                            'stars': repo['stargazerCount'],
                            'forks': repo['forkCount'],
                            'created_at': repo['createdAt'],
                            'updated_at': repo['updatedAt'],
                            'language': repo.get('primaryLanguage', {}).get('name') if repo.get('primaryLanguage') else None,
                            'description': repo.get('description'),
                            'url': repo['url'],
                            'private': repo['isPrivate'],
                            'license': repo.get('licenseInfo', {}).get('name') if repo.get('licenseInfo') else None
                        })
                        pbar.update(1)
                    
                    if not search_data['pageInfo']['hasNextPage']:
                        break
                    
                    cursor = search_data['pageInfo']['endCursor']
                    time.sleep(0.1)  # Rate limiting courtesy
                    
                except Exception as e:
                    print(f"❌ GraphQL API Error: {e}")
                    break
        
        self.results['graphql']['data'] = repos
        print(f"✅ GraphQL API: Fetched {len(repos)} repositories in {len(self.results['graphql']['times'])} requests")
        return repos

    def save_results_to_json(self):
        """Save all results to JSON files"""
        print("💾 Saving results to JSON files...")
        
        # Save performance metrics
        performance_data = {
            'study_metadata': {
                'timestamp': datetime.now().isoformat(),
                'target_repos': 1000,
                'rest_requests': len(self.results['rest']['times']),
                'graphql_requests': len(self.results['graphql']['times']),
            },
            'rest_api': {
                'total_time': sum(self.results['rest']['times']),
                'avg_time_per_request': np.mean(self.results['rest']['times']),
                'std_time_per_request': np.std(self.results['rest']['times']),
                'min_time': min(self.results['rest']['times']),
                'max_time': max(self.results['rest']['times']),
                'request_times': self.results['rest']['times'],
                'request_details': self.results['rest']['requests']
            },
            'graphql_api': {
                'total_time': sum(self.results['graphql']['times']),
                'avg_time_per_request': np.mean(self.results['graphql']['times']),
                'std_time_per_request': np.std(self.results['graphql']['times']),
                'min_time': min(self.results['graphql']['times']),
                'max_time': max(self.results['graphql']['times']),
                'request_times': self.results['graphql']['times'],
                'request_details': self.results['graphql']['requests']
            }
        }
        
        with open('performance_metrics.json', 'w') as f:
            json.dump(performance_data, f, indent=2)
        
        # Save repository data
        with open('rest_api_repos.json', 'w') as f:
            json.dump(self.results['rest']['data'], f, indent=2)
        
        with open('graphql_api_repos.json', 'w') as f:
            json.dump(self.results['graphql']['data'], f, indent=2)
        
        print("✅ Results saved to JSON files")

    def create_performance_graphs(self):
        """Create comprehensive performance comparison graphs"""
        print("📊 Creating performance comparison graphs...")
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('GitHub API Performance Study: REST vs GraphQL', fontsize=16, fontweight='bold')
        
        # 1. Request Times Comparison (Box Plot)
        ax1 = axes[0, 0]
        data_to_plot = [self.results['rest']['times'], self.results['graphql']['times']]
        bp = ax1.boxplot(data_to_plot, labels=['REST API', 'GraphQL API'], patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightgreen')
        ax1.set_title('Request Time Distribution')
        ax1.set_ylabel('Time (seconds)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Average Response Times (Bar Chart)
        ax2 = axes[0, 1]
        apis = ['REST API', 'GraphQL API']
        avg_times = [np.mean(self.results['rest']['times']), np.mean(self.results['graphql']['times'])]
        std_times = [np.std(self.results['rest']['times']), np.std(self.results['graphql']['times'])]
        
        bars = ax2.bar(apis, avg_times, yerr=std_times, capsize=5, 
                      color=['lightblue', 'lightgreen'], alpha=0.7)
        ax2.set_title('Average Response Time (±σ)')
        ax2.set_ylabel('Time (seconds)')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, avg_time in zip(bars, avg_times):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{avg_time:.3f}s', ha='center', va='bottom')
        
        # 3. Cumulative Request Times
        ax3 = axes[1, 0]
        rest_cumulative = np.cumsum(self.results['rest']['times'])
        graphql_cumulative = np.cumsum(self.results['graphql']['times'])
        
        ax3.plot(range(1, len(rest_cumulative) + 1), rest_cumulative, 
                'o-', label='REST API', color='blue', alpha=0.7)
        ax3.plot(range(1, len(graphql_cumulative) + 1), graphql_cumulative, 
                's-', label='GraphQL API', color='green', alpha=0.7)
        ax3.set_title('Cumulative Response Time')
        ax3.set_xlabel('Request Number')
        ax3.set_ylabel('Cumulative Time (seconds)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Performance Summary Table
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Calculate statistics
        rest_stats = {
            'Total Requests': len(self.results['rest']['times']),
            'Total Time': f"{sum(self.results['rest']['times']):.3f}s",
            'Avg Time': f"{np.mean(self.results['rest']['times']):.3f}s",
            'Std Dev': f"{np.std(self.results['rest']['times']):.3f}s",
            'Min Time': f"{min(self.results['rest']['times']):.3f}s",
            'Max Time': f"{max(self.results['rest']['times']):.3f}s"
        }
        
        graphql_stats = {
            'Total Requests': len(self.results['graphql']['times']),
            'Total Time': f"{sum(self.results['graphql']['times']):.3f}s",
            'Avg Time': f"{np.mean(self.results['graphql']['times']):.3f}s",
            'Std Dev': f"{np.std(self.results['graphql']['times']):.3f}s",
            'Min Time': f"{min(self.results['graphql']['times']):.3f}s",
            'Max Time': f"{max(self.results['graphql']['times']):.3f}s"
        }
        
        table_data = []
        for key in rest_stats.keys():
            table_data.append([key, rest_stats[key], graphql_stats[key]])
        
        table = ax4.table(cellText=table_data,
                         colLabels=['Metric', 'REST API', 'GraphQL API'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Color code the headers
        table[(0, 1)].set_facecolor('lightblue')
        table[(0, 2)].set_facecolor('lightgreen')
        
        ax4.set_title('Performance Statistics Summary')
        
        plt.tight_layout()
        plt.savefig('github_api_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create additional detailed analysis plot
        self.create_detailed_analysis_plot()
        
        print("✅ Performance graphs created and saved")

    def create_detailed_analysis_plot(self):
        """Create a detailed analysis plot with statistical tests"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Detailed Performance Analysis', fontsize=16, fontweight='bold')
        
        # 1. Time series of requests
        ax1 = axes[0]
        ax1.plot(self.results['rest']['times'], 'o-', label='REST API', alpha=0.7)
        ax1.plot(self.results['graphql']['times'], 's-', label='GraphQL API', alpha=0.7)
        ax1.set_title('Request Response Times Over Time')
        ax1.set_xlabel('Request Number')
        ax1.set_ylabel('Response Time (seconds)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Statistical comparison
        ax2 = axes[1]
        
        # Perform statistical test
        rest_times = self.results['rest']['times']
        graphql_times = self.results['graphql']['times']
        
        # Welch's t-test (assuming unequal variances)
        t_stat, p_value = stats.ttest_ind(rest_times, graphql_times, equal_var=False)
        
        # Create histogram comparison
        ax2.hist(rest_times, alpha=0.5, label=f'REST API (n={len(rest_times)})', 
                bins=20, color='blue', density=True)
        ax2.hist(graphql_times, alpha=0.5, label=f'GraphQL API (n={len(graphql_times)})', 
                bins=20, color='green', density=True)
        
        ax2.set_title(f'Response Time Distribution\n(t-test: t={t_stat:.3f}, p={p_value:.3f})')
        ax2.set_xlabel('Response Time (seconds)')
        ax2.set_ylabel('Density')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('github_api_detailed_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

    def print_summary(self):
        """Print a comprehensive summary of the study"""
        print("\n" + "="*80)
        print("🎯 GITHUB API PERFORMANCE STUDY SUMMARY")
        print("="*80)
        
        rest_total = sum(self.results['rest']['times'])
        graphql_total = sum(self.results['graphql']['times'])
        rest_avg = np.mean(self.results['rest']['times'])
        graphql_avg = np.mean(self.results['graphql']['times'])
        
        print(f"📊 Data Retrieved:")
        print(f"   • REST API: {len(self.results['rest']['data'])} repositories")
        print(f"   • GraphQL API: {len(self.results['graphql']['data'])} repositories")
        
        print(f"\n⏱️  Total Time:")
        print(f"   • REST API: {rest_total:.3f} seconds ({len(self.results['rest']['times'])} requests)")
        print(f"   • GraphQL API: {graphql_total:.3f} seconds ({len(self.results['graphql']['times'])} requests)")
        
        print(f"\n⚡ Average Response Time:")
        print(f"   • REST API: {rest_avg:.3f} ± {np.std(self.results['rest']['times']):.3f} seconds")
        print(f"   • GraphQL API: {graphql_avg:.3f} ± {np.std(self.results['graphql']['times']):.3f} seconds")
        
        if rest_avg > graphql_avg:
            improvement = ((rest_avg - graphql_avg) / rest_avg) * 100
            print(f"\n🏆 Winner: GraphQL API is {improvement:.1f}% faster on average")
        else:
            improvement = ((graphql_avg - rest_avg) / graphql_avg) * 100
            print(f"\n🏆 Winner: REST API is {improvement:.1f}% faster on average")
        
        # Statistical significance test
        t_stat, p_value = stats.ttest_ind(self.results['rest']['times'], 
                                         self.results['graphql']['times'], equal_var=False)
        
        print(f"\n📈 Statistical Analysis:")
        print(f"   • t-statistic: {t_stat:.3f}")
        print(f"   • p-value: {p_value:.6f}")
        print(f"   • Significance: {'Yes' if p_value < 0.05 else 'No'} (α = 0.05)")
        
        print("\n💾 Files Created:")
        print("   • performance_metrics.json - Detailed performance data")
        print("   • rest_api_repos.json - Repository data from REST API")
        print("   • graphql_api_repos.json - Repository data from GraphQL API")
        print("   • github_api_performance_comparison.png - Main comparison charts")
        print("   • github_api_detailed_analysis.png - Detailed statistical analysis")
        
        print("="*80)

def main():
    """Main execution function"""
    print("🚀 Starting GitHub API Performance Study")
    print("="*50)
    
    # Initialize the study
    study = GitHubAPIPerformanceStudy()
    
    try:
        # Fetch data using both APIs
        study.fetch_repos_via_rest(target_repos=1000)
        study.fetch_repos_via_graphql(target_repos=1000)
        
        # Save results
        study.save_results_to_json()
        
        # Create visualizations
        study.create_performance_graphs()
        
        # Print summary
        study.print_summary()
        
        print("\n✅ Study completed successfully!")
        
    except Exception as e:
        print(f"❌ Study failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

