package app;
import e.g;
import e.t;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Synthetic fixture. Never includes an original Brasfoot .ban. */
public final class RosterEditorSelfTest {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("brassfoot-roster-selftest");
        try {
            Path game = root.resolve("game");
            Files.createDirectories(game.resolve("teams"));
            Path source = game.resolve("teams/club.ban");
            Path roster = root.resolve("roster.tsv");
            Path output = root.resolve("result.ban");
            t team = new t();
            team.a = 29;
            team.id = 500;
            team.e = "Synthetic Team";
            team.l = new ArrayList<>();
            team.m = new ArrayList<>();
            for (int i = 0; i < 20; i++) {
                g player = new g();
                player.a = "Original " + i;
                player.tid = 900000 + i;
                player.e = i < 2 ? 0 : i < 6 ? 1 : i < 10 ? 2 : i < 16 ? 3 : 4;
                player.d = 23 + i%7;
                player.c = 29;
                player.g = 4;
                player.h = 7;
                player.hash = 5;
                team.l.add(player);
            }
            byte[] original = UpdateTeamRoster.serialize(team);
            Files.write(source, original);
            StringBuilder csv = new StringBuilder();
            for (int i = 0; i < 20; i++) {
                String name = i == 0 ? "Original 0" : "Real Verified " + i;
                csv.append(name).append('\t').append(i < 2 ? 0 : i < 6 ? 1 : i < 10 ? 2 : i < 16 ? 3 : 4)
                   .append("\t\t\n");
            }
            Files.writeString(roster, csv.toString(), StandardCharsets.UTF_8);
            String sha = UpdateTeamRoster.sha256(original);
            try {
                UpdateTeamRoster.main(new String[] {source.toString(), roster.toString(),
                    output.toString(), "0".repeat(64), "500", "--lab-estimates"});
                throw new AssertionError("Accepted wrong source SHA");
            } catch (java.io.IOException expected) {}
            try {
                UpdateTeamRoster.main(new String[] {source.toString(), roster.toString(),
                    output.toString(), sha, "500"});
                throw new AssertionError("Strict mode allowed estimated metadata");
            } catch (java.io.IOException expected) {}
            try {
                UpdateTeamRoster.main(new String[] {source.toString(), roster.toString(),
                    game.resolve("teams/unwanted.ban").toString(), sha, "500", "--lab-estimates"});
                throw new AssertionError("Allowed modification inside the game's teams folder");
            } catch (java.io.IOException expected) {}
            UpdateTeamRoster.main(new String[] {source.toString(), roster.toString(),
                output.toString(), sha, "500", "--lab-estimates"});
            t updated = UpdateTeamRoster.loadTeam(Files.readAllBytes(output));
            if (updated.l.size() != 20 || !updated.l.get(1).a.equals("Real Verified 1") ||
                updated.l.get(0).tid != team.l.get(0).tid ||
                !Arrays.equals(Files.readAllBytes(source), original)) {
                throw new AssertionError("Damaged original player identity or source bytes");
            }
            try {
                UpdateTeamRoster.main(new String[] {source.toString(), roster.toString(),
                    output.toString(), sha, "500", "--lab-estimates"});
                throw new AssertionError("Allowed overwriting an existing output");
            } catch (java.io.IOException expected) {}
            System.out.println("PASS synthetic SHA checks, strict mode, original preservation and guarded lab edit");
        } finally {
            try (var walk = Files.walk(root)) {
                for (Path path : walk.sorted(Comparator.reverseOrder()).toList())
                    Files.deleteIfExists(path);
            }
        }
    }
}
