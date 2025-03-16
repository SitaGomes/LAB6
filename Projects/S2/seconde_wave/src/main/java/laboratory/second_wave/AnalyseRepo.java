package laboratory.second_wave;

import java.io.*;
import org.eclipse.jgit.api.Git;

public class AnalyseRepo {

    /**
     * Clona um repositório, executa a ferramenta CK para coletar as métricas
     * e, por fim, deleta o repositório clonado.
     *
     * @param repoUrl   URL para clonar o repositório (por exemplo,
     *                  "https://github.com/freeCodeCamp/freeCodeCamp.git").
     * @param ckJarPath Caminho para o arquivo ck.jar.
     * @throws Exception Caso ocorra algum erro durante a clonagem, execução ou
     *                   exclusão.
     */
    public static void cloneAndAnalyzeRepository(String repoUrl) throws Exception {
        String ckJarPath = "/home/arthur/Documents/code/College/LAB6-S01/ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar";

        // Cria um diretório temporário para clonar o repositório
        File localPath = File.createTempFile("tempRepo", "");
        if (!localPath.delete()) {
            throw new IOException("Não foi possível deletar o arquivo temporário: " + localPath);
        }

        // Clona o repositório (shallow clone para reduzir o volume de dados)
        System.out.println("Clonando o repositório: " + repoUrl);
        Git.cloneRepository()
                .setURI(repoUrl)
                .setDirectory(localPath)
                .setDepth(1) // Clona apenas o último commit
                .call();
        System.out.println("Repositório clonado em: " + localPath.getAbsolutePath());

        // Executa a ferramenta CK utilizando ProcessBuilder
        // O CK é executado passando o diretório do repositório clonado
        ProcessBuilder pb = new ProcessBuilder("java", "-jar", ckJarPath, localPath.getAbsolutePath());
        pb.redirectErrorStream(true);
        Process process = pb.start();

        // Lê a saída do processo e a imprime no console
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        }
        int exitCode = process.waitFor();
        System.out.println("Processo CK finalizado com código de saída: " + exitCode);

        // Opcional: listar os arquivos CSV gerados na pasta (se o CK gerar os CSVs no
        // diretório clonado)
        File[] csvFiles = localPath.listFiles((dir, name) -> name.toLowerCase().endsWith(".csv"));
        if (csvFiles != null && csvFiles.length > 0) {
            for (File csv : csvFiles) {
                System.out.println("Arquivo CSV gerado: " + csv.getAbsolutePath());
            }
        } else {
            System.out.println("Nenhum arquivo CSV encontrado no diretório do repositório clonado.");
        }

        // Exclui o diretório do repositório clonado para liberar espaço em disco
        deleteDirectory(localPath);
        System.out.println("Repositório clonado deletado.");
    }

    /**
     * Método recursivo para deletar um diretório e todo o seu conteúdo.
     *
     * @param directory Diretório a ser deletado.
     */
    private static void deleteDirectory(File directory) {
        File[] allContents = directory.listFiles();
        if (allContents != null) {
            for (File file : allContents) {
                deleteDirectory(file);
            }
        }
        directory.delete();
    }

}
