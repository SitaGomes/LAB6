package laboratory.second_wave;

import java.net.URI;
import java.net.http.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class Main {

  private static final String ACCESS_TOKEN = "";
  private static final String GRAPHQL_URL = "https://api.github.com/graphql";
  private static final ObjectMapper mapper = new ObjectMapper();

  public static void main(String[] args) {
    try {

      String cursor = null;

      for (int i = 0; i < 1000; i++) {

        JsonNode response = fetchRepositories(1, cursor);

        JsonNode repository = response.path("data")
            .path("search")
            .path("nodes")
            .get(0);
        if (repository == null || repository.isMissingNode()) {
          System.out.println("Nenhum repositório encontrado na iteração " + (i + 1));
          break;
        }

        String repoName = repository.path("name").asText();
        String owner = repository.path("owner").path("login").asText();

        String cloneUrl = "https://github.com/" + owner + "/" + repoName + ".git";
        System.out.println("[" + (i + 1) + "] Repositório: " + owner + "/" + repoName);
        System.out.println("Clone URL: " + cloneUrl);

        AnalyseRepo.cloneAndAnalyzeRepository(cloneUrl);

        JsonNode pageInfo = response.path("data")
            .path("search")
            .path("pageInfo");
        boolean hasNextPage = pageInfo.path("hasNextPage").asBoolean();

        if (!hasNextPage) {
          System.out.println("Fim dos repositórios disponíveis.");
          break;
        }
        cursor = pageInfo.path("endCursor").asText();

        Thread.sleep(1000);
      }

    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  private static JsonNode fetchRepositories(int first, String cursor) throws Exception {
    HttpClient client = HttpClient.newHttpClient();
    String query = """
        query($first: Int!, $cursor: String) {
          search(query: "language:Java stars:>1000 sort:stars-desc", type: REPOSITORY, first: $first, after: $cursor) {
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

    System.out.println("Response JSON: " + response.body());

    if (response.statusCode() == 200) {
      return mapper.readTree(response.body());
    } else {
      throw new RuntimeException("Query falhou: " + response.statusCode() + " - " + response.body());
    }
  }

}
