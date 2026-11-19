package best;

import c.a;
import est.LoadLigaOptions;
import f.G;
import f.o;
import f.s;
import f.z;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class CompEstaduais {
    static final int CODE = 2700;

    private CompEstaduais() {
    }

    private static void log(String message, Throwable error) {
        System.err.println("[CompEstaduais] " + message + (error == null ? "" : ": " + error));
    }

    private static int index(int state) {
        for (int i = 0; i < CompEstaduaisData.STATE.length; i++) {
            if (CompEstaduaisData.STATE[i] == state) return i;
        }
        return -1;
    }

    private static ah byFile(String file) {
        ArrayList all = a.SR.P();
        for (int i = 0; i < all.size(); i++) {
            ah team = (ah) all.get(i);
            if (file.equals(team.jY())) return team;
        }
        return null;
    }

    public static void division(w state, LoadLigaOptions options, ArrayList teams, o competition) {
        try {
            if (state.ds.size() != 0) return;
            int k = index(state.getEstado());
            if (k < 0) return;
            String type = CompEstaduaisData.P1_TYPE[k];
            String[] files = CompEstaduaisData.TEAMS[k];
            ArrayList official = new ArrayList();
            for (int i = 0; i < files.length; i++) {
                ah team = byFile(files[i]);
                if (team == null || team.getEstado() != state.getEstado()) {
                    log("estadual " + state.getEstado() + ": clube oficial ausente " + files[i] + "; formato original mantido", null);
                    return;
                }
                official.add(team);
            }
            boolean[] legs = CompEstaduaisData.KO_LEGS[k].length > 0 ? CompEstaduaisData.KO_LEGS[k] : new boolean[]{false};
            boolean[] knockoutLegs = new boolean[7];
            for (int i = 0; i < knockoutLegs.length && i < legs.length; i++) knockoutLegs[i] = legs[i];
            ArrayList arranged = new ArrayList();
            if ("league".equals(type)) {
                arranged.addAll(official);
                options.nGrupos = 0;
            } else if ("groups".equals(type)) {
                String[][] groups = CompEstaduaisData.GROUPS[k];
                boolean equal = true;
                for (int g = 1; g < groups.length; g++) equal &= groups[g].length == groups[0].length;
                options.nGrupos = groups.length;
                if (equal) {
                    for (int r = 0; r < groups[0].length; r++) {
                        for (int g = 0; g < groups.length; g++) arranged.add(byFile(groups[g][r]));
                    }
                } else {
                    options.gruposNumeroDiferenteTimes = true;
                    for (int g = 0; g < groups.length; g++) {
                        options.numeroDefinidoTimesPorGrupo[g] = groups[g].length;
                        for (int r = 0; r < groups[g].length; r++) arranged.add(byFile(groups[g][r]));
                    }
                }
            } else {
                log("estadual " + state.getEstado() + ": primeira fase " + type + " sem suporte; formato original mantido", null);
                return;
            }
            options.nTimes = arranged.size();
            options.doisTurnos = CompEstaduaisData.P1_LEGS[k] == 2;
            options.jogosDentroGrupo = true;
            options.numeroTimesMataMata = 1;
            options.duasVoltasMataMata = knockoutLegs;
            options.desempateEstadual = 0;
            options.var0 = CODE;
            teams.clear();
            teams.addAll(arranged);
            competition.setnRebaixados(CompEstaduaisData.RELEGATED[k]);
        } catch (Throwable error) {
            log("falha ao montar o estadual", error);
        }
    }

    private static Field field(Class type, String name) throws Exception {
        Field field = type.getDeclaredField(name);
        field.setAccessible(true);
        return field;
    }

    static boolean ours(s league) {
        return league != null && league.ze() == CODE && league.ir() != null && index(league.ir().getEstado()) >= 0;
    }

    public static boolean knockout(s league) {
        try {
            if (!ours(league)) return false;
            int k = index(league.ir().getEstado());
            String[][][] rounds = CompEstaduaisData.KO_TIES[k];
            if (rounds.length == 0) return false;
            ArrayList list = resolve(league, null, rounds[0], k, 0);
            if (list == null) return false;
            boolean[] legs = new boolean[7];
            for (int i = 0; i < legs.length && i < CompEstaduaisData.KO_LEGS[k].length; i++) legs[i] = CompEstaduaisData.KO_LEGS[k][i];
            z knockout = new z(league, Math.max(2, list.size()), league.b(), 0, legs, league.yT(), -1);
            knockout.ff(rounds.length);
            field(s.class, "Zc").set(league, knockout);
            G round = new G();
            round.a(knockout, list, 0, legs[0], 0, 0, league.b(), false);
            return true;
        } catch (Throwable error) {
            log("falha ao iniciar o mata-mata estadual", error);
            return false;
        }
    }

    public static boolean round(G round, z knockout, ArrayList list, int index) {
        try {
            if (!(knockout.zy() instanceof s)) return false;
            s league = (s) knockout.zy();
            if (!ours(league)) return false;
            int k = index(league.ir().getEstado());
            String[][][] rounds = CompEstaduaisData.KO_TIES[k];
            if (index >= rounds.length) return true;
            if (index > 0) {
                ArrayList resolved = resolve(league, knockout, rounds[index], k, index);
                if (resolved == null) return true;
                list.clear();
                list.addAll(resolved);
            }
            String tiebreak = CompEstaduaisData.KO_TIEBREAK[k][index];
            if ("better-campaign".equals(tiebreak) || "aggregate-then-better-campaign".equals(tiebreak)) round.fb(2129);
            return true;
        } catch (Throwable error) {
            log("falha no mata-mata estadual", error);
            return true;
        }
    }

    private static ah slot(String code, s league, z knockout, int index, Comparator campaign, List candidates) {
        char head = code.charAt(0);
        if (Character.isDigit(head)) {
            int position = Integer.parseInt(code) - 1;
            ArrayList table = league.yK();
            return position < table.size() ? (ah) table.get(position) : null;
        }
        if (head == 'W' || head == 'L') {
            G previous = (G) knockout.zp().get(index - 1);
            int tie = Integer.parseInt(code.substring(1)) - 1;
            I match = (I) previous.zW().get(tie);
            boolean homeWon = previous.zY().contains(match.hc());
            return (head == 'W') == homeWon ? match.hc() : match.hd();
        }
        if (head == 'C') {
            int position = Integer.parseInt(code.substring(1)) - 1;
            ArrayList ranked = new ArrayList(candidates);
            Collections.sort(ranked, campaign);
            return position < ranked.size() ? (ah) ranked.get(position) : null;
        }
        int group = head - 'A';
        int position = Integer.parseInt(code.substring(1)) - 1;
        ArrayList members = ((best.G) league.yQ().get(group)).gR();
        return position < members.size() ? (ah) members.get(position) : null;
    }

    private static ArrayList resolve(s league, z knockout, String[][] ties, int k, int index) {
        Comparator campaign = campaign(league, knockout);
        ArrayList candidates = new ArrayList();
        if (knockout != null && index > 0) {
            G previous = (G) knockout.zp().get(index - 1);
            candidates.addAll(previous.zY());
            for (int t = 0; t < ties.length; t++) {
                for (int side = 0; side < 2; side++) {
                    char head = ties[t][side].charAt(0);
                    if (head != 'W' && head != 'L' && head != 'C') {
                        ah direct = slot(ties[t][side], league, knockout, index, campaign, candidates);
                        if (direct != null && !candidates.contains(direct)) candidates.add(direct);
                    }
                }
            }
        }
        String home = CompEstaduaisData.KO_HOME[k][index];
        ArrayList list = new ArrayList();
        for (int t = 0; t < ties.length; t++) {
            ah first = slot(ties[t][0], league, knockout, index, campaign, candidates);
            ah second = slot(ties[t][1], league, knockout, index, campaign, candidates);
            if (first == null || second == null) {
                log("confronto sem clube: " + ties[t][0] + " x " + ties[t][1], null);
                return null;
            }
            boolean firstBetter = campaign.compare(first, second) <= 0;
            if ("better-second".equals(home) && firstBetter || "better-single".equals(home) && !firstBetter) {
                ah swap = first;
                first = second;
                second = swap;
            }
            list.add(first);
            list.add(second);
        }
        return list;
    }

    private static Comparator campaign(final s league, final z knockout) {
        final Map cache = new HashMap();
        return new Comparator() {
            int[] of(Object team) {
                int[] value = (int[]) cache.get(team);
                if (value != null) return value;
                int[] group = ((ah) team).d(league);
                value = new int[]{group[0], group[2], group[7], group[5]};
                if (knockout != null) {
                    for (int r = 0; r < knockout.zp().size(); r++) {
                        G round = (G) knockout.zp().get(r);
                        add(value, (ah) team, round.zW());
                        add(value, (ah) team, round.zX());
                    }
                }
                cache.put(team, value);
                return value;
            }

            public int compare(Object x, Object y) {
                int[] p = of(x);
                int[] q = of(y);
                for (int i = 0; i < p.length; i++) {
                    if (p[i] != q[i]) return q[i] - p[i];
                }
                return league.yK().indexOf(x) - league.yK().indexOf(y);
            }
        };
    }

    private static void add(int[] total, ah team, ArrayList matches) {
        if (matches == null) return;
        for (int i = 0; i < matches.size(); i++) {
            I match = (I) matches.get(i);
            if (!match.hO()) continue;
            int own;
            int other;
            if (match.hc() == team) {
                own = match.hu();
                other = match.hw();
            } else if (match.hd() == team) {
                own = match.hw();
                other = match.hu();
            } else {
                continue;
            }
            total[0] += own > other ? 3 : own == other ? 1 : 0;
            total[1] += own > other ? 1 : 0;
            total[2] += own - other;
            total[3] += own;
        }
    }
}
