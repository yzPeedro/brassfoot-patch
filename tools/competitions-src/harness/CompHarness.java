import best.I;
import best.O;
import best.Z;
import best.ah;
import best.at;
import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.prefs.AbstractPreferences;
import java.util.prefs.Preferences;
import java.util.prefs.PreferencesFactory;

public final class CompHarness {
    public static final class MemoryPrefsFactory implements PreferencesFactory {
        private static final Preferences USER = new MemoryPrefs(null, "");
        private static final Preferences SYSTEM = new MemoryPrefs(null, "");

        public Preferences userRoot() {
            return USER;
        }

        public Preferences systemRoot() {
            return SYSTEM;
        }
    }

    static final class MemoryPrefs extends AbstractPreferences {
        private final Map<String, String> values = new HashMap<String, String>();
        private final Map<String, MemoryPrefs> children = new HashMap<String, MemoryPrefs>();

        MemoryPrefs(AbstractPreferences parent, String name) {
            super(parent, name);
        }

        protected void putSpi(String key, String value) {
            values.put(key, value);
        }

        protected String getSpi(String key) {
            return values.get(key);
        }

        protected void removeSpi(String key) {
            values.remove(key);
        }

        protected void removeNodeSpi() {
        }

        protected String[] keysSpi() {
            return values.keySet().toArray(new String[0]);
        }

        protected String[] childrenNamesSpi() {
            return children.keySet().toArray(new String[0]);
        }

        protected AbstractPreferences childSpi(String name) {
            MemoryPrefs child = children.get(name);
            if (child == null) {
                child = new MemoryPrefs(this, name);
                children.put(name, child);
            }
            return child;
        }

        protected void syncSpi() {
        }

        protected void flushSpi() {
        }
    }

    private static PrintStream out;
    private static int failures;

    private static void check(boolean condition, String label) {
        out.println((condition ? "OK   " : "FALHA ") + label);
        if (!condition) failures++;
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        int seasons = Integer.parseInt(args[1]);
        int startYear = Integer.parseInt(args[2]);
        int reloadAt = args.length > 4 ? Integer.parseInt(args[4]) : -1;
        String mode = args.length > 5 ? args[5] : "";
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
        if (mode.equals("continue")) {
            check(load("comp-harness"), "carreira antiga carregada pelo executavel novo");
        } else {
            best.p.dg();
            best.p.dh();
            c.a.SR.az();
        }
        sizes("criacao");
        if (args.length > 3 && !args[3].isEmpty()) {
            PrintStream members = new PrintStream(new FileOutputStream(args[3]), true, "UTF-8");
            ArrayList divisions = c.a.SR.o(29).eb();
            for (int i = 0; i < divisions.size(); i++) {
                for (Object team : ((f.B) divisions.get(i)).yi().yK()) members.println((i + 1) + "	" + ((ah) team).jY() + "	" + ((ah) team).getNome());
            }
            members.close();
        }
        for (int season = 0; season < seasons; season++) {
            int year = c.a.SR.op() + c.a.SR.H() - 1;
            int steps = 0;
            try {
                while (!c.a.SR.bk && steps < 5000) {
                    c.a.SR.V();
                    steps++;
                    if (season == 0 && steps == reloadAt) {
                        if (mode.equals("save-only")) {
                            c.a.ae("comp-harness");
                            out.println("save gravado no passo " + steps);
                            System.exit(0);
                        }
                        reload(year);
                    }
                }
            } catch (Throwable error) {
                error.printStackTrace(out);
                diagnose();
                System.exit(2);
            }
            check(c.a.SR.bk, "temporada " + year + " terminou em " + steps + " passos");
            Z brazil = c.a.SR.o(29);
            ArrayList divisions = brazil.eb();
            List<Set<ah>> before = new ArrayList<Set<ah>>();
            for (int i = 0; i < divisions.size(); i++) before.add(new HashSet<ah>(((f.B) divisions.get(i)).yi().yK()));
            for (int i = 0; i < divisions.size(); i++) {
                at division = (at) divisions.get(i);
                ah champion = division.cS();
                out.println("campeao " + year + " divisao " + (i + 1) + ": " + (champion == null ? "nenhum" : champion.getNome()));
            }
            serieB(year, (f.B) divisions.get(1));
            copa(year, brazil.jq());
            List<ah> promotedD = serieD(year, (f.B) divisions.get(3));
            ArrayList<ah> cRelegated = new ArrayList<ah>();
            c.a.SR.V();
            sizes("apos virada " + year);
            Set<ah> cNow = new HashSet<ah>(((f.B) divisions.get(2)).yi().yK());
            int arrived = 0;
            for (ah team : promotedD) if (cNow.contains(team)) arrived++;
            check(arrived == promotedD.size() && promotedD.size() == 6, year + ": " + arrived + " de " + promotedD.size() + " promovidos da Serie D estao na Serie C");
            for (ah team : before.get(2)) if (!cNow.contains(team) && team.getDivisao() != 2) cRelegated.add(team);
            out.println(year + ": sairam da Serie C para baixo: " + names(cRelegated));
            int expectedC = before.get(2).size() + 6 - (year >= 2028 ? 6 : 2);
            check(cNow.size() == expectedC, year + ": Serie C seguinte com " + cNow.size() + " clubes (esperado " + expectedC + ")");
        }
        out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }

