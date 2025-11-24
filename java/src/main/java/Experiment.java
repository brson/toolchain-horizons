import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import com.google.gson.*;
import com.google.gson.annotations.SerializedName;

/**
 * Dependency toolchain compatibility experiment for Java.
 *
 * This experiment tests how adding a single dependency affects the range
 * of Java versions that can successfully compile with that dependency.
 *
 * Uses SDKMAN for Java version management and Maven for dependency resolution.
 */
public class Experiment {

    // Package represents a Maven dependency to test.
    static class Package {
        String groupId;
        String artifactId;
        String versionRange;

        Package(String groupId, String artifactId, String versionRange) {
            this.groupId = groupId;
            this.artifactId = artifactId;
            this.versionRange = versionRange;
        }

        String getCoordinate() {
            return groupId + ":" + artifactId;
        }
    }

    // List of packages to test (groupId, artifactId, version range).
    //
    // Using version ranges to allow the resolver flexibility.
    static final Package[] PACKAGES = {
        // Core Apache Commons.
        new Package("org.apache.commons", "commons-lang3", "[3.12,4.0)"),
        new Package("commons-io", "commons-io", "[2.11,3.0)"),
        new Package("org.apache.commons", "commons-collections4", "[4.4,5.0)"),
        new Package("org.apache.commons", "commons-text", "[1.10,2.0)"),
        new Package("org.apache.commons", "commons-math3", "[3.6,4.0)"),
        new Package("org.apache.commons", "commons-csv", "[1.10,2.0)"),

        // Logging.
        new Package("org.slf4j", "slf4j-api", "[2.0,3.0)"),
        new Package("ch.qos.logback", "logback-classic", "[1.4,2.0)"),

        // JSON Processing.
        new Package("com.google.code.gson", "gson", "[2.10,3.0)"),
        new Package("com.fasterxml.jackson.core", "jackson-databind", "[2.15,3.0)"),

        // Testing.
        new Package("org.junit.jupiter", "junit-jupiter", "[5.10,6.0)"),
        new Package("org.mockito", "mockito-core", "[5.0,6.0)"),
        new Package("org.assertj", "assertj-core", "[3.24,4.0)"),

        // Utilities.
        new Package("com.google.guava", "guava", "[32.0,33.0)"),

        // HTTP Clients.
        new Package("org.apache.httpcomponents", "httpclient", "[4.5,5.0)"),
        new Package("com.squareup.okhttp3", "okhttp", "[4.12,5.0)"),

        // Date/Time.
        new Package("joda-time", "joda-time", "[2.12,3.0)"),

        // Async/Reactive.
        new Package("io.reactivex.rxjava3", "rxjava", "[3.1,4.0)"),

        // Database.
        new Package("com.h2database", "h2", "[2.2,3.0)"),
        new Package("org.postgresql", "postgresql", "[42.7,43.0)"),
        new Package("com.zaxxer", "HikariCP", "[5.1,6.0)"),

        // XML/YAML.
        new Package("org.dom4j", "dom4j", "[2.1,3.0)"),
        new Package("org.yaml", "snakeyaml", "[2.0,3.0)"),

        // Dependency Injection.
        new Package("javax.inject", "javax.inject", "[1,2)"),
        new Package("com.google.inject", "guice", "[7.0,8.0)"),

        // Validation.
        new Package("jakarta.validation", "jakarta.validation-api", "[3.0,4.0)"),
    };

    // Java versions to test.
    // Starting from Java 8 (oldest LTS still widely used).
    static final String[] JAVA_VERSIONS = {
        "8.0.432-tem",    // Java 8
        "11.0.25-tem",    // Java 11
        "17.0.13-tem",    // Java 17
        "21.0.5-tem",     // Java 21
        "23.0.1-tem",     // Java 23
    };

    // ExperimentResult holds results for a single package test.
    static class ExperimentResult {
        @SerializedName("package_name")
        String packageName;

        @SerializedName("version_spec")
        String versionSpec;

        @SerializedName("resolved_version")
        String resolvedVersion;

        @SerializedName("oldest_compatible")
        String oldestCompatible;

        @SerializedName("latest_compatible")
        String latestCompatible;

