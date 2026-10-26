package app;

import e.g;
import e.t;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.file.*;
import java.util.*;

/** Synthetic-only regression for the original-team metadata reader. */
public final class OriginalBrazilDivisionProbeSelfTest {
    private OriginalBrazilDivisionProbeSelfTest() {}
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("brassfoot-division-probe-test");
        try {
            Path teams = Files.createDirectory(root.resolve("teams"));
            Map<Path, byte[]> originals = new LinkedHashMap<>();
            for (int i = 0; i < 55; i++) {
                t club = new t();
                club.a = 29;
                club.id = 1000 + i;
                club.b = i % 3 + 1;
                club.e = "Synthetic " + i;
                club.l = new ArrayList<>();
                club.m = new ArrayList<>();
                g player = new g();
                player.a = "Synthetic player";
                player.e = 0;
                club.l.add(player);
                byte[] original = UpdateTeamRoster.serialize(club);
                Path file = teams.resolve("fixture" + i + ".ban");
                Files.write(file, original);
                originals.put(file, original);
            }
            ByteArrayOutputStream captured = new ByteArrayOutputStream();
            PrintStream previous = System.out;
            try {
                System.setOut(new PrintStream(captured, true, "UTF-8"));
                OriginalBrazilDivisionProbe.main(new String[]{teams.toString()});
            } finally {
                System.setOut(previous);
            }
            String result = captured.toString("UTF-8");
            if (!result.contains("brazilian=55") ||
                    !result.contains("BRA_TEAM filename=fixture0.ban") ||
                    result.lines().filter(line -> line.startsWith("BRA_TEAM")).count() != 55)
                throw new AssertionError("Read-only metadata audit incomplete");
            for (var entry : originals.entrySet()) {
                if (!Arrays.equals(entry.getValue(), Files.readAllBytes(entry.getKey())))
                    throw new AssertionError("Read-only audit modified a source team");
            }
            System.out.println("PASS: 55 synthetic Brazil teams read without mutation");
        } finally {
            try (var walk = Files.walk(root)) {
                for (Path path : walk.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(path);
            }
        }
    }
}