    private static void reload(int year) {
        int teams = c.a.SR.P().size();
        f.f cupBefore = c.a.SR.o(29).jq();
        int copaPhase = cupBefore == null || cupBefore.yf() == null ? -1 : cupBefore.yf().zb();
        int dTeams = ((f.B) c.a.SR.o(29).eb().get(3)).yi().yK().size();
        c.a.ae("comp-harness");
        boolean loaded = load("comp-harness");
        f.f cup = c.a.SR.o(29).jq();
        int copaAfter = cup == null || cup.yf() == null ? -1 : cup.yf().zb();
        int dAfter = ((f.B) c.a.SR.o(29).eb().get(3)).yi().yK().size();
        check(loaded && c.a.SR.P().size() == teams, year + ": save gravado e recarregado no meio da temporada (" + teams + " clubes)");
        check(copaPhase == copaAfter && dTeams == dAfter, year + ": apos recarregar, Copa na fase " + copaAfter + " (antes " + copaPhase + ") e Serie D com " + dAfter + " clubes (antes " + dTeams + ")");
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

    private static void diagnose() {
        ArrayList divisions = c.a.SR.o(29).eb();
        for (int i = 0; i < divisions.size(); i++) {
            f.B division = (f.B) divisions.get(i);
            inspect("div" + (i + 1) + " liga", division.yi().yY());
            inspect("div" + (i + 1) + " acesso", division.BR());
            if (division.zP() != null) inspect("div" + (i + 1) + " quadrangular", division.zP().yY());
            out.println("div" + (i + 1) + " clubes=" + division.yi().yK().size() + " grupos=" + division.yi().yQ().size() + " codigo=" + division.yi().ze()
                    + " rodadaAtual=" + division.yi().zb() + " rodadasComData=" + division.yi().yG() + " datas=" + division.yi().yF().size() + " terminou=" + division.BS());
            if (division.zP() != null) out.println("   quadrangular rodadaAtual=" + division.zP().zb() + " rodadasComData=" + division.zP().yG() + " datas=" + division.zP().yF());
        }
    }

    private static void inspect(String label, f.z knockout) {
        if (knockout == null) return;
        for (int r = 0; r < knockout.zp().size(); r++) {
            f.G round = (f.G) knockout.zp().get(r);
            StringBuilder text = new StringBuilder();
            for (Object item : round.zW()) {
                I match = (I) item;
                boolean ok = round.zY().contains(match.hc()) || round.zY().contains(match.hd());
                text.append(match.hc() == null ? "null" : match.hc().getNome()).append(" x ")
                    .append(match.hd() == null ? "null" : match.hd().getNome()).append(ok ? "" : " [SEM VENCEDOR]").append("; ");
            }
            out.println(label + " rodada " + r + " codigo=" + round.ze() + " jogos=" + round.zW().size() + " vencedores=" + round.zY().size() + " :: " + text);
        }
    }

    private static String names(List<ah> teams) {
        StringBuilder text = new StringBuilder();
        for (ah team : teams) text.append(team.getNome()).append(" (").append(team.jY()).append("); ");
        return text.toString();
    }

    private static void sizes(String label) {
        Z brazil = c.a.SR.o(29);
        StringBuilder text = new StringBuilder();
        for (Object division : brazil.eb()) text.append(((f.B) division).yi().yK().size()).append(' ');
        out.println("[" + label + "] H()=" + c.a.SR.H() + " tamanhos=" + text + "semDivisao=" + brazil.ek().size() + " bk()=" + c.a.SR.bk());
    }

    private static int legs(f.z knockout) {
        int total = 0;
        if (knockout == null) return 0;
        for (Object item : knockout.zp()) {
            f.G round = (f.G) item;
            total += round.zW().size() + (round.zX() == null ? 0 : round.zX().size());
        }
        return total;
    }

    private static void copa(int year, f.f cup) {
        f.z knockout = cup == null ? null : cup.yf();
        check(knockout != null && knockout.zp().size() == 9, year + ": Copa do Brasil com " + (knockout == null ? 0 : knockout.zp().size()) + " fases");
        if (knockout == null) return;
        int[] teams = {28, 88, 48, 24, 32, 16, 8, 4, 2};
        StringBuilder sizes = new StringBuilder();
        int matches = 0;
        boolean ok = knockout.zp().size() == 9;
        for (int i = 0; i < knockout.zp().size(); i++) {
            f.G round = (f.G) knockout.zp().get(i);
            int clubs = round.zW().size() * 2;
            int second = round.zX() == null ? 0 : round.zX().size();
            matches += round.zW().size() + second;
            sizes.append(clubs).append(second > 0 ? "(iv)" : "").append(' ');
            boolean twoLegs = i >= 4 && i <= 7;
            ok &= i < teams.length && clubs == teams[i] && (second > 0) == twoLegs && round.zY().size() == round.zW().size();
        }
        check(ok, year + ": Copa do Brasil fases " + sizes);
        check(matches == 155, year + ": Copa do Brasil com " + matches + " jogos (esperado 155)");
        ah champion = cup.cS();
        check(champion != null, year + ": campeao da Copa do Brasil " + (champion == null ? "nenhum" : champion.getNome()));
    }

    private static void serieB(int year, f.B b) {
        f.z playoff = b.BR();
        check(playoff != null && playoff.zp().size() == 1, year + ": Serie B com playoffs de acesso");
        if (playoff == null) return;
        f.G round = (f.G) playoff.zp().get(0);
        ArrayList table = b.yi().yK();
        StringBuilder pairs = new StringBuilder();
        boolean ok = round.zW().size() == 2 && round.zX().size() == 2;
        for (int i = 0; i < round.zW().size(); i++) {
            I first = (I) round.zW().get(i);
            int home = table.indexOf(first.hc()) + 1;
            int away = table.indexOf(first.hd()) + 1;
            pairs.append(home).append("o x ").append(away).append("o ").append(first.hu()).append('-').append(first.hw());
            I second = (I) round.zX().get(i);
            pairs.append(" / ").append(second.hu()).append('-').append(second.hw()).append("; ");
            ok &= home + away == 9 && home > away;
        }
        check(ok, year + ": Serie B playoffs 6x3 e 5x4 com volta na casa do melhor: " + pairs + " vencedores " + names(round.zY()));
        check(round.ze() == 2129, year + ": Serie B playoffs sem penaltis (codigo " + round.ze() + ")");
    }

    private static List<ah> serieD(int year, f.B d) {
        f.s league = d.yi();
        check(league.yQ().size() == 16, year + ": Serie D com " + league.yQ().size() + " grupos");
        int groupGames = 0;
        boolean six = true;
        for (Object group : league.yQ()) {
            ArrayList members = ((best.G) group).gR();
            six &= members.size() == 6;
            for (Object team : members) groupGames += ((ah) team).d(league)[1];
        }
        check(six, year + ": todos os grupos com 6 clubes");
        check(groupGames / 2 == 480, year + ": " + groupGames / 2 + " jogos na primeira fase");
        f.z knockout = league.yY();
        int knockoutGames = legs(knockout);
        StringBuilder rounds = new StringBuilder();
        if (knockout != null) for (Object item : knockout.zp()) rounds.append(((f.G) item).zW().size() * 2).append(' ');
        check(knockout != null && knockout.zp().size() == 6, year + ": mata-mata com rodadas de " + rounds + "clubes");
        f.z playoff = d.BR();
        int playoffGames = legs(playoff);
        check(playoff != null && playoffGames == 4, year + ": playoffs de acesso com " + playoffGames + " jogos");
        check(d.mB().length == 1 && d.mB()[0] == knockout, year + ": tela principal da Serie D mostra o mata-mata principal");
        check(groupGames / 2 + knockoutGames + playoffGames == 610, year + ": total " + (groupGames / 2 + knockoutGames + playoffGames) + " jogos (esperado 610)");
        if (knockout != null && knockout.zp().size() == 6) {
            f.G first = (f.G) knockout.zp().get(0);
            boolean sameGroup = false;
            for (Object item : first.zW()) {
                I match = (I) item;
                for (Object group : league.yQ()) {
                    ArrayList members = ((best.G) group).gR();
                    if (members.contains(match.hc()) && members.contains(match.hd())) sameGroup = true;
                }
            }
            check(!sameGroup, year + ": nenhum confronto da 2a fase entre clubes do mesmo grupo");
            check(first.ze() != 2129 && ((f.G) knockout.zp().get(5)).zX().size() == 1, year + ": final em ida e volta");
        }
        ArrayList promoted = league.l(6, true);
        List<ah> result = new ArrayList<ah>();
        for (Object team : promoted) result.add((ah) team);
        out.println(year + ": promovidos da Serie D: " + names(result));
        if (playoff != null && playoff.zp().size() == 1) {
            f.G round = (f.G) playoff.zp().get(0);
            check(round.ze() == 2129, year + ": playoffs da Serie D sem penaltis");
            for (Object winner : round.zY()) check(result.contains(winner), year + ": vencedor de playoff " + ((ah) winner).getNome() + " promovido");
        }
        return result;
    }
}