        @SerializedName("error")
        String error;

        ExperimentResult(String packageName, String versionSpec) {
            this.packageName = packageName;
            this.versionSpec = versionSpec;
        }
    }

    public static void main(String[] args) throws Exception {
        // Check if a specific package was requested.
        if (args.length > 0) {
            String packageCoordinate = args[0];
            System.out.printf("Testing single package: %s%n", packageCoordinate);
            runSinglePackageExperiment(packageCoordinate);
        } else {
            System.out.println("Starting dependency toolchain compatibility experiment");
            System.out.printf("Testing %d packages%n", PACKAGES.length);
            runFullExperiment();
        }
    }

    // Run the full experiment on all packages.
    static void runFullExperiment() throws Exception {
        List<ExperimentResult> results = new ArrayList<>();

        // First, test the control case (no dependencies).
        System.out.println("\n=== Testing control case (no dependencies) ===");
        try {
            ExperimentResult result = testControlCase();
            System.out.printf("Control: oldest=%s, latest=%s%n",
                result.oldestCompatible, result.latestCompatible);
            results.add(result);
        } catch (Exception e) {
            System.out.printf("Control case failed: %s%n", e.getMessage());
        }

        // Test each package.
        for (Package pkg : PACKAGES) {
            System.out.printf("\n=== Testing %s ===%n", pkg.getCoordinate());
            try {
                ExperimentResult result = testPackage(pkg);
                System.out.printf("%s: oldest=%s, latest=%s%n",
                    pkg.getCoordinate(), result.oldestCompatible, result.latestCompatible);
                results.add(result);
            } catch (Exception e) {
                System.out.printf("%s failed: %s%n", pkg.getCoordinate(), e.getMessage());
                ExperimentResult errorResult = new ExperimentResult(pkg.getCoordinate(), pkg.versionRange);
                errorResult.error = e.getMessage();
                results.add(errorResult);
            }
        }

        // Write results.
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(results);
        Files.writeString(Paths.get("results.json"), json);
        System.out.println("\n=== Results written to results.json ===");
    }

    // Run experiment on a single package.
    static void runSinglePackageExperiment(String packageCoordinate) throws Exception {
        // Find the package in our list.
        Package targetPkg = null;
        for (Package pkg : PACKAGES) {
            if (pkg.getCoordinate().equals(packageCoordinate)) {
                targetPkg = pkg;
                break;
            }
        }

        if (targetPkg == null) {
            System.out.printf("Warning: '%s' not found in predefined list%n", packageCoordinate);
            System.out.println("Available packages:");
            for (Package pkg : PACKAGES) {
                System.out.printf("  %s%n", pkg.getCoordinate());
            }
            System.exit(1);
        }

        System.out.printf("\n=== Testing %s (version spec: %s) ===%n",
            targetPkg.getCoordinate(), targetPkg.versionRange);

        ExperimentResult result = testPackage(targetPkg);

        System.out.printf("\nResults for %s:%n", targetPkg.getCoordinate());
        System.out.printf("  Version spec: %s%n", result.versionSpec);
        System.out.printf("  Resolved version: %s%n", result.resolvedVersion != null ? result.resolvedVersion : "N/A");
        System.out.printf("  Oldest compatible: %s%n", result.oldestCompatible != null ? result.oldestCompatible : "N/A");
        System.out.printf("  Latest compatible: %s%n", result.latestCompatible != null ? result.latestCompatible : "N/A");

        // Write single result to a file.
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(result);
        String filename = String.format("result-%s.json", packageCoordinate.replace(":", "-"));
        Files.writeString(Paths.get(filename), json);
        System.out.printf("\n=== Result written to %s ===%n", filename);
    }

    // Test the control case with no dependencies.
    static ExperimentResult testControlCase() throws Exception {
        ExperimentResult result = new ExperimentResult("CONTROL", "none");

        String oldest = findOldestCompatible(null);
        result.oldestCompatible = oldest;
        result.latestCompatible = JAVA_VERSIONS[JAVA_VERSIONS.length - 1];

        return result;
    }

