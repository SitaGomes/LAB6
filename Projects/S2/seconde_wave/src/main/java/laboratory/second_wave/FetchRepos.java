package laboratory.second_wave;

import java.io.*;
import java.net.URI;
import java.net.http.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class FetchRepos {

    // Substitua pelo seu token de acesso do GitHub
    private static final String ACCESS_TOKEN = "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";
    private static final String GRAPHQL_URL = "https://api.github.com/graphql";
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) {
        try {
            // 1. Executa a query GraphQL para buscar 1 repositório do owner especificado
            JsonNode response = fetchRepositories(1, null);
            // Extrai o primeiro nó (repositório) da resposta
            JsonNode repository = response.path("data")
                    .path("search")
                    .path("nodes")
                    .get(0);
            if (repository == null || repository.isMissingNode()) {
                System.out.println("Nenhum repositório encontrado.");
                return;
            }

            // 2. Extrai informações relevantes do repositório
            String repoName = repository.path("name").asText();
            String owner = repository.path("owner").path("login").asText();
            // int stars = repository.path("stargazers").path("totalCount").asInt();
            // String createdAt = repository.path("createdAt").asText();

            // Constrói a URL de clone (HTTPS)
            String cloneUrl = "https://github.com/" + owner + "/" + repoName + ".git";
            System.out.println("Repositório: " + owner + "/" + repoName);
            System.out.println("Clone URL: " + cloneUrl);

            AnalyseRepo.cloneAndAnalyzeRepository(cloneUrl);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static JsonNode fetchRepositories(int first, String cursor) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        // Adjusted query: filtering for repositories with more than 1000 stars
        String query = """
                query($first: Int!, $cursor: String) {
                  search(query: "stars:>1000 sort:stars-desc", type: REPOSITORY, first: $first, after: $cursor) {
                    nodes {
                      ... on Repository {
                        name
                        owner { login }
                        stargazers { totalCount }
                        pullRequests(states: [MERGED]) { totalCount }
                        allIssues: issues(states: [OPEN, CLOSED]) { totalCount }
                        closedIssues: issues(states: [CLOSED]) { totalCount }
                        primaryLanguage { name }
                        createdAt
                        releases { totalCount }
                        updatedAt
                      }
                    }
                    pageInfo {
                      endCursor
                      hasNextPage
                    }
                  }
                }

                """;

        // Create the request body with query and variables
        ObjectNode variables = mapper.createObjectNode();
        variables.put("first", first);
        if (cursor != null) {
            variables.put("cursor", cursor);
        } else {
            variables.putNull("cursor");
        }
        ObjectNode jsonBody = mapper.createObjectNode();
        jsonBody.put("query", query);
        jsonBody.set("variables", variables);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(GRAPHQL_URL))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + ACCESS_TOKEN)
                .POST(HttpRequest.BodyPublishers.ofString(jsonBody.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // Debug: print entire JSON response
        System.out.println("Response JSON: " + response.body());

        if (response.statusCode() == 200) {
            return mapper.readTree(response.body());
        } else {
            throw new RuntimeException("Query falhou: " + response.statusCode() + " - " + response.body());
        }
    }

}
