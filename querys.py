querys = """
query($first: Int!, $cursor: String) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $cursor) {
    nodes {
      ... on Repository {
        name
        owner { login }
        stargazers { totalCount }
        
        pullRequests(states: [MERGED]) {
          totalCount
        }
        
        allIssues: issues(states: [OPEN, CLOSED]) {
          totalCount 
        }

        closedIssues: issues(states: [CLOSED]) {
          totalCount 
        }

        primaryLanguage {
          name 
        }

        createdAt
        
        # Added fields:
        releases {
          totalCount
        }
        
        updatedAt
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""
