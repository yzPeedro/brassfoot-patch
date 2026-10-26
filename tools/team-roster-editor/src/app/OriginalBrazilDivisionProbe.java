package app;

import e.t;
import java.nio.file.*;
import java.util.*;

/**
 * Read-only forensic inventory of Brazil's original .ban team metadata.
 * Never serializes, writes back, or includes the original licensed file bytes.
 */
public final class OriginalBrazilDivisionProbe {
    private OriginalBrazilDivisionProbe() {}
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: OriginalBrazilDivisionProbe GAME_TEAMS_DIRECTORY");
        Path teams = Path.of(args[0]).toRealPath();
        if (!Files.isDirectory(teams) || !"teams".equalsIgnoreCase(teams.getFileName().toString()))
            throw new IllegalArgumentException("Require original teams/ directory");
        List<String> names = new ArrayList<>();
        int brazilian = 0, examined = 0, rejected = 0;
        try (var files = Files.list(teams)) {
            for (Path entry : files.sorted().toList()) {
                if (!Files.isRegularFile(entry, LinkOption.NOFOLLOW_LINKS)
                        || !entry.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(".ban"))
                    continue;
                examined++;
                if (Files.size(entry) > 1_000_000) { rejected++; continue; }
                try {
                    t club = UpdateTeamRoster.loadTeam(Files.readAllBytes(entry));
                    if (club.a != 29) continue;
                    brazilian++;
                    // Numeric metadata only. Name and original player lists are not printed.
                    String line = String.format(Locale.ROOT,
                        "BRA_TEAM filename=%s id=%d aid=%d sid=%d tid=%d vid=%d a=%d b=%d c=%d g=%d i=%d n=%d o=%d valid=%s players=%d",
                        entry.getFileName(), club.id, club.aid, club.sid, club.tid,
                        club.vid, club.a, club.b, club.c, club.g, club.i, club.n,
                        club.o, club.valid, club.l.size());
                    names.add(line);
                } catch (Exception unsupported) {
                    // Foreign-country files and unsupported serializations are not modified.
                    rejected++;
                }
            }
        }
        Collections.sort(names);
        System.out.printf("BRA_PROBE summary examined=%d brazilian=%d skipped=%d readonly=true%n",
                examined, brazilian, rejected);
        if (examined < 50 || brazilian < 50)
            throw new IllegalStateException("Brazil club metadata insufficient for interpretation");
        for (String line : names) System.out.println(line);
        System.out.println("BRA_PROBE evidence only; field meaning and competition gameplay not yet verified");
    }
}