    // Test a single package.
    static ExperimentResult testPackage(Package pkg) throws Exception {
        ExperimentResult result = new ExperimentResult(pkg.getCoordinate(), pkg.versionRange);

        // Get resolved version with latest Java.
        String resolved = getResolvedVersion(pkg);
        result.resolvedVersion = resolved;

        // Find oldest compatible version.
        String oldest = findOldestCompatible(pkg);
        result.oldestCompatible = oldest;
        result.latestCompatible = JAVA_VERSIONS[JAVA_VERSIONS.length - 1];

        return result;
    }

    // Get the resolved version of a package with the latest Java.
    static String getResolvedVersion(Package pkg) throws Exception {
        Path tmpDir = Files.createTempDirectory("java-exp-");
        try {
            // Ensure latest Java version is installed.
            String latestVer = JAVA_VERSIONS[JAVA_VERSIONS.length - 1];
            if (!ensureJavaInstalled(latestVer)) {
                throw new Exception("Failed to install Java " + latestVer);
            }

            // Create pom.xml.
            createPomXml(tmpDir, pkg, getJavaVersionNumber(latestVer));

            // Run Maven to resolve dependencies.
            ProcessBuilder pb = new ProcessBuilder(
                "bash", "-c",
                String.format("source ~/.sdkman/bin/sdkman-init.sh && sdk use java %s && mvn dependency:resolve",
                    latestVer)
            );
            pb.directory(tmpDir.toFile());
            pb.redirectErrorStream(true);

            Process proc = pb.start();
            String output = new String(proc.getInputStream().readAllBytes());

            if (!proc.waitFor(60, TimeUnit.SECONDS) || proc.exitValue() != 0) {
                return null;
            }

            // Get resolved version from dependency tree.
            pb = new ProcessBuilder(
                "bash", "-c",
                String.format("source ~/.sdkman/bin/sdkman-init.sh && sdk use java %s && mvn dependency:tree",
                    latestVer)
            );
            pb.directory(tmpDir.toFile());
            pb.redirectErrorStream(true);

            proc = pb.start();
            output = new String(proc.getInputStream().readAllBytes());

            if (!proc.waitFor(60, TimeUnit.SECONDS) || proc.exitValue() != 0) {
                return null;
            }

            // Parse output to find resolved version.
            for (String line : output.split("\n")) {
                if (line.contains(pkg.groupId) && line.contains(pkg.artifactId)) {
                    // Format: [INFO] +- groupId:artifactId:jar:version:compile
                    String[] parts = line.split(":");
                    if (parts.length >= 4) {
                        return parts[3].trim();
                    }
                }
            }

            return null;
        } finally {
            deleteDirectory(tmpDir);
        }
    }

    // Find the oldest compatible Java version using binary search.
    static String findOldestCompatible(Package pkg) throws Exception {
        int left = 0;
        int right = JAVA_VERSIONS.length;
        String oldest = null;

        while (left < right) {
            int mid = left + (right - left) / 2;
            String version = JAVA_VERSIONS[mid];

            System.out.printf("  Testing Java %s%n", version);

            if (testJavaVersion(version, pkg)) {
                oldest = version;
                right = mid;
            } else {
                left = mid + 1;
            }
        }

        return oldest;
    }

    // Test if a package works with a specific Java version.
    static boolean testJavaVersion(String javaVersion, Package pkg) {
        try {
            // Ensure Java version is installed.
            if (!ensureJavaInstalled(javaVersion)) {
                return false;
            }

            Path tmpDir = Files.createTempDirectory("java-exp-");
            try {
                // Create pom.xml.
                createPomXml(tmpDir, pkg, getJavaVersionNumber(javaVersion));

                // Create a simple Main.java that uses the dependency.
                if (pkg != null) {
                    Path srcDir = tmpDir.resolve("src/main/java");
                    Files.createDirectories(srcDir);
                    String javaCode = "public class Main { public static void main(String[] args) {} }";
                    Files.writeString(srcDir.resolve("Main.java"), javaCode);
                } else {
                    // Control case.
                    Path srcDir = tmpDir.resolve("src/main/java");
                    Files.createDirectories(srcDir);
                    String javaCode = "public class Main { public static void main(String[] args) {} }";
                    Files.writeString(srcDir.resolve("Main.java"), javaCode);
                }

                // Run Maven compile.
                ProcessBuilder pb = new ProcessBuilder(
                    "bash", "-c",
                    String.format("source ~/.sdkman/bin/sdkman-init.sh && sdk use java %s && mvn compile",
                        javaVersion)
                );
                pb.directory(tmpDir.toFile());
                pb.redirectErrorStream(true);

                Process proc = pb.start();
                // Consume output to prevent blocking.
                proc.getInputStream().readAllBytes();

                return proc.waitFor(120, TimeUnit.SECONDS) && proc.exitValue() == 0;
            } finally {
                deleteDirectory(tmpDir);
            }
        } catch (Exception e) {
            return false;
        }
    }

