package app;

import e.g;
import e.t;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public final class WorldBuild {
    private static final int COLUMNS = 16;

    private WorldBuild() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) {
            System.err.println("WorldBuild <base-teams-dir> <plan.tsv> <roster-dir> <new-teams-dir>");
            System.exit(2);
        }
        Path base = Path.of(args[0]).toAbsolutePath().normalize();
        Path plan = Path.of(args[1]);
        Path rosters = Path.of(args[2]);
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        if (Files.exists(output) || output.startsWith(base)) throw new IllegalArgumentException("Output must be a new directory");
        Files.createDirectories(output);
        Set<String> seen = new HashSet<>();
        int replaced = 0, kept = 0, players = 0;
        for (String row : Files.readAllLines(plan, StandardCharsets.UTF_8)) {
            String[] v = row.split("\t", -1);
            if (v.length != COLUMNS) throw new IllegalArgumentException("Expected " + COLUMNS + " columns: " + row);
            String file = v[0];
            if (!file.matches("[\\p{L}\\p{N}_. -]{1,60}") || !seen.add(file.toLowerCase(Locale.ROOT)))
                throw new IllegalArgumentException("Invalid or duplicate team file: " + file);
            t team = Main.load(base.resolve(v[1]));
            team.d = file;
            team.a = Main.parseIntField(v[2], "country", 0, 223);
            team.b = Main.parseIntField(v[3], "state", 0, 255);
            team.c = Main.parseIntField(v[4], "level", 1, 20);
            team.n = Main.parseIntField(v[5], "reputation", 0, 5);
            team.id = Main.parseIntField(v[6], "id", 0, Integer.MAX_VALUE);
            team.e = text(v[7], "name", 40, team.e);
            team.f = text(v[8], "stadium", 60, team.f);
            team.g = Main.parseIntField(v[9], "capacity", 0, 250000);
            team.h = text(v[10], "manager", 60, team.h);
            team.i = Main.parseIntField(v[11], "manager country", 0, 223);
            team.cor1 = color(v[12], team.cor1);
            team.cor2 = color(v[13], team.cor2);
            if ("replace".equals(v[14])) {
                team.l = Main.readRoster(rosters.resolve(file + ".ban.tsv"));
                replaced++;
            } else if ("keep".equals(v[14])) {
                kept++;
            } else {
                throw new IllegalArgumentException("Unknown roster mode: " + v[14]);
            }
            if ("clear".equals(v[15])) {
                team.m = new ArrayList<g>();
            } else if (!"keep".equals(v[15])) {
                throw new IllegalArgumentException("Unknown juniors mode: " + v[15]);
            }
            team.valid = true;
            Main.shortenNames(team.l);
            Main.shortenNames(team.m);
            players += team.l == null ? 0 : team.l.size();
            Main.store(team, output.resolve(file + ".ban"));
        }
        System.out.println("{\"teams\":" + seen.size() + ",\"rostersReplaced\":" + replaced + ",\"rostersKept\":" + kept
                + ",\"players\":" + players + "}");
    }

    private static String text(String value, String label, int maximum, String fallback) {
        if (value.isEmpty()) return fallback;
        String decoded = new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8).strip();
        if (decoded.isEmpty() || decoded.length() > maximum) throw new IllegalArgumentException("Invalid " + label);
        return decoded;
    }

    private static String color(String value, String fallback) {
        if (value.isEmpty()) return fallback;
        if (!value.matches("#[0-9a-f]{6}")) throw new IllegalArgumentException("Invalid color " + value);
        return value;
    }
}
