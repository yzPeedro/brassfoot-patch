package app;

import e.t;
import e.g;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class Main {
    private Main() { }

    private static t load(Path path) throws Exception {
        if (Files.size(path) > 1024 * 1024) throw new IOException(".ban exceeds maximum expected size: " + path);
        try (ObjectInputStream in = new ObjectInputStream(Files.newInputStream(path))) {
            // Deserialization allowlist: no classes other than those observed in team samples.
            in.setObjectInputFilter(info -> {
                Class<?> cls = info.serialClass();
                if (info.depth() > 50 || info.references() > 5000 || info.arrayLength() > 1000 || info.streamBytes() > 1000000) {
                    return ObjectInputFilter.Status.REJECTED;
                }
                if (cls == null) return ObjectInputFilter.Status.UNDECIDED;
                return cls == t.class || cls == g.class || cls == ArrayList.class || cls == String.class
                        || (cls.isArray() && cls.getComponentType() == Object.class)
                        ? ObjectInputFilter.Status.ALLOWED : ObjectInputFilter.Status.REJECTED;
            });
            Object result = in.readObject();
            if (!(result instanceof t)) throw new IOException("Expected e.t team object");
            if (in.read() != -1) throw new IOException("Trailing data after serialized team");
            return (t) result;
        }
    }

    private static void store(t team, Path path) throws IOException {
        if (path.getParent() != null) Files.createDirectories(path.getParent());
        if (Files.exists(path)) throw new FileAlreadyExistsException(path.toString());
        try (ObjectOutputStream out = new ObjectOutputStream(Files.newOutputStream(path, StandardOpenOption.CREATE_NEW))) {
            out.writeObject(team);
        }
    }

    private static byte[] encode(t team) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) { out.writeObject(team); }
        return bytes.toByteArray();
    }

    private static List<Path> teamFiles(Path dir) throws IOException {
        if (!Files.isDirectory(dir)) throw new NotDirectoryException(dir.toString());
        try (var list = Files.list(dir)) {
            return list.filter(Files::isRegularFile).filter(p -> p.getFileName().toString().endsWith(".ban"))
                    .sorted().toList();
        }
    }

    private static void auditDirectory(Path dir) throws Exception {
        List<Path> originals = teamFiles(dir);
        if (originals.isEmpty()) throw new IOException("No .ban files found in: " + dir);
        int ok = 0, failed = 0;
        for (Path path : originals) {
            try {
                byte[] original = Files.readAllBytes(path);
                byte[] roundtrip = encode(load(path));
                if (!Arrays.equals(original, roundtrip)) throw new IOException("Roundtrip differs from source");
                ok++;
            } catch (Exception failure) {
                failed++;
                System.err.println("FAILED: " + path.getFileName() + ": " + failure.getMessage());
            }
        }
        System.out.println("{\"examined\":" + originals.size() + ",\"exactRoundtrips\":" + ok + ",\"failed\":" + failed + "}");
        if (failed != 0) System.exit(1);
    }

    private static void exportDirectory(Path dir, Path out) throws Exception {
        List<Path> originals = teamFiles(dir);
        if (originals.isEmpty()) throw new IOException("No .ban files found in: " + dir);
        Files.createDirectories(out);
        if (!Files.isDirectory(out)) throw new IOException("Export output is not a directory");
        for (Path path : originals) {
            Path target = out.resolve(path.getFileName().toString() + ".json");
            if (Files.exists(target)) throw new FileAlreadyExistsException(target.toString());
        }
        for (Path path : originals) {
            Path target = out.resolve(path.getFileName().toString() + ".json");
            Files.writeString(target, json(load(path)) + "\n", StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
        System.out.println("{\"exported\":" + originals.size() + ",\"directory\":" + str(out.toAbsolutePath().toString()) + "}");
    }

    private static String str(String s) {
        if (s == null) return "null";
        StringBuilder sb = new StringBuilder("\"");
        for (char ch : s.toCharArray()) {
            switch (ch) {
                case '\\': sb.append("\\\\"); break;
                case '"': sb.append("\\\""); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default: if (ch < 0x20) sb.append(String.format("\\u%04x", (int)ch)); else sb.append(ch);
            }
        }
        return sb.append('"').toString();
    }

    private static String players(ArrayList<g> list) {
        if (list == null) return "null";
        StringJoiner result = new StringJoiner(",", "[", "]");
        for (g p : list) {
            result.add("{\"name\":" + str(p.a)
                    + ",\"aid\":" + p.aid + ",\"b\":" + p.b + ",\"c\":" + p.c
                    + ",\"d\":" + p.d + ",\"e\":" + p.e + ",\"f\":" + p.f
                    + ",\"g\":" + p.g + ",\"h\":" + p.h + ",\"hash\":" + p.hash
                    + ",\"i\":" + p.i + ",\"j\":" + p.j + ",\"sid\":" + p.sid
                    + ",\"tid\":" + p.tid + "}");
        }
        return result.toString();
    }

    private static String json(t team) {
        return "{\"name\":" + str(team.e) + ",\"id\":" + str(team.d) + ",\"stadium\":" + str(team.f)
                + ",\"manager\":" + str(team.h) + ",\"primaryColor\":" + str(team.cor1)
                + ",\"secondaryColor\":" + str(team.cor2)
                + ",\"a\":" + team.a + ",\"aid\":" + team.aid + ",\"b\":" + team.b
                + ",\"c\":" + team.c + ",\"g\":" + team.g + ",\"i\":" + team.i
                + ",\"internalId\":" + team.id + ",\"n\":" + team.n + ",\"o\":" + team.o
                + ",\"sid\":" + team.sid + ",\"tid\":" + team.tid + ",\"valid\":" + team.valid
                + ",\"vid\":" + team.vid + ",\"players\":" + players(team.l)
                + ",\"secondaryPlayers\":" + players(team.m) + "}";
    }

    private static int parseIntField(String value, String label, int min, int max) {
        int parsed;
        try { parsed = Integer.parseInt(value); }
        catch (NumberFormatException ex) { throw new IllegalArgumentException("Invalid " + label + ": " + value); }
        if (parsed < min || parsed > max) throw new IllegalArgumentException("Out of range " + label + ": " + parsed);
        return parsed;
    }

    /** Creates a .ban using an original club as a template and a full, typed roster.
     *  The tabular roster is an internal interchange generated by roster_to_tsv.py.
     *  This command does not overwrite source files or write to the game directory.
     */
    private static void replaceRoster(Path source, Path roster, Path destination) throws Exception {
        if (Files.exists(destination)) throw new FileAlreadyExistsException(destination.toString());
        t team = load(source);
        team.l = readRoster(roster);
        store(team, destination);
        System.out.println("{\"teamId\":" + str(team.d) + ",\"players\":" + team.l.size()
                + ",\"output\":" + str(destination.toAbsolutePath().toString()) + "}");
    }

    private static ArrayList<g> readRoster(Path roster) throws Exception {
        List<String> rows = Files.readAllLines(roster, StandardCharsets.UTF_8);
        if (rows.size() < 16 || rows.size() > 40)
            throw new IllegalArgumentException("Expected 16..40 roster players, got " + rows.size());
        ArrayList<g> replacement = new ArrayList<>();
        for (String row : rows) {
            String[] v = row.split("\t", -1);
            if (v.length != 14) throw new IllegalArgumentException("Expected 14 columns in roster row");
            g p = new g();
            p.a = new String(Base64.getDecoder().decode(v[0]), StandardCharsets.UTF_8);
            if (p.a.isBlank() || p.a.length() > 120) throw new IllegalArgumentException("Invalid player name");
            p.aid = parseIntField(v[1], "aid", 0, Integer.MAX_VALUE);
            p.b = Boolean.parseBoolean(v[2]);
            p.c = parseIntField(v[3], "c", 0, 223);
            p.d = parseIntField(v[4], "d", 0, 100);
            p.e = parseIntField(v[5], "e", 0, 4);
            p.f = parseIntField(v[6], "f", 0, 1);
            p.g = parseIntField(v[7], "g", 0, 13);
            p.h = parseIntField(v[8], "h", 0, 13);
            p.hash = parseIntField(v[9], "hash", 0, 10);
            p.i = parseIntField(v[10], "i", 0, 1);
            p.j = Boolean.parseBoolean(v[11]);
            p.sid = parseIntField(v[12], "sid", 0, Integer.MAX_VALUE);
            p.tid = parseIntField(v[13], "tid", 0, Integer.MAX_VALUE);
            replacement.add(p);
        }
        return replacement;
    }

    private static void shortenNames(ArrayList<g> players) {
        if (players == null) return;
        for (g player : players) {
            if (player.a == null) continue;
            String[] words = player.a.strip().split("\\s+");
            player.a = words.length > 2 ? words[0] + " " + words[1] : String.join(" ", words);
        }
    }

    /** One production compiler invocation; preserves every base team field and
     * secondary player field except the explicitly requested display-name rule. */
    private static void batchRosters(Path sourceDir, Path rosterDir, Path destinationDir) throws Exception {
        sourceDir = sourceDir.toAbsolutePath().normalize();
        rosterDir = rosterDir.toAbsolutePath().normalize();
        destinationDir = destinationDir.toAbsolutePath().normalize();
        if (destinationDir.startsWith(sourceDir) || sourceDir.startsWith(destinationDir)
                || destinationDir.startsWith(rosterDir) || Files.exists(destinationDir))
            throw new IOException("Batch destination must be new and separate from its inputs");
        List<Path> sources = teamFiles(sourceDir);
        Files.createDirectories(destinationDir);
        int updated = 0, players = 0;
        for (Path source : sources) {
            t team = load(source);
            Path roster = rosterDir.resolve(source.getFileName() + ".tsv");
            if (Files.isRegularFile(roster)) {
                team.l = readRoster(roster);
                updated++;
            }
            shortenNames(team.l);
            shortenNames(team.m);
            players += team.l == null ? 0 : team.l.size();
            store(team, destinationDir.resolve(source.getFileName()));
        }
        System.out.println("{\"teams\":" + sources.size() + ",\"rostersSupplied\":" + updated
                + ",\"players\":" + players + "}");
    }

    private static void usage() {
        System.err.println("Usage:");
        System.err.println("  inspect <original.ban>");
        System.err.println("  clone <original.ban> <new.ban>");
        System.err.println("  rename-player <original.ban> <old-name> <new-name> <new.ban>");
        System.err.println("  audit-directory <installation/teams>");
        System.err.println("  export-directory <installation/teams> <out-json-directory>");
        System.err.println("  replace-roster <original.ban> <roster.tsv> <new.ban>");
        System.err.println("  batch-rosters <base-teams-dir> <tsv-dir> <new-teams-dir>");
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {usage(); System.exit(2);}
        switch (args[0]) {
            case "batch-rosters": {
                if (args.length != 4) {usage(); System.exit(2);}
                batchRosters(Path.of(args[1]), Path.of(args[2]), Path.of(args[3]));
                break;
            }
            case "inspect": {
                if (args.length != 2) {usage(); System.exit(2);}
                System.out.println(json(load(Path.of(args[1]))));
                break;
            }
            case "clone": {
                if (args.length != 3) {usage(); System.exit(2);}
                t team = load(Path.of(args[1]));
                store(team, Path.of(args[2]));
                break;
            }
            case "rename-player": {
                if (args.length != 5) {usage(); System.exit(2);}
                t team = load(Path.of(args[1]));
                int hits = 0;
                for (g p : team.l) {
                    if (Objects.equals(p.a, args[2])) {
                        p.a = args[3];
                        hits++;
                    }
                }
                if (hits != 1) throw new IllegalArgumentException("Expected exactly one player matching '"+args[2]+"', found "+hits);
                store(team, Path.of(args[4]));
                break;
            }
            case "replace-roster": {
                if (args.length != 4) {usage(); System.exit(2);}
                replaceRoster(Path.of(args[1]), Path.of(args[2]), Path.of(args[3]));
                break;
            }
            case "audit-directory": {
                if (args.length != 2) {usage(); System.exit(2);}
                auditDirectory(Path.of(args[1]));
                break;
            }
            case "export-directory": {
                if (args.length != 3) {usage(); System.exit(2);}
                exportDirectory(Path.of(args[1]), Path.of(args[2]));
                break;
            }
            default: usage(); System.exit(2);
        }
    }
}
