# Task Documentation: GitHub Pull Request (PR) Analysis

## Introduction

Code review practices have become essential within agile development workflows. Generally, code review involves interactions between developers and reviewers to inspect code before integrating it into the main codebase, ensuring code quality and preventing defects.

In open-source systems, especially those hosted on GitHub, code reviews typically involve evaluating contributions submitted via Pull Requests (PRs). For code to be integrated into the main branch, developers must submit a pull request that is then evaluated and discussed by project collaborators. Ultimately, the reviewer may either approve or reject the merge request. Frequently, automated tools perform an initial analysis, assessing code style or predefined organizational standards.

The objective of this task is to analyze code review activities in popular GitHub repositories to identify factors influencing the merge of a PR from the perspective of contributors submitting code.

## Methodology

### 1. Dataset Creation

The dataset for this analysis consists of PRs from repositories that meet the following criteria:

- **Popularity**: PRs submitted to the top 200 most popular GitHub repositories.
- **Activity Level**: Each repository must have at least 100 PRs (MERGED + CLOSED).

Additionally, to ensure inclusion of PRs that underwent genuine code review, select only PRs that:

- Have status **MERGED** or **CLOSED**.
- Have at least one review (`review` total count ≥ 1).

Finally, to exclude automatically reviewed PRs (e.g., bots or CI/CD tools), select only PRs reviewed for at least one hour (time between PR creation and merge or close > 1 hour).

### 2. Research Questions

Based on the collected dataset, we aim to answer the following research questions, divided into two categories:

#### A. Final Feedback of Reviews (PR Status)

- **RQ01**: What's the relationship between PR size and final review feedback?
- **RQ02**: What's the relationship between PR analysis duration and final review feedback?
- **RQ03**: What's the relationship between PR description length and final review feedback?
- **RQ04**: What's the relationship between interactions in PRs and final review feedback?

#### B. Number of Reviews

- **RQ05**: What's the relationship between PR size and the number of reviews?
- **RQ06**: What's the relationship between PR analysis duration and the number of reviews?
- **RQ07**: What's the relationship between PR description length and the number of reviews?
- **RQ08**: What's the relationship between interactions in PRs and the number of reviews?

### 3. Metrics Definition

For each dimension, correlations will be performed using the following metrics:

- **Size**: Number of files changed; total lines added and removed.
- **Analysis Duration**: Time between PR creation and last activity (merge or close).
- **Description**: Number of characters in the PR description body (in markdown format).
- **Interactions**: Number of participants; total comments count.

## Final Report

The final report should contain the following elements:

1. **Introduction**: Provide informal hypotheses regarding expected outcomes.
2. **Methodology**: Clearly describe the methods used to answer the research questions.
3. **Results**: Present median values for each research question across all PRs without repository-specific segmentation.
4. **Discussion**: Compare obtained results against initial hypotheses, explaining any observations or deviations.

**Statistical Analysis:**
Use a reliable statistical test to measure correlations (e.g., Spearman's or Pearson's correlation test). Clearly justify your choice.
