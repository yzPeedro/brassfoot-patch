package app;

import e.g;
import e.t;
import java.io.ByteArrayInputStream;
import java.io.ObjectInputFilter;
import java.io.ObjectInputStream;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public final class ListCountryTeams {
    private ListCountryTeams() {}

    private static String q(String s) {
        return s == null ? "null" : "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }

    public static void main(String[] args) throws Exception {
        Set<Integer> countries = new HashSet<>();
        for (int i = 1; i < args.length; i++) countries.add(Integer.parseInt(args[i]));
        StringBuilder out = new StringBuilder("[");
        boolean first = true;
        try (DirectoryStream<Path> files = Files.newDirectoryStream(Path.of(args[0]), "*.ban")) {
            for (Path file : files) {
                t team;
                try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(Files.readAllBytes(file)))) {
                    in.setObjectInputFilter(info -> {
                        Class<?> kind = info.serialClass();
                        if (kind == null || kind == t.class || kind == g.class || kind == ArrayList.class
                                || kind == String.class || kind == Object[].class) return ObjectInputFilter.Status.ALLOWED;
                        return ObjectInputFilter.Status.REJECTED;
                    });
                    team = (t) in.readObject();
                } catch (Exception skipped) {
                    continue;
                }
                if (!countries.isEmpty() && !countries.contains(team.a)) continue;
                if (!first) out.append(",\n");
                first = false;
                out.append("{\"file\":").append(q(file.getFileName().toString())).append(",\"a\":").append(team.a)
                   .append(",\"b\":").append(team.b).append(",\"c\":").append(team.c).append(",\"n\":").append(team.n)
                   .append(",\"g\":").append(team.g).append(",\"i\":").append(team.i).append(",\"vid\":").append(team.vid)
                   .append(",\"valid\":").append(team.valid).append(",\"d\":").append(q(team.d)).append(",\"e\":").append(q(team.e))
                   .append(",\"f\":").append(q(team.f)).append(",\"players\":").append(team.l == null ? 0 : team.l.size()).append('}');
            }
        }
        System.out.println(out.append("]"));
    }
}
