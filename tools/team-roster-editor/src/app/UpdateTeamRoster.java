package app;

import e.g;
import e.t;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.text.Normalizer;
import java.util.*;

/** Offline editor for legitimate local Brasfoot 22-23 .ban files. Never distributes originals. */
public final class UpdateTeamRoster {
    private UpdateTeamRoster() {}

    public static String sha256(byte[] bytes) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder out = new StringBuilder();
        for (byte b : hash) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }

    public static String normalize(String value) {
        return Normalizer.normalize(value, Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "").replaceAll("[^\\p{Alnum}]", "")
                .toLowerCase(Locale.ROOT);
    }

    public record Player(String name, int position, Integer age, Integer country) {}
    public record Report(int total, int reused, int estimatedAge, int estimatedCountry, int estimatedRatings) {}

    public static List<Player> loadPlayers(Path roster) throws IOException {
        List<Player> result = new ArrayList<>();
        Set<String> unique = new HashSet<>();
        int lineNumber = 0;
        for (String line : Files.readAllLines(roster, StandardCharsets.UTF_8)) {
            lineNumber++;
            if (line.isBlank() || line.startsWith("#")) continue;
            String[] parts = line.split("\t", -1);
            if (parts.length != 4) throw new IOException("Expected 4 TSV fields at line " + lineNumber);
            String name = parts[0].strip();
            if (name.isEmpty() || name.length() > 80 || name.contains("?") ||
                !unique.add(normalize(name))) throw new IOException("Invalid/duplicate player: line " + lineNumber);
            int position = Integer.parseInt(parts[1]);
            Integer age = parts[2].isBlank() ? null : Integer.valueOf(parts[2]);
            Integer country = parts[3].isBlank() ? null : Integer.valueOf(parts[3]);
            if (position < 0 || position > 4 || (age != null && (age < 15 || age > 49)) ||
                (country != null && (country < 1 || country > 250))) throw new IOException("Unsupported metadata at line " + lineNumber);
            result.add(new Player(name, position, age, country));
        }
        if (result.size() < 18 || result.size() > 40 ||
            result.stream().filter(p -> p.position() == 0).count() < 2)
            throw new IOException("Require 18..40 identified players with at least 2 goalkeepers");
        return result;
    }

    public static t loadTeam(byte[] bytes) throws Exception {
        if (bytes.length < 50 || bytes.length > 1_000_000 ||
            bytes[0] != (byte) 0xac || bytes[1] != (byte) 0xed)
            throw new IOException("Unsupported Java team data");
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            in.setObjectInputFilter(info -> {
                if (info.depth() > 32 || info.references() > 1024 ||
                    info.arrayLength() > 128 || info.streamBytes() > 1_000_000)
                    return ObjectInputFilter.Status.REJECTED;
                Class<?> kind = info.serialClass();
                if (kind == null) return ObjectInputFilter.Status.UNDECIDED;
                if (kind == t.class || kind == g.class || kind == ArrayList.class ||
                    kind == String.class || kind == Object[].class)
                    return ObjectInputFilter.Status.ALLOWED;
                return ObjectInputFilter.Status.REJECTED;
            });
            Object value = in.readObject();
            if (!(value instanceof t team) || in.read() != -1 || team.l == null ||
                team.a != 29 || team.l.isEmpty()) throw new IOException("Unexpected team type or country");
            return team;
        }
    }

    public static byte[] serialize(t team) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(team);
        }
        return bytes.toByteArray();
    }

    private static g create(Player row, t team, int serial, int namespace, List<g> existing) {
        g base = existing.stream().filter(p -> p.e == row.position()).findFirst().orElse(existing.get(0));
        g player = new g();
        player.a = row.name();
        player.tid = 200_000_000 + namespace * 100 + serial;
        player.d = row.age() != null ? row.age() : 25;
        player.e = row.position();
        player.c = row.country() != null ? row.country() : 29;
        player.f = base.f;
        player.g = base.g;
        player.h = base.h;
        player.hash = base.hash;
        player.i = base.i;
        return player;
    }

    public static Report update(t team, List<Player> rows, boolean labEstimates, int namespace) throws IOException {
        List<g> original = new ArrayList<>(team.l);
        Map<String, g> oldByName = new HashMap<>();
        for (g player : original) if (player.a != null)
            oldByName.putIfAbsent(normalize(player.a), player);
        ArrayList<g> newRoster = new ArrayList<>();
        Set<Integer> ids = new HashSet<>();
        int reused = 0, estimatedAges = 0, estimatedCountries = 0, estimatedRatings = 0;
        int serial = 1;
        for (Player row : rows) {
            g old = oldByName.get(normalize(row.name()));
            g player = create(row, team, serial, namespace, original);
            if (old != null) {
                player.tid = old.tid;
                player.aid = old.aid;
                player.sid = old.sid;
                player.f = old.f;
                player.g = old.g;
                player.h = old.h;
                player.hash = old.hash;
                player.i = old.i;
                player.d = row.age() != null ? row.age() : Math.min(49, old.d + 4);
                player.c = row.country() != null ? row.country() : old.c;
                reused++;
            } else {
                estimatedRatings++;
                if (row.age() == null) estimatedAges++;
                if (row.country() == null) estimatedCountries++;
            }
            player.a = row.name();
            player.e = row.position();
            if (!ids.add(player.tid)) throw new IOException("Duplicate numeric player ID");
            newRoster.add(player);
            serial++;
        }
        if (!labEstimates && (estimatedRatings > 0 || estimatedAges > 0 || estimatedCountries > 0))
            throw new IOException("Strict mode rejected unverified attributes. Use --lab-estimates only for isolated testing.");
        team.l = newRoster;
        return new Report(newRoster.size(), reused, estimatedAges, estimatedCountries, estimatedRatings);
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 6)
            throw new IllegalArgumentException("INPUT.ban ROSTER.tsv OUTPUT.ban APPROVED_SHA256 TEAM_ID [--lab-estimates]");
        boolean lab = args.length == 6 && args[5].equals("--lab-estimates");
        if (args.length == 6 && !lab) throw new IllegalArgumentException("Unknown option");
        Path input = Path.of(args[0]).toAbsolutePath().normalize();
        Path roster = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (input.equals(output) || roster.equals(output) || Files.exists(output) ||
            !Files.isDirectory(output.getParent()))
            throw new IOException("Output must be a new file outside the inputs");
        if (input.getParent() != null && input.getParent().getFileName().toString().equalsIgnoreCase("teams") &&
            output.startsWith(input.getParent().getParent()))
            throw new IOException("Refusing to write into a game installation");
        byte[] original = Files.readAllBytes(input);
        if (!sha256(original).equalsIgnoreCase(args[3])) throw new IOException("Original SHA-256 not approved");
        t team = loadTeam(original);
        int teamId = Integer.parseInt(args[4]);
        if (team.id != teamId) throw new IOException("Unexpected internal team ID");
        if (!Arrays.equals(serialize(team), original)) throw new IOException("Original does not round-trip byte for byte");
        // A number of legitimate original 2022-23 Brazilian clubs have internal ID=0.
        // Derive a stable, source-hash-scoped namespace for synthetic player IDs
        // rather than reusing 0 across different clubs. This is NOT proof that
        // the game's league selector knows which division the club belongs to.
        int namespace = (int) (Long.parseLong(sha256(original).substring(0, 7), 16) % 1_000_000);
        Report report = update(team, loadPlayers(roster), lab, namespace);
        byte[] result = serialize(team);
        t verified = loadTeam(result);
        if (verified.l.size() != report.total()) throw new IOException("Serialized roster invalid");
        List<Player> expectedPlayers=loadPlayers(roster);
        for (int i=0;i<report.total();i++) {
            Player expected=expectedPlayers.get(i);
            g actual=verified.l.get(i);
            if (!expected.name().equals(actual.a) || actual.e!=expected.position())
                throw new IOException("Serialized player name/position mismatched at index " + i);
        }
        Files.write(output, result, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.printf("TEAM=%d PLAYERS=%d REUSED=%d ESTIMATED_AGE=%d ESTIMATED_COUNTRY=%d ESTIMATED_RATINGS=%d%n",
            teamId, report.total(), report.reused(), report.estimatedAge(), report.estimatedCountry(), report.estimatedRatings());
        System.out.println("SOURCE_SHA256=" + sha256(original) + " TARGET_SHA256=" + sha256(result));
        System.out.println("Local experiment only: does not prove game compatibility.");
    }
}
