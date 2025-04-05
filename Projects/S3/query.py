# Step 1: Just fetch basic repository information
query_repositories = """
query($first: Int!, $cursor: String) {
  search(query: "stars:>1000 sort:stars-desc", type: REPOSITORY, first: $first, after: $cursor) {
    nodes {
      ... on Repository {
        name
        owner { login }
        url
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""

# Step 2: Fetch PR counts separately for each repository
query_repository_pr_count = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [MERGED, CLOSED]) {
      totalCount
    }
  }
}
"""

# Simplified PR query with minimal fields
query_pull_requests = """
query($owner: String!, $name: String!, $first: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: $first, after: $cursor, states: [MERGED, CLOSED]) {
      totalCount
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        number
        state
        createdAt
        mergedAt
        closedAt
      }
    }
  }
}
"""

# Fetch PR details separately to reduce complexity
query_pull_request_details = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      title
      bodyText
      changedFiles
      additions
      deletions
    }
  }
}
"""

# Fetch PR review counts separately
query_pull_request_review_count = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviews {
        totalCount
      }
    }
  }
}
"""

# Fetch PR comments count separately
query_pull_request_comments_count = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      comments {
        totalCount
      }
    }
  }
}
"""

# Fetch PR participants count separately
query_pull_request_participants_count = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      participants {
        totalCount
      }
    }
  }
}
""" 