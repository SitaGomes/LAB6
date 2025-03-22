package laboratory.second_wave;

import java.io.*;
import org.eclipse.jgit.api.Git;

public class AnalyseRepo {

    public static void cloneAndAnalyzeRepository(String repoUrl) throws Exception {
        String ckJarPath = "/home/arthur/Documents/code/College/LAB6-S01/ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar";

        File localPath = File.createTempFile("tempRepo", "");
        if (!localPath.delete()) {
            throw new IOException("Não foi possível deletar o arquivo temporário: " + localPath);
        }

        System.out.println("Clonando o repositório: " + repoUrl);
        Git.cloneRepository()
                .setURI(repoUrl)
                .setDirectory(localPath)
                .setDepth(1)
                .call();
        System.out.println("Repositório clonado em: " + localPath.getAbsolutePath());

        ProcessBuilder pb = new ProcessBuilder("java", "-jar", ckJarPath, localPath.getAbsolutePath());
        pb.redirectErrorStream(true);
        Process process = pb.start();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        }
        int exitCode = process.waitFor();
        System.out.println("Processo CK finalizado com código de saída: " + exitCode);

        File[] csvFiles = localPath.listFiles((dir, name) -> name.toLowerCase().endsWith(".csv"));
        if (csvFiles != null && csvFiles.length > 0) {
            for (File csv : csvFiles) {
                System.out.println("Arquivo CSV gerado: " + csv.getAbsolutePath());
            }
        } else {
            System.out.println("Nenhum arquivo CSV encontrado no diretório do repositório clonado.");
        }

        deleteDirectory(localPath);
        System.out.println("Repositório clonado deletado.");
    }

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
