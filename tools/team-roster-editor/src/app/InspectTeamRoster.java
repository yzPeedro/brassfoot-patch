package app;
import e.t;
import java.nio.file.*;

/** Safely print V4 internal team identity and player count; no original bytes exposed. */
public final class InspectTeamRoster {
    private InspectTeamRoster(){}
    public static void main(String[] args) throws Exception {
        if(args.length != 1) throw new IllegalArgumentException("TEAM.ban");
        t team=UpdateTeamRoster.loadTeam(Files.readAllBytes(Path.of(args[0])));
        long keepers=team.l.stream().filter(p->p.e==0).count();
        System.out.printf("ID=%d PLAYERS=%d GOALKEEPERS=%d NAME=%s%n",
          team.id,team.l.size(),keepers,team.e);
    }
}
