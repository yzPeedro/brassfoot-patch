package best;

import c.a;
import est.LoadLigaOptions;
import f.F;
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
    static final int POINTS_CODE = 2701;
    static final int HOME_CODE = 2130;

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

    static int key(s league) {
        if (league == null) return -1;
        int code = league.ze();
        if (code == CODE) return league.ir() == null ? -1 : index(league.ir().getEstado());
        if (code > CODE + 1 && code < CODE + 100) return index(code - CODE + 100);
        Z country = league.iq();
        return country == null ? -1 : index(10000 + country.jc() * 10 + league.ip());
    }

    static boolean officialSeason() {
        return a.SR.op() + a.SR.H() - 1 == 2026;
    }

    private static final int[][] BLOCKS = {{0, 2, 3, 13, 20, 21}, {6, 7, 8, 11, 12, 26}};
    private static final int[][] REGION_STATES = {{}, {}, {1, 4, 5, 9, 14, 15, 16, 19, 24}, {0, 2, 3, 6, 7, 8, 11, 12, 13, 20, 21, 26}};

    private static boolean in(int[] values, int value) {
        for (int i = 0; i < values.length; i++) if (values[i] == value) return true;
        return false;
    }

    private static ArrayList laterSeason(int region, String[][] groups, ArrayList pool) {
        int size = groups[0].length;
        int[][] blocks = region == 3 ? BLOCKS : new int[][]{REGION_STATES[region]};
        int perBlock = groups.length / blocks.length;
        ArrayList arranged = new ArrayList();
        for (int b = 0; b < blocks.length; b++) {
            ArrayList picked = new ArrayList();
            for (int i = 0; i < pool.size() && picked.size() < perBlock * size; i++) {
                ah team = (ah) pool.get(i);
                if (team.getPais() == 29 && in(blocks[b], team.getEstado()) && !picked.contains(team)) picked.add(team);
            }
            if (picked.size() < perBlock * size) return null;
            ArrayList[] block = new ArrayList[perBlock];
            for (int g = 0; g < perBlock; g++) block[g] = new ArrayList();
            for (int i = 0; i < picked.size(); i++) {
                int line = i / perBlock;
                int g = line % 2 == 0 ? i % perBlock : perBlock - 1 - i % perBlock;
                block[g].add(picked.get(i));
            }
            for (int g = 0; g < perBlock; g++) arranged.addAll(block[g]);
        }
        return arranged;
    }

    public static boolean regional(F cup, ArrayList pool) {
        try {
            int region = ((Integer) field(F.class, "aad").get(cup)).intValue();
            int k = index(100 + region);
            if (k < 0) return false;
            String[][] groups = CompEstaduaisData.GROUPS[k];
            ArrayList arranged = new ArrayList();
            if (!officialSeason()) {
                arranged = laterSeason(region, groups, pool);
                if (arranged == null) return false;
            }
            for (int g = 0; officialSeason() && g < groups.length; g++) {
                for (int r = 0; r < groups[g].length; r++) {
                    ah team = byFile(groups[g][r]);
                    if (team == null || team.getPais() != 29) {
                        log("regional " + region + ": clube oficial ausente " + groups[g][r] + "; formato original mantido", null);
                        return false;
                    }
                    arranged.add(team);
                }
            }
            boolean[] legs = new boolean[7];
            for (int i = 0; i < legs.length && i < CompEstaduaisData.KO_LEGS[k].length; i++) legs[i] = CompEstaduaisData.KO_LEGS[k][i];
            LoadLigaOptions options = new LoadLigaOptions();
            options.nTimes = arranged.size();
            options.nGrupos = groups.length;
            options.numeroTimesMataMata = 1;
            options.doisTurnos = CompEstaduaisData.P1_LEGS[k] == 2;
            options.duasVoltasMataMata = legs;
            options.jogosDentroGrupo = !"crossed".equals(CompEstaduaisData.P1_TYPE[k]);
            options.var0 = CODE + region;
            ArrayList members = (ArrayList) field(F.class, "YF").get(cup);
            members.clear();
            members.addAll(arranged);
            s league = new s(options, members, 0, null, null, null, 10, null, false, null, true, cup);
            field(F.class, "YD").set(cup, league);
            league.setNome(cup.getNome());
            return true;
        } catch (Throwable error) {
            log("falha ao montar o regional", error);
            return false;
        }
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
            if (state.ds.size() != 0 || !officialSeason()) return;
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
            if ("league".equals(type) || "fixtures".equals(type)) {
                arranged.addAll(official);
                options.nGrupos = 0;
                options.jogosDentroGrupo = true;
            } else if ("groups".equals(type) || "crossed".equals(type)) {
                String[][] groups = CompEstaduaisData.GROUPS[k];
                options.jogosDentroGrupo = !"crossed".equals(type);
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

    public static ah[][][] crossed(s league, ArrayList teams, boolean cross, ArrayList groups, ah[][][] current) {
        try {
            if (teams.isEmpty()) return current;
            int state = ((ah) teams.get(0)).getEstado();
            int k = league.ze() == CODE ? index(state) : key(league);
            if (k < 0) return current;
            if (!cross) {
                if (officialSeason() && CompEstaduaisData.FIXTURES[k].length > 0) return fixtures(league, teams, k, current);
                return teams.size() % 2 == 1 ? oddRoundRobin(league, teams, k, current) : current;
            }
            if (groups == null || groups.size() < 2) return current;
            int n = teams.size();
            int[] group = new int[n];
            int size = -1;
            for (int g = 0; g < groups.size(); g++) {
                ArrayList members = ((best.G) groups.get(g)).gR();
                if (size >= 0 && members.size() != size) return current;
                size = members.size();
                for (int m = 0; m < members.size(); m++) group[teams.indexOf(members.get(m))] = g;
            }
            int[][] opponents = CompEstaduaisData.OPPONENTS[k];
            boolean[][] allowed = new boolean[groups.size()][groups.size()];
            int rounds = 0;
            for (int g = 0; g < groups.size(); g++) {
                for (int h = 0; h < groups.size(); h++) {
                    boolean listed = opponents.length == 0;
                    for (int i = 0; opponents.length > 0 && i < opponents[g].length; i++) listed |= opponents[g][i] == h;
                    allowed[g][h] = g != h && listed;
                    if (g == 0 && allowed[g][h]) rounds += size;
                }
            }
            int[][] pairs = schedule(n, group, allowed, rounds, new java.util.Random(7919L * (k + 1)));
            if (pairs == null) {
                log("estadual " + state + ": tabela cruzada sem solucao", null);
                return current;
            }
            boolean twoLegs = CompEstaduaisData.P1_LEGS[k] == 2;
            int total = twoLegs ? rounds * 2 : rounds;
            ah[][][] result = new ah[total][n / 2][4];
            int[] homes = new int[n];
            for (int r = 0; r < rounds; r++) {
                for (int m = 0; m < n / 2; m++) {
                    int x = pairs[r][2 * m];
                    int y = pairs[r][2 * m + 1];
                    if (homes[y] < homes[x] || homes[y] == homes[x] && (r + m) % 2 == 1) {
                        int swap = x;
                        x = y;
                        y = swap;
                    }
                    homes[x]++;
                    result[r][m][0] = (ah) teams.get(x);
                    result[r][m][3] = (ah) teams.get(y);
                    if (twoLegs) {
                        result[r + rounds][m][0] = (ah) teams.get(y);
                        result[r + rounds][m][3] = (ah) teams.get(x);
                    }
                }
            }
            return result;
        } catch (Throwable error) {
            log("falha na tabela cruzada", error);
            return current;
        }
    }

    private static ah[][][] fixtures(s league, ArrayList teams, int k, ah[][][] current) {
        String[] pairs = CompEstaduaisData.FIXTURES[k];
        if (pairs.length == 0) return current;
        int perRound = teams.size() / 2;
        int rounds = pairs.length / 2 / perRound;
        boolean twoLegs = CompEstaduaisData.P1_LEGS[k] == 2;
        ah[][][] result = new ah[twoLegs ? rounds * 2 : rounds][perRound][4];
        for (int i = 0; i < pairs.length / 2; i++) {
            ah home = byFile(pairs[2 * i]);
            ah away = byFile(pairs[2 * i + 1]);
            if (home == null || away == null || !teams.contains(home) || !teams.contains(away)) {
                log("estadual " + k + ": jogo da tabela sem clube", null);
                return current;
            }
            int r = i / perRound;
            int m = i % perRound;
            result[r][m][0] = home;
            result[r][m][3] = away;
            if (twoLegs) {
                result[r + rounds][m][0] = away;
                result[r + rounds][m][3] = home;
            }
        }
        return result;
    }

    private static ah[][][] oddRoundRobin(s league, ArrayList teams, int k, ah[][][] current) {
        int n = teams.size();
        int nodes = n + 1;
        int[] group = new int[nodes];
        boolean[][] allowed = new boolean[nodes][nodes];
        for (int i = 0; i < nodes; i++) {
            group[i] = i;
            for (int j = 0; j < nodes; j++) allowed[i][j] = i != j;
        }
        int[][] pairs = schedule(nodes, group, allowed, n, new java.util.Random(104729L * (k + 1)));
        if (pairs == null) return current;
        boolean twoLegs = CompEstaduaisData.P1_LEGS[k] == 2;
        int perRound = n / 2;
        ah[][][] result = new ah[twoLegs ? n * 2 : n][perRound][4];
        int[] homes = new int[n];
        for (int r = 0; r < n; r++) {
            int m = 0;
            for (int p = 0; p < pairs[r].length; p += 2) {
                int x = pairs[r][p];
                int y = pairs[r][p + 1];
                if (x == n || y == n) continue;
                if (homes[y] < homes[x] || homes[y] == homes[x] && (r + m) % 2 == 1) {
                    int swap = x;
                    x = y;
                    y = swap;
                }
                homes[x]++;
                result[r][m][0] = (ah) teams.get(x);
                result[r][m][3] = (ah) teams.get(y);
                if (twoLegs) {
                    result[r + n][m][0] = (ah) teams.get(y);
                    result[r + n][m][3] = (ah) teams.get(x);
                }
                m++;
            }
        }
        return result;
    }

    static int[][] schedule(int n, int[] group, boolean[][] allowed, int rounds, java.util.Random random) {
        for (int attempt = 0; attempt < 5000; attempt++) {
            boolean[][] used = new boolean[n][n];
            int[][] result = new int[rounds][];
            boolean ok = true;
            for (int r = 0; r < rounds && ok; r++) {
                int[] matching = new int[n];
                java.util.Arrays.fill(matching, -1);
                ok = match(0, n, group, allowed, used, matching, random);
                if (!ok) break;
                int[] flat = new int[n];
                int f = 0;
                for (int v = 0; v < n; v++) {
                    if (matching[v] > v) {
                        flat[f++] = v;
                        flat[f++] = matching[v];
                        used[v][matching[v]] = true;
                        used[matching[v]][v] = true;
                    }
                }
                result[r] = flat;
            }
            if (ok) return result;
        }
        return null;
    }

    private static boolean match(int from, int n, int[] group, boolean[][] allowed, boolean[][] used, int[] matching, java.util.Random random) {
        int v = from;
        while (v < n && matching[v] >= 0) v++;
        if (v == n) return true;
        int[] order = new int[n];
        for (int i = 0; i < n; i++) order[i] = i;
        for (int i = n - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            int t = order[i];
            order[i] = order[j];
            order[j] = t;
        }
        for (int i = 0; i < n; i++) {
            int w = order[i];
            if (w == v || matching[w] >= 0 || !allowed[group[v]][group[w]] || used[v][w]) continue;
            matching[v] = w;
            matching[w] = v;
            if (match(v + 1, n, group, allowed, used, matching, random)) return true;
            matching[v] = -1;
            matching[w] = -1;
        }
        return false;
    }

    private static Field field(Class type, String name) throws Exception {
        Field field = type.getDeclaredField(name);
        field.setAccessible(true);
        return field;
    }

    static boolean ours(s league) {
        return key(league) >= 0;
    }

    public static boolean knockout(s league) {
        try {
            if (!ours(league)) return false;
            int k = key(league);
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
            int k = key(league);
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
            if ("points-then-penalties".equals(tiebreak)) round.fb(POINTS_CODE);
            if ("aggregate-then-second-host".equals(tiebreak)) round.fb(2129);
            if ("home-advances".equals(tiebreak)) round.fb(HOME_CODE);
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
        if (head == 'P') {
            int position = Integer.parseInt(code.substring(1)) - 1;
            ArrayList ordered = new ArrayList();
            ArrayList groups = league.yQ();
            for (int place = 0; ordered.size() < league.yK().size(); place++) {
                ArrayList same = new ArrayList();
                for (int g = 0; g < groups.size(); g++) {
                    ArrayList members = ((best.G) groups.get(g)).gR();
                    if (place < members.size()) same.add(members.get(place));
                }
                if (same.isEmpty()) break;
                Collections.sort(same, campaign);
                ordered.addAll(same);
            }
            return position < ordered.size() ? (ah) ordered.get(position) : null;
        }
        if (head == 'Q') {
            int group = code.charAt(1) - 'A';
            int position = Integer.parseInt(code.substring(2)) - 1;
            final ArrayList members = ((best.G) league.yQ().get(group)).gR();
            ArrayList same = new ArrayList();
            for (int i = 0; i < candidates.size(); i++) if (members.contains(candidates.get(i))) same.add(candidates.get(i));
            Collections.sort(same, new Comparator() {
                public int compare(Object x, Object y) {
                    return members.indexOf(x) - members.indexOf(y);
                }
            });
            return position < same.size() ? (ah) same.get(position) : null;
        }
        if (head == 'G') {
            int position = Integer.parseInt(code.substring(1)) - 1;
            ArrayList winners = new ArrayList(((G) knockout.zp().get(index - 1)).zY());
            Collections.sort(winners, byGroupPosition(league, campaign));
            return position < winners.size() ? (ah) winners.get(position) : null;
        }
        if (head == 'R') {
            int position = Integer.parseInt(code.substring(1)) - 1;
            ArrayList ranked = new ArrayList(candidates);
            final ArrayList table = league.yK();
            Collections.sort(ranked, new Comparator() {
                public int compare(Object x, Object y) {
                    return table.indexOf(x) - table.indexOf(y);
                }
            });
            return position < ranked.size() ? (ah) ranked.get(position) : null;
        }
        int group = head - 'A';
        int position = Integer.parseInt(code.substring(1)) - 1;
        ArrayList members = ((best.G) league.yQ().get(group)).gR();
        return position < members.size() ? (ah) members.get(position) : null;
    }

    private static boolean direct(String code) {
        char head = code.charAt(0);
        return head != 'W' && head != 'L' && head != 'R' && head != 'Q' && head != 'G' && head != 'X';
    }

    private static Comparator byGroupPosition(final s league, final Comparator campaign) {
        return new Comparator() {
            int place(Object team) {
                ArrayList groups = league.yQ();
                for (int g = 0; g < groups.size(); g++) {
                    int at = ((best.G) groups.get(g)).gR().indexOf(team);
                    if (at >= 0) return at;
                }
                return league.yK().indexOf(team);
            }

            public int compare(Object x, Object y) {
                int difference = place(x) - place(y);
                return difference != 0 ? difference : campaign.compare(x, y);
            }
        };
    }

    private static ArrayList resolve(s league, z knockout, String[][] ties, int k, int index) {
        Comparator campaign = campaign(league, knockout);
        ArrayList candidates = new ArrayList();
        ArrayList winners = new ArrayList();
        if (knockout != null && index > 0) {
            G previous = (G) knockout.zp().get(index - 1);
            winners.addAll(previous.zY());
            candidates.addAll(winners);
            String[] entrants = index < CompEstaduaisData.KO_ENTRANTS[k].length ? CompEstaduaisData.KO_ENTRANTS[k][index] : new String[0];
            for (int e = 0; e < entrants.length; e++) {
                ah entrant = slot(entrants[e], league, knockout, index, campaign, candidates);
                if (entrant != null && !candidates.contains(entrant)) candidates.add(entrant);
            }
            for (int t = 0; t < ties.length; t++) {
                for (int side = 0; side < 2; side++) {
                    if (direct(ties[t][side])) {
                        ah team = slot(ties[t][side], league, knockout, index, campaign, candidates);
                        if (team != null && !candidates.contains(team)) candidates.add(team);
                    }
                }
            }
        }
        ah[][] chosen = new ah[ties.length][2];
        ArrayList used = new ArrayList();
        for (int t = 0; t < ties.length; t++) {
            for (int side = 0; side < 2; side++) {
                if (ties[t][side].charAt(0) == 'X') continue;
                chosen[t][side] = slot(ties[t][side], league, knockout, index, campaign, candidates);
                if (chosen[t][side] != null) used.add(chosen[t][side]);
            }
        }
        ArrayList drawn = new ArrayList(winners);
        drawn.removeAll(used);
        Collections.shuffle(drawn);
        for (int t = 0; t < ties.length; t++) {
            for (int side = 0; side < 2; side++) {
                if (ties[t][side].charAt(0) != 'X') continue;
                int position = Integer.parseInt(ties[t][side].substring(1)) - 1;
                chosen[t][side] = position < drawn.size() ? (ah) drawn.get(position) : null;
            }
        }
        String home = CompEstaduaisData.KO_HOME[k][index];
        ArrayList list = new ArrayList();
        for (int t = 0; t < ties.length; t++) {
            ah first = chosen[t][0];
            ah second = chosen[t][1];
            if (first == null || second == null) {
                log("confronto sem clube: " + ties[t][0] + " x " + ties[t][1] + " (grupos " + (league.yQ() == null ? -1 : league.yQ().size()) + ", tabela " + league.yK().size() + ")", null);
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
