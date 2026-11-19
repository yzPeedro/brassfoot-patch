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
        boolean any = expected.length == 2 && expected[1] == 0;
        boolean ok = any ? divisions.size() > 0 : divisions.size() == expected.length - 1;
        for (int i = 0; i < divisions.size(); i++) {
            int size = ((f.B) divisions.get(i)).yi().yK().size();
            text.append(size).append(' ');
            ok &= any ? size > 0 : i + 1 < expected.length && size == expected[i + 1];
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

    private static String ties(ArrayList table, f.G round) {
        StringBuilder text = new StringBuilder();
        for (int t = 0; t < round.zW().size(); t++) {
            I first = (I) round.zW().get(t);
            text.append(table.indexOf(first.hc()) + 1).append('x').append(table.indexOf(first.hd()) + 1)
                    .append(' ').append(first.hu()).append('-').append(first.hw());
            if (round.zX() != null && t < round.zX().size()) {
                I second = (I) round.zX().get(t);
                text.append('/').append(second.hu()).append('-').append(second.hw());
            }
            text.append("; ");
        }
        StringBuilder winners = new StringBuilder();
        for (Object team : round.zY()) winners.append(table.indexOf(team) + 1).append(' ');
        return text + "-> " + winners;
    }

    private static Object field(Object target, String name) throws Exception {
        java.lang.reflect.Field field = target.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(target);
    }

    private static void italyB(int year, f.B division) throws Exception {
        ArrayList table = division.yi().yK();
        f.z eliminators = (f.z) field(division, "ZV");
        f.z playoff = division.BR();
        f.z playout = (f.z) field(division, "agB");
        int third = ((ah) table.get(2)).d(division.yi())[0];
        int fourth = ((ah) table.get(3)).d(division.yi())[0];
        if (third - fourth > 14) {
            out.println(year + " Serie B: 3o sobe direto (" + third + " x " + fourth + " pontos)");
        } else {
            boolean ok = eliminators != null && !eliminators.zp().isEmpty();
            String text = ok ? ties(table, (f.G) eliminators.zp().get(0)) : "";
            if (ok) {
                f.G first = (f.G) eliminators.zp().get(0);
                I a = (I) first.zW().get(0);
                I b = (I) first.zW().get(1);
                ok = table.indexOf(a.hc()) == 4 && table.indexOf(a.hd()) == 7 && table.indexOf(b.hc()) == 5 && table.indexOf(b.hd()) == 6;
                for (int t = 0; t < 2; t++) {
                    I match = (I) first.zW().get(t);
                    if (match.hu() == match.hw()) ok &= first.zY().contains(match.hc());
                }
            }
            check(ok, year + " Serie B eliminatorias 5x8 e 6x7, empate classifica o mandante: " + text);
            boolean semis = playoff != null && playoff.zp().size() == 2;
            String semiText = playoff != null && !playoff.zp().isEmpty() ? ties(table, (f.G) playoff.zp().get(0)) : "";
            if (semis) {
                f.G first = (f.G) playoff.zp().get(0);
                semis = table.indexOf(((I) first.zW().get(0)).hd()) == 2 && table.indexOf(((I) first.zW().get(1)).hd()) == 3;
            }
            check(semis, year + " Serie B semifinais com o 3o e o 4o mandando a volta: " + semiText
                    + (playoff != null && playoff.zp().size() > 1 ? " | final " + ties(table, (f.G) playoff.zp().get(1)) : ""));
        }
        int sixteenth = ((ah) table.get(15)).d(division.yi())[0];
        int seventeenth = ((ah) table.get(16)).d(division.yi())[0];
        if (sixteenth - seventeenth > 4) {
            check(playout == null, year + " Serie B sem play-out (" + sixteenth + " x " + seventeenth + " pontos)");
        } else {
            boolean ok = playout != null && !playout.zp().isEmpty() && ((f.G) playout.zp().get(0)).zY().size() == 1;
            check(ok, year + " Serie B play-out 17o x 16o: " + (ok ? ties(table, (f.G) playout.zp().get(0)) : "ausente"));
        }
    }

    private static void italyC(int year, f.B division) throws Exception {
        f.s league = division.yi();
        ArrayList groups = league.yQ();
        StringBuilder sizes = new StringBuilder();
        for (Object group : groups) sizes.append(((best.G) group).gR().size()).append(' ');
        check(groups.size() == 3 && sizes.toString().equals("20 20 20 "), year + " Serie C em 3 grupos: " + sizes);
        f.z knockout = league.yY();
        int rounds = knockout == null ? 0 : knockout.zp().size();
        ArrayList last = rounds == 0 ? new ArrayList() : ((f.G) knockout.zp().get(rounds - 1)).zY();
        StringBuilder text = new StringBuilder();
        for (int r = 0; r < rounds; r++) text.append(((f.G) knockout.zp().get(r)).zW().size()).append(' ');
        check(rounds == 6 && last.size() == 1, year + " Serie C play-off com 6 fases (confrontos " + text + ") campeao "
                + (last.isEmpty() ? "nenhum" : ((ah) last.get(0)).getNome()));
        StringBuilder leaders = new StringBuilder();
        for (Object group : groups) leaders.append(((ah) ((best.G) group).gR().get(0)).getNome()).append("; ");
        out.println(year + " Serie C campeoes de grupo: " + leaders);
        for (int g = 0; g < groups.size(); g++) {
            StringBuilder files = new StringBuilder();
            for (Object team : ((best.G) groups.get(g)).gR()) files.append(((ah) team).jY()).append(',');
            out.println(year + " grupo " + (char) ('A' + g) + ": " + files);
        }
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
            if (kind.equals("italyB")) {
                italyB(year, division);
                continue;
            }
            if (kind.equals("italyC")) {
                italyC(year, division);
                continue;
            }
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
