# GitHub Pull Request (PR) Analysis

This project analyzes code review activities in popular GitHub repositories to identify factors influencing the merge of a pull request from the perspective of contributors submitting code.

## Features

- Fetches data from the top 200 most popular GitHub repositories
- Filters repositories with at least 100 PRs
- Analyzes PRs with at least one review and that were reviewed for at least one hour
- Generates correlation analyses for eight research questions related to PR attributes
- Creates visualizations of the results
- Produces a comprehensive final report

## Research Questions

### Final Feedback of Reviews (PR Status)

- **RQ01**: What's the relationship between PR size and final review feedback?
- **RQ02**: What's the relationship between PR analysis duration and final review feedback?
- **RQ03**: What's the relationship between PR description length and final review feedback?
- **RQ04**: What's the relationship between interactions in PRs and final review feedback?

### Number of Reviews

- **RQ05**: What's the relationship between PR size and the number of reviews?
- **RQ06**: What's the relationship between PR analysis duration and the number of reviews?
- **RQ07**: What's the relationship between PR description length and the number of reviews?
- **RQ08**: What's the relationship between interactions in PRs and the number of reviews?

## Prerequisites

- Python 3.7+
- GitHub personal access token with appropriate permissions

## Installation

1. Clone this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your GitHub token in the `.env` file:

```
# Create a .env file in the root directory
GITHUB_TOKEN=your_github_token_here
```

Alternatively, you can set it as an environment variable:

```bash
export GITHUB_TOKEN=your_github_token_here
```

## Usage

### Fetching Data

To fetch data from GitHub:

```bash
python main.py --fetch
```

This will collect data from the top repositories and their pull requests according to the specified criteria and save them to CSV files in the `data` directory.

### Analyzing Data

To analyze the collected data:

```bash
python main.py --analyze
```

This will perform the correlation analyses, generate visualizations, and produce a final report.

### Complete Process

To fetch data and analyze it in one command:

```bash
python main.py --fetch --analyze
```

### Customizing the Analysis

You can limit the number of repositories to analyze (default is 200):

```bash
python main.py --fetch --analyze --repo-limit 100
```

## Output

The script generates several outputs:

- **Raw Data**: CSV files in the `data` directory
- **Analysis Results**: JSON and CSV files in the `results` directory
- **Visualizations**: PNG files in the `plots` directory
- **Final Report**: Markdown file in the `report` directory

## Methodology

The analysis uses Spearman's rank correlation coefficient to measure relationships between variables, as it does not assume linear relationships and is robust against outliers.

The following metrics are used for each dimension:

- **Size**: Number of files changed; total lines added and removed
- **Analysis Duration**: Time between PR creation and last activity (merge or close)
- **Description**: Number of characters in the PR description body
- **Interactions**: Number of participants; total comments count
