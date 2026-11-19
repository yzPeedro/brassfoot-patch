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
    private static String[][] rules;
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
        rules = new String[args.length - 4][];
        for (int i = 4; i < args.length; i++) {
            String[] parts = args[i].split(":");
            rules[i - 4] = parts.length > 2 ? parts[2].split(",") : new String[0];
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
            for (int k = 0; k < sizes.length; k++) seasonEnd(year, sizes[k][0], rules[k]);
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

    private static void tableOrder(int year, int id, f.B division, int number) {
        f.s league = division.yi();
        ArrayList table = league.yK();
        boolean ok = true;
        for (int k = 0; k + 1 < table.size(); k++) {
            int[] p = ((ah) table.get(k)).d(league);
            int[] q = ((ah) table.get(k + 1)).d(league);
            int cmp = p[0] != q[0] ? q[0] - p[0] : p[7] != q[7] ? q[7] - p[7] : p[5] != q[5] ? q[5] - p[5] : q[2] - p[2];
            ok &= cmp <= 0;
        }
        check(ok, year + " pais " + id + " divisao " + number + " ordenada por pontos, saldo, gols pro e vitorias");
    }

    private static void sixTeam(int year, int id, f.B division, int number) throws Exception {
        java.lang.reflect.Field field = f.B.class.getDeclaredField("ZV");
        field.setAccessible(true);
        f.z eliminators = (f.z) field.get(division);
        ArrayList table = division.yi().yK();
        check(eliminators != null && eliminators.zp().size() == 1, year + " pais " + id + " divisao " + number + " com eliminatorias do playoff de seis");
        if (eliminators == null || eliminators.zp().isEmpty()) return;
        f.G round = (f.G) eliminators.zp().get(0);
        StringBuilder text = new StringBuilder();
        boolean ok = round.zW().size() == 2 && (round.zX() == null || round.zX().isEmpty());
        for (Object item : round.zW()) {
            I match = (I) item;
            int home = table.indexOf(match.hc()) + 1, away = table.indexOf(match.hd()) + 1;
            text.append(home).append('x').append(away).append(' ');
            ok &= home + away == 13 && home < away;
        }
        check(ok, year + " pais " + id + " eliminatorias " + text + "(5x8 e 6x7, jogo unico, mando do melhor)");
        f.z playoff = division.BR();
        check(playoff != null && playoff.zp().size() == 2, year + " pais " + id + " semifinais e final do playoff de seis");
        if (playoff == null || playoff.zp().isEmpty()) return;
        f.G semis = (f.G) playoff.zp().get(0);
        ArrayList winners = round.zY();
        int worst = Math.max(table.indexOf(winners.get(0)), table.indexOf(winners.get(1))) + 1;
        StringBuilder pairs = new StringBuilder();
        boolean semisOk = semis.zW().size() == 2 && semis.zX().size() == 2;
        for (int k = 0; k < semis.zW().size(); k++) {
            I match = (I) semis.zW().get(k);
            int home = table.indexOf(match.hc()) + 1, away = table.indexOf(match.hd()) + 1;
            pairs.append(home).append('x').append(away).append(' ');
            if (away == 3) semisOk &= home == worst;
            semisOk &= away == 3 || away == 4;
        }
        check(semisOk, year + " pais " + id + " semifinais " + pairs + "(3o recebe o vencedor de pior colocacao, volta na casa do melhor)");
        check(((f.G) playoff.zp().get(1)).zX() == null || ((f.G) playoff.zp().get(1)).zX().isEmpty(), year + " pais " + id + " final do playoff em jogo unico");
    }

    private static void seasonEnd(int year, int id, String[] rule) throws Exception {
        Z country = c.a.SR.o(id);
        ArrayList divisions = country.eb();
        for (int i = 0; i < divisions.size(); i++) {
            f.B division = (f.B) divisions.get(i);
            ah champion = ((at) division).cS();
            out.println(year + " pais " + id + " divisao " + (i + 1) + " campeao: " + (champion == null ? "nenhum" : champion.getNome()));
            check(champion != null, year + " pais " + id + " divisao " + (i + 1) + " com campeao");
            String kind = i < rule.length ? rule[i] : "";
            if (kind.equals("six")) {
                sixTeam(year, id, division, i + 1);
                tableOrder(year, id, division, i + 1);
                continue;
            }
            if (id == 97) tableOrder(year, id, division, i + 1);
            f.z playoff = division.BR();
            if (division.getVagasSobemPeloMataMata() <= 0 || id == 29 && i == 3 || kind.isEmpty() || kind.equals("-")) continue;
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
                ok &= kind.equals("vanilla") ? home < away : home > away;
            }
            if (!kind.equals("vanilla")) {
                for (Object item : first.zW()) {
                    I match = (I) item;
                    ok &= table.indexOf(match.hc()) + table.indexOf(match.hd()) + 2 == 2 * top + 3;
                }
            }
            check(ok, year + " pais " + id + " divisao " + (i + 1) + " playoff " + pairs + (kind.equals("vanilla") ? "(ordem original do jogo)" : "(pior em casa na ida)"));
        }
    }
}
