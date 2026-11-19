import best.I;
import best.O;
import best.Z;
import best.ah;
import best.at;
import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

public final class CountryHarness {
    private static PrintStream out;
    private static int failures;

    private static void check(boolean condition, String label) {
        out.println((condition ? "OK   " : "FALHA ") + label);
        if (!condition) failures++;
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", CompHarness.MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        int seasons = Integer.parseInt(args[1]);
        int startYear = Integer.parseInt(args[2]);
        Set<Integer> countries = new HashSet<Integer>();
        for (String id : args[3].split(",")) countries.add(Integer.valueOf(id));
        int[][] sizes = new int[args.length - 4][];
        for (int i = 4; i < args.length; i++) {
            String[] parts = args[i].split(":");
            String[] values = parts[1].split(",");
            sizes[i - 4] = new int[values.length + 1];
            sizes[i - 4][0] = Integer.parseInt(parts[0]);
            for (int k = 0; k < values.length; k++) sizes[i - 4][k + 1] = Integer.parseInt(values[k]);
        }
        System.setProperty("user.dir", game.getPath());
        out = System.out;
        System.setOut(new PrintStream(new FileOutputStream(new File(game, "harness-game-stdout.log")), true, "UTF-8"));
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
        Set<Integer> listed = new HashSet<Integer>();
        for (Object item : c.a.SR.bF) {
            O option = (O) item;
            listed.add(option.getPais());
            option.v(countries.contains(option.getPais()));
        }
        check(listed.containsAll(countries), "paises pedidos aparecem na lista inicial: " + countries + " em " + listed);
        c.a.SR.I(startYear);
        c.a.SR.setJogaEstadual(true);
        c.a.SR.setJogaIntClubes(false);
        c.a.SR.setJogaSelecoesAll(false);
        best.p.dg();
        best.p.dh();
        c.a.SR.az();
        for (int season = 0; season < seasons; season++) {
            int year = c.a.SR.op() + c.a.SR.H() - 1;
            for (int[] expected : sizes) {
                divisions("criacao " + year, expected);
                if (season == 0) members(expected[0]);
            }
            int steps = 0;
            while (!c.a.SR.bk && steps < 5000) {
                c.a.SR.V();
                steps++;
            }
            check(c.a.SR.bk, year + ": temporada terminou em " + steps + " passos");
            for (int[] expected : sizes) seasonEnd(year, expected[0]);
            c.a.SR.V();
        }
        out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }

    private static void members(int id) throws Exception {
        PrintStream file = new PrintStream(new FileOutputStream(new File(System.getProperty("user.dir"), "members-" + id + ".tsv")), true, "UTF-8");
        ArrayList divisions = c.a.SR.o(id).eb();
        for (int i = 0; i < divisions.size(); i++) {
            for (Object team : ((f.B) divisions.get(i)).yi().yK()) file.println((i + 1) + "	" + ((ah) team).jY());
        }
        file.close();
    }

    private static void divisions(String label, int[] expected) {
        Z country = c.a.SR.o(expected[0]);
        ArrayList divisions = country.eb();
        StringBuilder text = new StringBuilder();
        boolean ok = divisions.size() == expected.length - 1;
        for (int i = 0; i < divisions.size(); i++) {
            int size = ((f.B) divisions.get(i)).yi().yK().size();
            text.append(size).append(' ');
            ok &= i + 1 < expected.length && size == expected[i + 1];
        }
        check(ok, label + " pais " + expected[0] + ": divisoes " + text);
    }

    private static void seasonEnd(int year, int id) {
        Z country = c.a.SR.o(id);
        ArrayList divisions = country.eb();
        for (int i = 0; i < divisions.size(); i++) {
            f.B division = (f.B) divisions.get(i);
            ah champion = ((at) division).cS();
            out.println(year + " pais " + id + " divisao " + (i + 1) + " campeao: " + (champion == null ? "nenhum" : champion.getNome()));
            check(champion != null, year + " pais " + id + " divisao " + (i + 1) + " com campeao");
            f.z playoff = division.BR();
            if (division.getVagasSobemPeloMataMata() <= 0 || id == 29 && i == 3) continue;
            check(playoff != null && !playoff.zp().isEmpty(), year + " pais " + id + " divisao " + (i + 1) + " com playoff de acesso");
            if (playoff == null || playoff.zp().isEmpty()) continue;
            f.G first = (f.G) playoff.zp().get(0);
            ArrayList table = division.yi().yK();
            StringBuilder pairs = new StringBuilder();
            boolean ok = first.zW().size() == 2;
            int top = Integer.MAX_VALUE;
            for (Object item : first.zW()) {
                I match = (I) item;
                int home = table.indexOf(match.hc()) + 1;
                int away = table.indexOf(match.hd()) + 1;
                top = Math.min(top, away);
                pairs.append(home).append("x").append(away).append(' ');
                ok &= home > away;
            }
            for (Object item : first.zW()) {
                I match = (I) item;
                ok &= table.indexOf(match.hc()) + table.indexOf(match.hd()) + 2 == 2 * top + 3;
            }
            check(ok, year + " pais " + id + " divisao " + (i + 1) + " playoff " + pairs + "(pior em casa na ida)");
        }
    }
}
