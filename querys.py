mostFamousQuery = """
query {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: 100) {
    nodes {
      ... on Repository {
        name
        owner {
          login
        }
        stargazerCount
        description
        url
      }
    }
  }
}
"""