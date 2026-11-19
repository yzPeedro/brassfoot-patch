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
            spec.teams = Arrays.asList(cols[3].split(","));
            if (!cols[4].isEmpty()) for (String g : cols[4].split(";")) spec.groups.add(Arrays.asList(g.split(",")));
            if (!cols[5].isEmpty()) spec.fixtures.addAll(Arrays.asList(cols[5].split(",")));
            spec.legs = Integer.parseInt(cols[6]);
            spec.rounds = Integer.parseInt(cols[7]);
            result.add(spec);
        }
        reader.close();
        return result;
    }

    private static f.s league(int state) {
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
            }
        } catch (Throwable error) {
            error.printStackTrace(out);
            System.exit(2);
        }
        check(c.a.SR.bk, "temporada terminou em " + steps + " passos");
        for (Spec spec : specs) result(spec);
        out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }

    private static void structure(Spec spec) {
        f.s league = league(spec.state);
        check(league != null, spec.uf + ": estadual criado");
        if (league == null) return;
        check(league.ze() == 2700, spec.uf + ": formato oficial aplicado (codigo " + league.ze() + ")");
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
        if ("crossed".equals(spec.type)) expected = n * (n - spec.groups.get(0).size()) / 2 * spec.legs;
        else if ("groups".equals(spec.type)) {
            expected = 0;
            for (List<String> g : spec.groups) expected += g.size() * (g.size() - 1) / 2 * spec.legs;
        } else expected = n * (n - 1) / 2 * spec.legs;
        if ("fixtures".equals(spec.type)) expected = spec.fixtures.size() * spec.legs;
        check(matches.size() == expected, spec.uf + ": " + matches.size() + " jogos na 1a fase (esperado " + expected + ")");
        check(repeated == 0, spec.uf + ": nenhum confronto repetido em turno unico");
        if ("crossed".equals(spec.type)) check(intra == 0, spec.uf + ": nenhum jogo dentro do proprio grupo (" + intra + ")");
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
        f.z knockout = league.yY();
        check(knockout != null, spec.uf + ": mata-mata criado");
        if (knockout == null) return;
        ArrayList rounds = knockout.zp();
        check(rounds.size() == spec.rounds, spec.uf + ": " + rounds.size() + " fases de mata-mata (esperado " + spec.rounds + ")");
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
    }

    private static String names(List teams) {
        StringBuilder text = new StringBuilder();
        for (Object team : teams) text.append(text.length() == 0 ? "" : ", ").append(((ah) team).getNome());
        return text.toString();
    }
}
