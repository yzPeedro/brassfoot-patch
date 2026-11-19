import best.I;
import best.O;
import best.ah;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class EstaduaisHarness {
    private static PrintStream out;
    private static int failures;

    private static void check(boolean condition, String label) {
        out.println((condition ? "OK   " : "FALHA ") + label);
        if (!condition) failures++;
    }

    private static final class Spec {
        String uf;
        int state;
        String type;
        List<String> teams;
        List<List<String>> groups = new ArrayList<List<String>>();
        Set<String> fixtures = new HashSet<String>();
        int legs;
        int rounds;
        int degree;
        int code;
        int sameA = -1;
        int sameB = -1;
        boolean rule;
    }

    private static List<Spec> specs(File file) throws Exception {
        List<Spec> result = new ArrayList<Spec>();
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file), "UTF-8"));
        for (String line = reader.readLine(); line != null; line = reader.readLine()) {
            String[] cols = line.split("\t", -1);
            Spec spec = new Spec();
            spec.uf = cols[0];
            spec.state = Integer.parseInt(cols[1]);
            spec.type = cols[2];
            if (cols.length > 10 && cols[10].length() > 0) {
                String[] pair = cols[10].split(",");
                spec.sameA = Integer.parseInt(pair[0]);
                spec.sameB = Integer.parseInt(pair[1]);
            }
            spec.rule = cols.length > 11 && "1".equals(cols[11]);
            spec.teams = Arrays.asList(cols[3].split(","));
            if (!cols[4].isEmpty()) for (String g : cols[4].split(";")) spec.groups.add(Arrays.asList(g.split(",")));
            if (!cols[5].isEmpty()) spec.fixtures.addAll(Arrays.asList(cols[5].split(",")));
            spec.legs = Integer.parseInt(cols[6]);
            spec.rounds = Integer.parseInt(cols[7]);
            spec.degree = Integer.parseInt(cols[8]);
            spec.code = Integer.parseInt(cols[9]);
            result.add(spec);
        }
        reader.close();
        return result;
    }

    private static f.s league(int state) {
        if (state >= 100) {
            f.F cup = c.a.SR.bV()[state - 100];
            return cup == null ? null : cup.yd();
        }
        for (Object item : c.a.SR.aE()) {
            best.w w = (best.w) item;
            if (w.getEstado() == state && !w.ds.isEmpty()) return ((f.o) w.ds.get(0)).yi();
        }
        return null;
    }

    private static List matches(f.s league) {
        List result = new ArrayList();
        for (Object day : c.a.SR.R()) {
            for (Object item : ((best.a) day).h()) {
                I match = (I) item;
                if (match.ht() == league) result.add(match);
            }
        }
        return result;
    }

    private static Set<String> files(List teams) {
        Set<String> result = new HashSet<String>();
        for (Object team : teams) result.add(((ah) team).jY());
        return result;
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", CompHarness.MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        List<Spec> specs = specs(new File(args[1]));
        int startYear = Integer.parseInt(args[2]);
        System.setProperty("user.dir", game.getPath());
        out = System.out;
        System.setOut(new PrintStream(new FileOutputStream(new File(game, "harness-game-stdout.log")), true, "UTF-8"));
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
        for (Object item : c.a.SR.bF) {
            O option = (O) item;
            option.v(option.getPais() == 29);
        }
        c.a.SR.I(startYear);
        c.a.SR.setJogaEstadual(true);
        c.a.SR.setJogaIntClubes(false);
        c.a.SR.setJogaRegionaisTodos(new boolean[]{false, false, true, true});
        c.a.SR.setJogaSelecoesAll(false);
        best.p.dg();
        best.p.dh();
        c.a.SR.az();
        for (Spec spec : specs) structure(spec);
        int steps = 0;
        try {
            while (!c.a.SR.bk && steps < 5000) {
                c.a.SR.V();
                steps++;
                maybeReload(specs);
            }
        } catch (Throwable error) {
            error.printStackTrace(out);
            System.exit(2);
        }
        check(c.a.SR.bk, "temporada terminou em " + steps + " passos");
        for (Spec spec : specs) result(spec);
        int seasons = args.length > 3 ? Integer.parseInt(args[3]) : 1;
        for (int season = 1; season < seasons; season++) {
            steps = 0;
            try {
                c.a.SR.V();
                while (!c.a.SR.bk && steps < 5000) {
                    c.a.SR.V();
                    steps++;
                    maybeReload(specs);
                }
            } catch (Throwable error) {
                error.printStackTrace(out);
                System.exit(2);
            }
            int year = c.a.SR.op() + c.a.SR.H() - 1;
            check(c.a.SR.bk, year + ": temporada terminou em " + steps + " passos");
            for (Spec spec : specs) later(spec, year);
        }
        if (RELOAD_UF.length() > 0) check(reloads == RELOAD_AT.length, RELOAD_UF + ": " + reloads + " de " + RELOAD_AT.length + " saves recarregados durante o mata-mata");
        out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }

    private static final String RELOAD_UF = System.getProperty("reload.uf", "");
    private static final String[] RELOAD_AT = System.getProperty("reload.rounds", "").split(",");
    private static int reloads = 0;

    private static void maybeReload(List<Spec> specs) {
        if (RELOAD_UF.length() == 0 || reloads >= RELOAD_AT.length || RELOAD_AT[reloads].length() == 0) return;
        for (Spec spec : specs) {
            if (!spec.uf.equals(RELOAD_UF)) continue;
            f.s league = league(spec.state);
            f.z knockout = league == null ? null : league.yY();
            if (knockout != null && knockout.zp().size() == Integer.parseInt(RELOAD_AT[reloads])) {
                reload(spec, knockout);
                reloads++;
            }
        }
    }

    private static void reload(Spec spec, f.z knockout) {
        int rounds = knockout.zp().size();
        int stage = knockout.zb();
        int leg = knockout.zr();
        String last = names(((f.G) knockout.zp().get(rounds - 1)).zW().isEmpty() ? new ArrayList() : teamsOf((f.G) knockout.zp().get(rounds - 1)));
        int teams = c.a.SR.P().size();
        c.a.ae("est-harness");
        boolean loaded = load("est-harness");
        f.s league = league(spec.state);
        f.z after = league == null ? null : league.yY();
        boolean same = loaded && after != null && after != knockout && after.zp().size() == rounds && after.zb() == stage && after.zr() == leg
                && c.a.SR.P().size() == teams
                && last.equals(names(teamsOf((f.G) after.zp().get(rounds - 1))));
        check(same, spec.uf + ": save gravado e recarregado com " + rounds + " fases do mata-mata (fase " + (stage + 1) + ", jogo " + leg + "; " + last + ")");
    }

    private static List teamsOf(f.G round) {
        List result = new ArrayList();
        for (Object item : round.zW()) {
            result.add(((I) item).hc());
            result.add(((I) item).hd());
        }
        return result;
    }

    private static boolean load(String name) {
        try {
            com.esotericsoftware.kryo.Kryo kryo = new com.esotericsoftware.kryo.Kryo();
            kryo.setRegistrationRequired(false);
            com.esotericsoftware.kryo.io.Input input = new com.esotericsoftware.kryo.io.Input(
                    new java.io.FileInputStream(System.getProperty("user.dir") + "/sav/" + name + ".s22"));
            c.a.SR = (best.f) kryo.readClassAndObject(input);
            c.a.afQ = (best.ay) kryo.readClassAndObject(input);
            input.close();
            c.a.SR.bs = false;
            c.a.SR.G();
            return true;
        } catch (Exception error) {
            error.printStackTrace(out);
            return false;
        }
    }

    private static void structure(Spec spec) {
        f.s league = league(spec.state);
        check(league != null, spec.uf + ": estadual criado");
        if (league == null) return;
        check(league.ze() == spec.code, spec.uf + ": formato oficial aplicado (codigo " + league.ze() + ")");
        check(files(league.yK()).equals(new HashSet<String>(spec.teams)), spec.uf + ": participantes oficiais (" + league.yK().size() + " de " + spec.teams.size() + ")");
        Map<String, Integer> group = new HashMap<String, Integer>();
        for (int g = 0; g < spec.groups.size(); g++) for (String f : spec.groups.get(g)) group.put(f, g);
        if (!spec.groups.isEmpty()) {
            ArrayList real = league.yQ();
            boolean same = real != null && real.size() == spec.groups.size();
            for (int g = 0; same && g < real.size(); g++) {
                same = files(((best.G) real.get(g)).gR()).equals(new HashSet<String>(spec.groups.get(g)));
            }
            check(same, spec.uf + ": grupos oficiais");
        }
        List matches = matches(league);
        Map<String, Integer> played = new HashMap<String, Integer>();
        int intra = 0;
        Set<String> pairs = new HashSet<String>();
        Set<String> seen = new HashSet<String>();
        int repeated = 0;
        for (Object item : matches) {
            I match = (I) item;
            String home = match.hc().jY();
            String away = match.hd().jY();
            pairs.add(home + ">" + away);
            String key = home.compareTo(away) < 0 ? home + "|" + away : away + "|" + home;
            if (!seen.add(key) && spec.legs == 1) repeated++;
            played.put(home, played.getOrDefault(home, 0) + 1);
            played.put(away, played.getOrDefault(away, 0) + 1);
            if (group.containsKey(home) && group.get(home).equals(group.get(away))) intra++;
        }
        int n = spec.teams.size();
        int expected;
        if ("crossed".equals(spec.type) || "turns".equals(spec.type)) expected = n * spec.degree / 2 * spec.legs;
        else if ("groups".equals(spec.type)) {
            expected = 0;
            for (List<String> g : spec.groups) expected += g.size() * (g.size() - 1) / 2 * spec.legs;
        } else expected = n * (n - 1) / 2 * spec.legs;
        if ("fixtures".equals(spec.type)) expected = spec.fixtures.size() * spec.legs;
        check(matches.size() == expected, spec.uf + ": " + matches.size() + " jogos na 1a fase (esperado " + expected + ")");
        check(repeated == 0, spec.uf + ": nenhum confronto repetido em turno unico");
        if ("crossed".equals(spec.type)) check(intra == 0, spec.uf + ": nenhum jogo dentro do proprio grupo (" + intra + ")");
        if ("turns".equals(spec.type)) {
            int inside = 0;
            for (List<String> g : spec.groups) inside += g.size() * (g.size() - 1) / 2;
            check(intra == inside, spec.uf + ": 2o turno com " + intra + " jogos dentro da chave (esperado " + inside + ")");
        }
        if ("fixtures".equals(spec.type)) check(pairs.containsAll(spec.fixtures), spec.uf + ": mandos da tabela oficial");
        Set<Integer> counts = new HashSet<Integer>(played.values());
        check(counts.size() == 1, spec.uf + ": todos os clubes com o mesmo numero de jogos " + counts);
    }

    private static void result(Spec spec) {
        f.s league = league(spec.state);
        if (league == null) return;
        int goals = 0;
        for (Object item : matches(league)) goals += ((I) item).hu() + ((I) item).hw();
        check(goals > 0, spec.uf + ": 1a fase disputada (" + goals + " gols)");
        if (!spec.groups.isEmpty()) {
            boolean sorted = true;
            for (Object group : league.yQ()) {
                ArrayList members = ((best.G) group).gR();
                for (int i = 1; i < members.size(); i++) {
                    sorted &= ((ah) members.get(i - 1)).d(league)[0] >= ((ah) members.get(i)).d(league)[0];
                }
            }
            check(sorted, spec.uf + ": grupos ordenados por pontos ao fim da 1a fase");
        }
        f.z knockout = league.yY();
        check(knockout != null, spec.uf + ": mata-mata criado");
        if (knockout == null) return;
        ArrayList rounds = knockout.zp();
        check(roundsOk(spec, rounds), spec.uf + ": " + rounds.size() + " fases de mata-mata (esperado " + spec.rounds + ")");
        StringBuilder text = new StringBuilder();
        for (int r = 0; r < rounds.size(); r++) {
            f.G round = (f.G) rounds.get(r);
            text.append(" | fase ").append(r + 1).append(':');
            for (int t = 0; t < round.zW().size(); t++) {
                I first = (I) round.zW().get(t);
                text.append(' ').append(first.hc().getNome()).append(' ').append(first.hu()).append('x').append(first.hw()).append(' ').append(first.hd().getNome());
                if (round.zX() != null && t < round.zX().size()) {
                    I second = (I) round.zX().get(t);
                    text.append(" / ").append(second.hu()).append('x').append(second.hw());
                }
            }
            text.append(" -> ").append(names(round.zY()));
        }
        out.println(spec.uf + ":" + text);
        ArrayList last = ((f.G) rounds.get(rounds.size() - 1)).zY();
        check(last.size() == 1, spec.uf + ": campeao " + (last.isEmpty() ? "nenhum" : ((ah) last.get(0)).getNome()));
        table(spec, league, String.valueOf(c.a.SR.op() + c.a.SR.H() - 1));
    }

    private static boolean roundsOk(Spec spec, ArrayList rounds) {
        if (rounds.size() == spec.rounds) {
            if (spec.sameA < 0) return true;
            Object a = ((f.G) rounds.get(spec.sameA)).zY().get(0);
            Object b = ((f.G) rounds.get(spec.sameB)).zY().get(0);
            check(a != b, spec.uf + ": final geral disputada entre campeoes de turno diferentes");
            return a != b;
        }
        if (spec.sameA < 0 || rounds.size() != spec.rounds - 1) return false;
        Object a = ((f.G) rounds.get(spec.sameA)).zY().get(0);
        Object b = ((f.G) rounds.get(spec.sameB)).zY().get(0);
        check(a == b, spec.uf + ": sem final geral porque o mesmo clube venceu os dois turnos (" + ((ah) a).getNome() + ")");
        return a == b;
    }

    private static final Map<String, Set<String>> down = new HashMap<String, Set<String>>();
    private static final Map<String, Set<String>> before = new HashMap<String, Set<String>>();

    private static void table(Spec spec, f.s league, String year) {
        before.put(spec.uf, files(league.yK()));
        ArrayList order = best.CompEstaduais.finalOrder(league);
        ArrayList fallen = best.CompEstaduais.relegated(league, 0);
        if (!spec.rule) return;
        check(order != null && order.size() == league.yK().size(), year + " " + spec.uf + ": classificacao final com " + (order == null ? 0 : order.size()) + " clubes");
        if (order == null) return;
        ArrayList rounds = league.yY().zp();
        Object champion = ((f.G) rounds.get(rounds.size() - 1)).zY().get(0);
        check(order.get(0) == champion, year + " " + spec.uf + ": 1o colocado e o campeao do mata-mata");
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < order.size(); i++) text.append(i + 1).append(". ").append(((ah) order.get(i)).getNome()).append("; ");
        out.println(year + " " + spec.uf + " classificacao final: " + text);
        check(fallen != null && !fallen.isEmpty(), year + " " + spec.uf + ": rebaixados pela regra " + (fallen == null ? "nenhum" : names(fallen)));
        if (fallen == null) return;
        boolean bottom = true;
        for (Object team : fallen) bottom &= order.indexOf(team) >= order.size() - fallen.size() - 2;
        check(!fallen.contains(champion), year + " " + spec.uf + ": campeao nao rebaixado");
        if (spec.sameA >= 0) {
            Object first = ((f.G) rounds.get(spec.sameA)).zY().get(0);
            Object second = ((f.G) rounds.get(spec.sameB)).zY().get(0);
            check(!fallen.contains(first) && !fallen.contains(second), year + " " + spec.uf + ": campeoes de turno protegidos do rebaixamento");
        }
        down.put(spec.uf, files(fallen));
    }

    private static void later(Spec spec, int year) {
        f.s league = league(spec.state);
        check(league != null && league.yK().size() == spec.teams.size(), year + " " + spec.uf + ": disputado com " + (league == null ? 0 : league.yK().size()) + " clubes");
        if (league == null) return;
        int goals = 0;
        for (Object item : matches(league)) goals += ((I) item).hu() + ((I) item).hw();
        f.z knockout = league.yY();
        ArrayList rounds = knockout == null ? new ArrayList() : knockout.zp();
        ArrayList last = rounds.isEmpty() ? new ArrayList() : ((f.G) rounds.get(rounds.size() - 1)).zY();
        Set<String> now = files(league.yK());
        Set<String> previous = before.get(spec.uf);
        if (spec.rule && previous != null && down.containsKey(spec.uf)) {
            Set<String> left = new HashSet<String>(previous);
            left.removeAll(files(league.yK()));
            check(left.equals(down.get(spec.uf)), year + " " + spec.uf + ": sairam " + left + ", rebaixados pela regra " + down.get(spec.uf));
        }
        now.removeAll(spec.teams);
        if (knockout != null && rounds.size() > 0 && last.size() == 1) table(spec, league, String.valueOf(year));
        check(goals > 0 && roundsOk(spec, rounds) && last.size() == 1, year + " " + spec.uf + ": " + rounds.size() + " fases, campeao " + (last.isEmpty() ? "nenhum" : ((ah) last.get(0)).getNome()) + ", clubes novos " + now);
    }

    private static String names(List teams) {
        StringBuilder text = new StringBuilder();
        for (Object team : teams) text.append(text.length() == 0 ? "" : ", ").append(((ah) team).getNome());
        return text.toString();
    }
}
