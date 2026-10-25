package app;
import est.ArrayLigaType;
import est.ArrayLigaEType;
import est.ConfigLigaType;
import est.ConfigEstadualType;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;

/** Synthetic fixtures only: no proprietary game files committed to the repository. */
public final class CodecSelfTest {
    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory("competition-codec-test-");
        try {
            ArrayLigaType leagues = new ArrayLigaType();
            leagues.a = new ArrayList<>();
            for (int i=0; i<4; i++) {
                ConfigLigaType d = new ConfigLigaType();
                d.divisao=i+1; d.nTimes=i==3?64:20; d.nGrupos=i==3?8:0;
                d.pais=29; d.versaoArquivo=22;
                d.nome="Teste"; d.nomeDivisao="Série "+ "ABCD".charAt(i);
                d.duasVoltasMataMata = new boolean[7];
                d.duasVoltasMataMataSobe = new boolean[3];
                d.duasVoltasplayoffReb = new boolean[3];
                leagues.a.add(d);
            }
            Path source = directory.resolve("BRA.cfg");
            try(ObjectOutputStream out = new ObjectOutputStream(Files.newOutputStream(source))) {
                out.writeObject(leagues);
            }
            Path roundtrip=directory.resolve("roundtrip.cfg");
            CompetitionCodec.main(new String[]{"roundtrip",source.toString(),roundtrip.toString()});
            if (!Arrays.equals(Files.readAllBytes(source),Files.readAllBytes(roundtrip))) {
                throw new AssertionError("National roundtrip changed the bytes");
            }
            Path trial=directory.resolve("candidate.cfg");
            CompetitionCodec.main(new String[]{"trial-serie-d-96",source.toString(),trial.toString()});
            if (Files.size(source)!=Files.size(trial)) throw new AssertionError("Trial changed length");

            ArrayLigaEType state = new ArrayLigaEType();
            state.a = new ArrayList<>();
            for (int i=1; i<=4; i++) {
                ConfigEstadualType c = new ConfigEstadualType();
                c.divisao=i; c.id=10; c.nRebaixados=2; c.finaisIdaVolta=new int[]{2,2,2};
                state.a.add(c);
            }
            Path stateFile=directory.resolve("MG.ces");
            try(ObjectOutputStream out=new ObjectOutputStream(Files.newOutputStream(stateFile))) {
                out.writeObject(state);
            }
            CompetitionCodec.main(new String[]{"roundtrip",stateFile.toString(),directory.resolve("MG-output.ces").toString()});
            try {
                CompetitionCodec.main(new String[]{"trial-serie-d-96",stateFile.toString(),directory.resolve("forbidden.cfg").toString()});
                throw new AssertionError("Trial accepted non-BRA file");
            } catch (IOException expected) { }
            try {
                CompetitionCodec.main(new String[]{"roundtrip",source.toString(),source.toString()});
                throw new AssertionError("Original could be overwritten");
            } catch (IOException expected) { }
            System.out.println("PASS synthetic national/state codec, roundtrip, size safety and path guards");
        } finally {
            try(var paths=Files.walk(directory)) {
                paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                    try { Files.deleteIfExists(path); }
                    catch(IOException e) { throw new UncheckedIOException(e); }
                });
            }
        }
    }
}
