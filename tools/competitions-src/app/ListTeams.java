package app;

import e.t;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;

public final class ListTeams {
    private ListTeams() {}

    private static String q(String s) {
        if (s == null) return "null";
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("TEAMS_DIRECTORY");
        StringBuilder out = new StringBuilder("[");
        boolean first = true;
        try (DirectoryStream<Path> files = Files.newDirectoryStream(Path.of(args[0]), "*.ban")) {
            for (Path file : files) {
                t team;
                try {
                    team = UpdateTeamRoster.loadTeam(Files.readAllBytes(file));
                } catch (java.io.IOException skipped) {
                    continue;
                }
                if (!first) out.append(",\n");
                first = false;
                out.append("{\"file\":").append(q(file.getFileName().toString()))
                   .append(",\"id\":").append(team.id).append(",\"a\":").append(team.a)
                   .append(",\"b\":").append(team.b).append(",\"c\":").append(team.c)
                   .append(",\"g\":").append(team.g).append(",\"i\":").append(team.i)
                   .append(",\"n\":").append(team.n).append(",\"o\":").append(team.o)
                   .append(",\"aid\":").append(team.aid).append(",\"sid\":").append(team.sid)
                   .append(",\"tid\":").append(team.tid).append(",\"vid\":").append(team.vid)
                   .append(",\"d\":").append(q(team.d)).append(",\"e\":").append(q(team.e))
                   .append(",\"f\":").append(q(team.f)).append(",\"h\":").append(q(team.h))
                   .append(",\"players\":").append(team.l == null ? 0 : team.l.size()).append('}');
            }
        }
        System.out.println(out.append("]"));
    }
}
