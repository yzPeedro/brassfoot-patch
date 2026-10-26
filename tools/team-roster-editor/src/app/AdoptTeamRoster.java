package app;
import e.g;
import e.t;
import java.nio.file.*;
import java.util.ArrayList;

/** Offline V4 lab utility: copy experimental A roster into same-club V4 file.
 * Keeps V4 team identity, division settings and remaining serialized fields.
 * Never writes inside input installation; caller must provide fresh output.
 */
public final class AdoptTeamRoster {
    private AdoptTeamRoster(){}
    public static void main(String[] args) throws Exception {
        if(args.length != 3) throw new IllegalArgumentException("V4-TEAM.ban DONOR-TEAM.ban OUTPUT.ban");
        Path source=Path.of(args[0]).toAbsolutePath().normalize();
        Path donorPath=Path.of(args[1]).toAbsolutePath().normalize();
        Path out=Path.of(args[2]).toAbsolutePath().normalize();
        if(Files.exists(out) || out.equals(source) || out.equals(donorPath) ||
           !Files.isDirectory(out.getParent()))
            throw new IllegalArgumentException("Output must be a new separate file");
        t base=UpdateTeamRoster.loadTeam(Files.readAllBytes(source));
        t donor=UpdateTeamRoster.loadTeam(Files.readAllBytes(donorPath));
        if(base.id!=donor.id || base.a!=donor.a || !base.e.equals(donor.e) ||
           donor.l.size()<18 || donor.l.size()>40)
            throw new IllegalArgumentException("Incompatible original / V4 team identity");
        base.l=new ArrayList<g>(donor.l);
        byte[] result=UpdateTeamRoster.serialize(base);
        t check=UpdateTeamRoster.loadTeam(result);
        if(check.l.size()!=donor.l.size() || check.id!=base.id || !check.e.equals(base.e))
            throw new IllegalStateException("Transplanted roster did not serialize correctly");
        Files.write(out,result,StandardOpenOption.CREATE_NEW);
        System.out.printf("ADOPTED_TEAM_ID=%d PLAYERS=%d OUTPUT_SHA256=%s%n",
          base.id,check.l.size(),UpdateTeamRoster.sha256(result));
    }
}
