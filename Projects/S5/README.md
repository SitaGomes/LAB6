# GitHub API Performance Study: REST vs GraphQL

This project compares the performance of GitHub's REST API vs GraphQL API by fetching the 1000 most starred repositories.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. GitHub Token Setup

1. Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name like "API Performance Study"
4. Select the following scopes:
   - `public_repo` (to access public repositories)
   - `read:user` (optional, for user info)
5. Copy the generated token

### 3. Configure Environment

Edit the `.env` file and replace `your_github_token_here` with your actual token:

```
GITHUB_TOKEN=ghp_your_actual_token_here
```

### 4. Run the Study

```bash
python main.py
```

## What the Study Does

1. **Fair Comparison**: Uses identical queries to fetch the same data from both APIs
2. **Comprehensive Data**: Retrieves 1000 most starred repositories with detailed information
3. **Performance Metrics**: Measures response times, total time, and statistical significance
4. **Multiple Requests**: Makes necessary paginated requests (typically 10 per API)
5. **Data Storage**: Saves all results in JSON format
6. **Visualizations**: Creates detailed performance comparison charts

## Output Files

- `performance_metrics.json` - Detailed performance statistics
- `rest_api_repos.json` - Repository data from REST API
- `graphql_api_repos.json` - Repository data from GraphQL API
- `github_api_performance_comparison.png` - Main comparison charts
- `github_api_detailed_analysis.png` - Statistical analysis charts

## Study Features

- ✅ Rate limiting compliance
- ✅ Progress bars for real-time feedback
- ✅ Error handling and recovery
- ✅ Statistical significance testing
- ✅ Comprehensive visualizations
- ✅ JSON data export
- ✅ Fair comparison methodology

## Expected Results

The study will show you:

- Which API is faster on average
- Response time distributions
- Statistical significance of differences
- Cumulative performance over time
- Detailed metrics comparison table

## Note

This study respects GitHub's API rate limits and includes proper delays between requests.
