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
import java.util.TreeMap;

public final class CountTeams {
    private CountTeams() {}

    public static void main(String[] args) throws Exception {
        TreeMap<Integer, int[]> countries = new TreeMap<>();
        TreeMap<Integer, int[]> states = new TreeMap<>();
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
                int[] count = countries.computeIfAbsent(team.a, k -> new int[2]);
                count[0]++;
                if (team.valid && team.vid == 185) count[1]++;
                if (team.a == 29 && team.valid && team.vid == 185) states.computeIfAbsent(team.b, k -> new int[1])[0]++;
            }
        }
        StringBuilder out = new StringBuilder("{\"countries\":{");
        boolean first = true;
        for (var e : countries.entrySet()) {
            if (!first) out.append(',');
            first = false;
            out.append('"').append(e.getKey()).append("\":[").append(e.getValue()[0]).append(',').append(e.getValue()[1]).append(']');
        }
        out.append("},\"brazilStates\":{");
        first = true;
        for (var e : states.entrySet()) {
            if (!first) out.append(',');
            first = false;
            out.append('"').append(e.getKey()).append("\":").append(e.getValue()[0]);
        }
        System.out.println(out.append("}}"));
    }
}