    // Ensure a Java version is installed via SDKMAN.
    static boolean ensureJavaInstalled(String version) {
        try {
            // Check if already installed.
            ProcessBuilder pb = new ProcessBuilder(
                "bash", "-c",
                String.format("source ~/.sdkman/bin/sdkman-init.sh && sdk list java | grep -q 'installed.*%s'",
                    version)
            );
            Process proc = pb.start();
            if (proc.waitFor(10, TimeUnit.SECONDS) && proc.exitValue() == 0) {
                return true;
            }

            // Install the version.
            System.out.printf("    Installing Java %s...%n", version);
            pb = new ProcessBuilder(
                "bash", "-c",
                String.format("source ~/.sdkman/bin/sdkman-init.sh && sdk install java %s < /dev/null",
                    version)
            );
            proc = pb.start();
            // Consume output.
            proc.getInputStream().readAllBytes();
            proc.getErrorStream().readAllBytes();

            return proc.waitFor(300, TimeUnit.SECONDS) && proc.exitValue() == 0;
        } catch (Exception e) {
            System.out.printf("    Failed to install %s: %s%n", version, e.getMessage());
            return false;
        }
    }

    // Create a pom.xml file.
    static void createPomXml(Path dir, Package pkg, String javaVersion) throws IOException {
        StringBuilder pom = new StringBuilder();
        pom.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        pom.append("<project xmlns=\"http://maven.apache.org/POM/4.0.0\"\n");
        pom.append("         xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n");
        pom.append("         xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0\n");
        pom.append("         http://maven.apache.org/xsd/maven-4.0.0.xsd\">\n");
        pom.append("    <modelVersion>4.0.0</modelVersion>\n");
        pom.append("    <groupId>test</groupId>\n");
        pom.append("    <artifactId>test</artifactId>\n");
        pom.append("    <version>1.0-SNAPSHOT</version>\n");
        pom.append("    <properties>\n");
        pom.append("        <maven.compiler.source>").append(javaVersion).append("</maven.compiler.source>\n");
        pom.append("        <maven.compiler.target>").append(javaVersion).append("</maven.compiler.target>\n");
        pom.append("        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>\n");
        pom.append("    </properties>\n");

        if (pkg != null) {
            pom.append("    <dependencies>\n");
            pom.append("        <dependency>\n");
            pom.append("            <groupId>").append(pkg.groupId).append("</groupId>\n");
            pom.append("            <artifactId>").append(pkg.artifactId).append("</artifactId>\n");
            pom.append("            <version>").append(pkg.versionRange).append("</version>\n");
            pom.append("        </dependency>\n");
            pom.append("    </dependencies>\n");
        }

        pom.append("</project>\n");

        Files.writeString(dir.resolve("pom.xml"), pom.toString());
    }

    // Get Java version number from SDKMAN identifier (e.g., "8.0.432-tem" -> "8").
    static String getJavaVersionNumber(String sdkmanVersion) {
        return sdkmanVersion.split("\\.")[0];
    }

    // Delete a directory recursively.
    static void deleteDirectory(Path dir) throws IOException {
        if (Files.exists(dir)) {
            Files.walk(dir)
                .sorted(Comparator.reverseOrder())
                .forEach(path -> {
                    try {
                        Files.delete(path);
                    } catch (IOException e) {
                        // Ignore.
                    }
                });
        }
    }
}
