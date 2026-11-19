package best;

import c.a;
import components.aD;
import f.B;
import f.f;
import f.G;
import f.s;
import f.z;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

public final class CompBrasil2026 {
    private static final int BRAZIL = 29;
    private static final int SERIE_D_GROUPS = 16;
    private static final int SERIE_D_TEAMS = 96;
    private static final int PLAYOFF_CODE = 1097;
    private static final String[] STATES = {"AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
            "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"};
    private static final String[] REGION_ORDER = {"AM", "RR", "AC", "RO", "TO", "GO", "DF", "MT", "PA", "AP", "MA",
            "CE", "PI", "RN", "PB", "PE", "SE", "AL", "BA", "MS", "MG", "ES", "RJ", "SP", "PR", "SC", "RS"};
    private static final String[] DUPLICATES = {"interlimeirasp_bra", "brasilpelotas_bra"};
    private static boolean busy;

    private CompBrasil2026() {
    }

    private static void log(String message, Throwable error) {
        System.err.println("[CompBrasil2026] " + message + (error == null ? "" : ": " + error));
    }

    private static int stateIndex(String uf) {
        for (int i = 0; i < STATES.length; i++) {
            if (STATES[i].equals(uf)) return i;
        }
        return -1;
    }

    private static int season() {
        return a.SR.op() + a.SR.H() - 1;
    }

    static boolean isSerieD(s league) {
        if (league == null || league.getDivisao() != 4 || league.yQ().size() != SERIE_D_GROUPS) return false;
        Z country = league.iq();
        return country != null && country.jc() == BRAZIL;
    }

    public static ArrayList serieD(int n) {
        if (busy || n != SERIE_D_TEAMS || a.SR == null) return null;
        try {
            Z brazil = a.SR.o(BRAZIL);
            if (brazil == null) return null;
            ArrayList fallback;
            busy = true;
            try {
                fallback = w.Q(n);
            } finally {
                busy = false;
            }
            ArrayList picked = a.SR.H() == 1 ? official(brazil, fallback) : career(brazil, fallback);
            if (picked == null || picked.size() != SERIE_D_TEAMS) {
                log("participantes incompletos; mantida a selecao original", null);
                return null;
            }
            return picked;
        } catch (Throwable error) {
            log("falha ao montar a Serie D", error);
            return null;
        }
    }

    private static ah byFile(Z brazil, String file) {
        if (file == null || file.isEmpty()) return null;
        ArrayList teams = brazil.jg();
        for (int i = 0; i < teams.size(); i++) {
            ah team = (ah) teams.get(i);
            if (file.equals(team.jY())) return team;
        }
        return null;
    }

    private static boolean duplicate(Object team) {
        String file = ((ah) team).jY();
        for (int i = 0; i < DUPLICATES.length; i++) {
            if (DUPLICATES[i].equals(file)) return true;
        }
        return false;
    }

    private static boolean free(ah team) {
        return team != null && team.getDivisao() == 0 && !team.ko() && !duplicate(team);
    }

    private static ArrayList official(Z brazil, ArrayList fallback) {
        String[][] groups = CompBrasil2026Data.SERIE_D_FILES;
        String[][] states = CompBrasil2026Data.SERIE_D_STATES;
        ah[][] grid = new ah[SERIE_D_GROUPS][6];
        HashSet used = new HashSet();
        for (int g = 0; g < SERIE_D_GROUPS; g++) {
            for (int r = 0; r < 6; r++) {
                ah team = byFile(brazil, groups[g][r]);
                if (free(team) && used.add(team)) {
                    grid[g][r] = team;
                } else if (team != null) {
                    log("clube oficial indisponivel para a Serie D: " + groups[g][r] + " (divisao " + team.getDivisao() + ")", null);
                } else if (groups[g][r] != null && !groups[g][r].isEmpty()) {
                    log("arquivo oficial ausente no jogo: " + groups[g][r], null);
                }
            }
        }
        int filled = 0;
        for (int g = 0; g < SERIE_D_GROUPS; g++) {
            for (int r = 0; r < 6; r++) {
                if (grid[g][r] != null) continue;
                ah substitute = substitute(fallback, used, stateIndex(states[g][r]));
                if (substitute == null) return null;
                grid[g][r] = substitute;
                used.add(substitute);
                filled++;
            }
        }
        if (filled > 0) log(filled + " vagas oficiais sem clube no jogo, completadas pela selecao original", null);
        return arrange(grid);
    }

    private static ah substitute(ArrayList pool, HashSet used, int state) {
        for (int i = 0; i < pool.size(); i++) {
            ah team = (ah) pool.get(i);
            if (!used.contains(team) && !duplicate(team) && team.getEstado() == state) return team;
        }
        for (int i = 0; i < pool.size(); i++) {
            ah team = (ah) pool.get(i);
            if (!used.contains(team) && !duplicate(team)) return team;
        }
        return null;
    }

    private static ArrayList arrange(ah[][] grid) {
        ArrayList result = new ArrayList();
        for (int r = 0; r < 6; r++) {
            for (int g = 0; g < SERIE_D_GROUPS; g++) result.add(grid[g][r]);
        }
        return result;
    }

    private static ArrayList career(Z brazil, ArrayList fallback) {
        ArrayList chosen = new ArrayList();
        ArrayList relegated = a.SR.bY();
        for (int i = 0; i < relegated.size(); i++) {
            ah team = (ah) relegated.get(i);
            if (free(team) && !chosen.contains(team)) chosen.add(team);
        }
        ArrayList ranking = a.SR.bx();
        String[] rnf = CompBrasil2026Data.RNF_2026;
        for (int rank = 0; rank < rnf.length; rank++) {
            int slots = rank == 0 ? 4 : rank <= 8 ? 3 : 2;
            int state = stateIndex(rnf[rank]);
            for (int i = 0; i < ranking.size() && slots > 0; i++) {
                aD entry = (aD) ranking.get(i);
                ah team = entry.vD();
                if (entry.getEstado() == state && free(team) && !chosen.contains(team)) {
                    chosen.add(team);
                    slots--;
                }
            }
        }
        for (int i = 0; i < fallback.size() && chosen.size() < SERIE_D_TEAMS; i++) {
            ah team = (ah) fallback.get(i);
            if (free(team) && !chosen.contains(team)) chosen.add(team);
        }
        ArrayList all = brazil.jg();
        for (int i = 0; i < all.size() && chosen.size() < SERIE_D_TEAMS; i++) {
            ah team = (ah) all.get(i);
            if (free(team) && !chosen.contains(team)) chosen.add(team);
        }
        if (chosen.size() < SERIE_D_TEAMS) return null;
        while (chosen.size() > SERIE_D_TEAMS) chosen.remove(chosen.size() - 1);
        return regional(chosen);
    }

    private static int region(ah team) {
        int state = team.getEstado();
        String uf = state >= 0 && state < STATES.length ? STATES[state] : "";
        for (int i = 0; i < REGION_ORDER.length; i++) {
            if (REGION_ORDER[i].equals(uf)) return i;
        }
        return REGION_ORDER.length;
    }

    private static ArrayList regional(ArrayList teams) {
        ArrayList sorted = new ArrayList(teams);
        Collections.sort(sorted, new Comparator() {
            public int compare(Object a, Object b) {
                return region((ah) a) - region((ah) b);
            }
        });
        ah[][] grid = new ah[SERIE_D_GROUPS][6];
        int[] size = new int[SERIE_D_GROUPS];
        ArrayList pending = new ArrayList(sorted);
        for (int g = 0; g < SERIE_D_GROUPS; g++) {
            Map perState = new HashMap();
            for (int i = 0; i < pending.size() && size[g] < 6; ) {
                ah team = (ah) pending.get(i);
                Integer state = Integer.valueOf(team.getEstado());
                Integer count = (Integer) perState.get(state);
                int current = count == null ? 0 : count.intValue();
                if (current < 3) {
                    grid[g][size[g]++] = team;
                    perState.put(state, Integer.valueOf(current + 1));
                    pending.remove(i);
                } else {
                    i++;
                }
            }
            while (size[g] < 6 && !pending.isEmpty()) grid[g][size[g]++] = (ah) pending.remove(0);
        }
        return arrange(grid);
    }

    private static int[] campaign(ah team, s league, z knockout) {
        int[] group = team.d(league);
        int[] total = {group[0], group[2], group[7], group[5]};
        if (knockout == null) return total;
        List rounds = knockout.zp();
        for (int r = 0; r < rounds.size(); r++) {
            G round = (G) rounds.get(r);
            add(total, team, round.zW());
            add(total, team, round.zX());
        }
        return total;
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

    private static Comparator byCampaign(final s league, final z knockout) {
        final Map cache = new HashMap();
        return new Comparator() {
            int[] of(Object team) {
                int[] value = (int[]) cache.get(team);
                if (value == null) {
                    value = campaign((ah) team, league, knockout);
                    cache.put(team, value);
                }
                return value;
            }

            public int compare(Object a, Object b) {
                int[] x = of(a);
                int[] y = of(b);
                for (int i = 0; i < x.length; i++) {
                    if (x[i] != y[i]) return y[i] - x[i];
                }
                return 0;
            }
        };
    }

    private static void betterHostsSecondLeg(ArrayList list, Comparator order) {
        for (int i = 0; i + 1 < list.size(); i += 2) {
            if (order.compare(list.get(i), list.get(i + 1)) < 0) {
                Object first = list.get(i);
                list.set(i, list.get(i + 1));
                list.set(i + 1, first);
            }
        }
    }

    public static void pairing(G round, z knockout, ArrayList list, int index) {
        try {
            if (knockout == null || list == null || !(knockout.yT() instanceof B)) return;
            B owner = (B) knockout.yT();
            if (owner.zO() != BRAZIL) return;
            if (knockout.zf() == 1099 && owner.ip() == 2 && list.size() == 4) {
                serieBPlayoff(round, owner, list);
                return;
            }
            if (knockout.zf() == PLAYOFF_CODE) {
                round.fb(2129);
                return;
            }
            s league = owner.yi();
            if (!isSerieD(league) || knockout != league.yY()) return;
            Comparator order = byCampaign(league, knockout);
            if (index == 0 && list.size() == 64) {
                secondPhase(list);
            } else if ((index == 1 || index == 2) && list.size() % 8 == 0) {
                bracket(list);
                betterHostsSecondLeg(list, order);
            } else if (index == 3 && list.size() == 8) {
                quarterFinals(list, order);
            } else {
                if (index == 4 && list.size() == 4) playoffs(owner, league, knockout);
                betterHostsSecondLeg(list, order);
            }
        } catch (Throwable error) {
            log("falha no chaveamento", error);
        }
    }

    private static void serieBPlayoff(G round, B owner, ArrayList list) {
        Object third = list.get(0);
        Object fourth = list.get(1);
        Object fifth = list.get(2);
        Object sixth = list.get(3);
        list.clear();
        list.add(sixth);
        list.add(third);
        list.add(fifth);
        list.add(fourth);
        round.fb(2129);
    }

    private static void secondPhase(ArrayList list) {
        ArrayList result = new ArrayList();
        for (int pair = 0; pair < 8; pair++) {
            int p = pair * 2 * 4;
            int q = (pair * 2 + 1) * 4;
            result.add(list.get(q + 3));
            result.add(list.get(p));
            result.add(list.get(p + 2));
            result.add(list.get(q + 1));
            result.add(list.get(p + 3));
            result.add(list.get(q));
            result.add(list.get(q + 2));
            result.add(list.get(p + 1));
        }
        list.clear();
        list.addAll(result);
    }

    private static void bracket(ArrayList list) {
        int[] pattern = {0, 5, 1, 4, 2, 7, 3, 6};
        ArrayList winners = new ArrayList(list);
        ArrayList result = new ArrayList();
        for (int block = 0; block < winners.size(); block += 8) {
            for (int i = 0; i < pattern.length; i++) result.add(winners.get(block + pattern[i]));
        }
        list.clear();
        list.addAll(result);
    }

    private static void quarterFinals(ArrayList list, Comparator order) {
        ArrayList ranked = new ArrayList(list);
        Collections.sort(ranked, order);
        int[] pattern = {7, 0, 4, 3, 6, 1, 5, 2};
        list.clear();
        for (int i = 0; i < pattern.length; i++) list.add(ranked.get(pattern[i]));
    }

    private static void playoffs(B owner, s league, z knockout) throws Exception {
        if (owner.BR() != null || knockout.zp().size() < 4) return;
        G quarters = (G) knockout.zp().get(3);
        ArrayList losers = new ArrayList(quarters.zV());
        losers.removeAll(quarters.zY());
        if (losers.size() != 4) return;
        Collections.sort(losers, byCampaign(league, knockout));
        ArrayList order = new ArrayList();
        order.add(losers.get(3));
        order.add(losers.get(0));
        order.add(losers.get(2));
        order.add(losers.get(1));
        boolean[] legs = {true, true, true, true, true, true, true};
        z playoff = new z(null, 4, owner.b(), 1, legs, owner, PLAYOFF_CODE);
        Field field = B.class.getDeclaredField("agA");
        field.setAccessible(true);
        field.set(owner, playoff);
        new G().a(playoff, order, 0, true, 0, 0, owner.b(), false);
    }

    public static boolean supercopa(at cup) {
        try {
            Field country = cup.getClass().getDeclaredField("pais");
            country.setAccessible(true);
            if (country.getInt(cup) != BRAZIL) return false;
            Z brazil = a.SR.o(BRAZIL);
            if (brazil == null || brazil.eb() == null || brazil.eb().isEmpty()) return false;
            int previous = a.SR.H() - 1;
            B serieA = (B) brazil.eb().get(0);
            ah champion = serieA.cv(previous);
            ah[] copa = brazil.bk(previous);
            ah opponent = null;
            if (copa != null && copa[0] != champion) {
                opponent = copa[0];
            } else {
                for (int k = 0; k < serieA.mn().size(); k++) {
                    i record = (i) serieA.mn().get(k);
                    if (record.H() == previous) opponent = record.cf();
                }
            }
            cup.getClass().getMethod("b", ah.class, ah.class).invoke(cup, champion, opponent);
            return true;
        } catch (Throwable error) {
            log("falha na Supercopa Rei", error);
            return false;
        }
    }

    public static L[] mainPhase(B division) {
        try {
            z playoff = division.BR();
            s league = division.yi();
            if (playoff == null || playoff.zf() != PLAYOFF_CODE || !isSerieD(league) || league.yY() == null) return null;
            return new L[]{league.yY()};
        } catch (Throwable error) {
            return null;
        }
    }

    public static void divisionOrder(ArrayList teams, Z country) {
        try {
            if (country.jc() != BRAZIL || a.SR.H() != 1 || a.SR.op() != 2026) return;
            ArrayList ordered = new ArrayList();
            String[][] divisions = CompBrasil2026Data.DIVISIONS_2026;
            for (int d = 0; d < divisions.length; d++) {
                for (int i = 0; i < divisions[d].length; i++) {
                    for (int t = 0; t < teams.size(); t++) {
                        ah team = (ah) teams.get(t);
                        if (divisions[d][i].equals(team.jY()) && !ordered.contains(team)) {
                            ordered.add(team);
                            break;
                        }
                    }
                }
                if (ordered.size() != (d + 1) * 20) {
                    log("Serie " + (char) ('A' + d) + " oficial incompleta no jogo: " + (ordered.size() - d * 20) + " de 20", null);
                    return;
                }
            }
            for (int t = 0; t < teams.size(); t++) {
                if (!ordered.contains(teams.get(t))) ordered.add(teams.get(t));
            }
            teams.clear();
            teams.addAll(ordered);
        } catch (Throwable error) {
            log("falha ao ordenar as divisoes oficiais", error);
        }
    }

    private static final int COPA_FIRST_CODE = 26101;
    private static final int COPA_FINAL_CODE = 2729;
    private static final int COPA_PHASES = 9;
    private static final String[] COPA_NAMES = {"1ª fase", "2ª fase", "3ª fase", "4ª fase", "5ª fase", "Oitavas",
            "Quartas", "Semifinal", "Final"};
    private static final int[] COPA_WAITING = {74, 4, 20};

    private static ArrayList waitingList(f cup) throws Exception {
        Field field = f.class.getDeclaredField("afU");
        field.setAccessible(true);
        ArrayList value = (ArrayList) field.get(cup);
        if (value == null) {
            value = new ArrayList();
            field.set(cup, value);
        }
        return value;
    }

    private static ArrayList waiting(f cup, int group) throws Exception {
        ArrayList all = waitingList(cup);
        int start = 0;
        for (int i = 0; i < group; i++) start += COPA_WAITING[i];
        int end = start + COPA_WAITING[group];
        if (all.size() < end) return new ArrayList();
        return new ArrayList(all.subList(start, end));
    }

    private static boolean isCopa2026(f cup) {
        z knockout = cup.yf();
        return knockout != null && knockout.zf() == 2029 && knockout.zq() == COPA_PHASES - 1;
    }

    public static String[] copaNames(f cup) {
        try {
            return isCopa2026(cup) ? COPA_NAMES : null;
        } catch (Throwable error) {
            return null;
        }
    }

    private static int rank(ah team) {
        String file = team.jY();
        String[] order = CompBrasil2026Data.RNC_FILES;
        for (int i = 0; i < order.length; i++) {
            if (order[i].equals(file)) return i;
        }
        return order.length;
    }

    private static void sortByRanking(ArrayList teams) {
        ArrayList ranked = new ArrayList();
        ArrayList unranked = new ArrayList();
        for (int i = 0; i < teams.size(); i++) {
            ah team = (ah) teams.get(i);
            if (rank(team) < CompBrasil2026Data.RNC_FILES.length) ranked.add(team);
            else unranked.add(team);
        }
        Collections.sort(ranked, new Comparator() {
            public int compare(Object x, Object y) {
                return rank((ah) x) - rank((ah) y);
            }
        });
        teams.clear();
        teams.addAll(ranked);
        teams.addAll(unranked);
    }

    private static void addPair(ArrayList pairs, Object first, Object second) {
        if (Math.random() < 0.5) {
            pairs.add(first);
            pairs.add(second);
        } else {
            pairs.add(second);
            pairs.add(first);
        }
    }

    public static boolean copa(f cup, ArrayList pool) {
        try {
            Z country = cup.yg();
            if (country == null || country.jc() != BRAZIL || season() < 2026) return false;
            ArrayList[] entries = a.SR.H() == 1 && a.SR.op() == 2026 ? copaOfficial(country, pool) : copaCareer(country, pool);
            if (entries == null) {
                log("Copa do Brasil sem participantes suficientes; formato original mantido", null);
                return false;
            }
            ArrayList third = entries[2];
            sortByRanking(third);
            ArrayList firstPhase = new ArrayList(third.subList(third.size() - 28, third.size()));
            ArrayList secondPhase = new ArrayList(third.subList(0, third.size() - 28));
            ArrayList pairs = new ArrayList();
            for (int i = 0; i < 14; i++) addPair(pairs, firstPhase.get(i), firstPhase.get(27 - i));
            boolean[] legs = {false, false, false, false, true, true, true, true, false};
            z knockout = new z(null, 128, 2, 0, legs, cup, 2029);
            knockout.ff(COPA_PHASES);
            cup.b(knockout);
            ArrayList stored = waitingList(cup);
            stored.clear();
            stored.addAll(secondPhase);
            stored.addAll(entries[1]);
            stored.addAll(entries[0]);
            G round = new G();
            round.a(knockout, pairs, 1, false, 0, 0, 2, false);
            round.fb(COPA_FIRST_CODE);
            return true;
        } catch (Throwable error) {
            log("falha ao montar a Copa do Brasil", error);
            return false;
        }
    }

    private static ArrayList[] copaOfficial(Z country, ArrayList pool) {
        ArrayList[] entries = {new ArrayList(), new ArrayList(), new ArrayList()};
        HashSet used = new HashSet();
        String[] files = CompBrasil2026Data.COPA_FILES;
        int[] criteria = CompBrasil2026Data.COPA_CRITERIA;
        ArrayList missing = new ArrayList();
        for (int i = 0; i < files.length; i++) {
            ah team = byFile(country, files[i]);
            if (team != null && used.add(team)) entries[criteria[i] - 1].add(team);
            else missing.add(new int[]{criteria[i], stateIndex(CompBrasil2026Data.COPA_STATES[i])});
        }
        for (int i = 0; i < missing.size(); i++) {
            int[] slot = (int[]) missing.get(i);
            ah substitute = substitute(pool, used, slot[1]);
            if (substitute == null) return null;
            used.add(substitute);
            entries[slot[0] - 1].add(substitute);
        }
        if (!missing.isEmpty()) log(missing.size() + " vagas da Copa do Brasil sem clube no jogo, completadas por clubes do mesmo estado", null);
        return entries[0].size() == 20 && entries[1].size() == 4 && entries[2].size() == 102 ? entries : null;
    }

    private static ArrayList[] copaCareer(Z country, ArrayList pool) {
        ArrayList[] entries = {new ArrayList(), new ArrayList(), new ArrayList()};
        HashSet used = new HashSet();
        ArrayList divisions = country.eb();
        ArrayList serieA = ((B) divisions.get(0)).yi().yK();
        for (int i = 0; i < serieA.size() && entries[0].size() < 20; i++) {
            if (used.add(serieA.get(i))) entries[0].add(serieA.get(i));
        }
        at[] regional = a.SR.bV();
        at[] sources = {regional != null && regional.length > 2 ? regional[2] : null,
                regional != null && regional.length > 3 ? regional[3] : null,
                divisions.size() > 2 ? (at) divisions.get(2) : null,
                divisions.size() > 3 ? (at) divisions.get(3) : null};
        for (int i = 0; i < sources.length; i++) {
            if (sources[i] == null) continue;
            ah champion = i < 2 ? sources[i].cS() : sources[i].cv(a.SR.H() - 1);
            if (champion != null && used.add(champion)) entries[1].add(champion);
        }
        ArrayList ranking = a.SR.bx();
        String[] rnf = CompBrasil2026Data.RNF_2026;
        for (int r = 0; r < rnf.length; r++) {
            int slots = r <= 1 ? 6 : r <= 4 ? 5 : r <= 13 ? 4 : 3;
            int state = stateIndex(rnf[r]);
            for (int i = 0; i < ranking.size() && slots > 0; i++) {
                aD entry = (aD) ranking.get(i);
                ah team = entry.vD();
                if (entry.getEstado() == state && team != null && !duplicate(team) && used.add(team)) {
                    entries[2].add(team);
                    slots--;
                }
            }
        }
        for (int i = 0; i < pool.size() && entries[1].size() < 4; i++) {
            if (!duplicate(pool.get(i)) && used.add(pool.get(i))) entries[1].add(pool.get(i));
        }
        for (int i = 0; i < pool.size() && entries[2].size() < 102; i++) {
            if (!duplicate(pool.get(i)) && used.add(pool.get(i))) entries[2].add(pool.get(i));
        }
        return entries[0].size() == 20 && entries[1].size() == 4 && entries[2].size() == 102 ? entries : null;
    }

    public static void afterTie(G round) {
        try {
            int code = round.ze();
            if (code < COPA_FIRST_CODE || code >= COPA_FIRST_CODE + COPA_PHASES - 1) return;
            z knockout = round.zT();
            if (knockout == null || !(knockout.yT() instanceof f)) return;
            f cup = (f) knockout.yT();
            int phase = code - COPA_FIRST_CODE + 1;
            ArrayList next = new ArrayList(round.zY());
            if (phase == 4) {
                next.addAll(waiting(cup, 2));
                sortByRanking(next);
                ArrayList top = new ArrayList(next.subList(0, next.size() / 2));
                ArrayList bottom = new ArrayList(next.subList(next.size() / 2, next.size()));
                Collections.shuffle(top);
                Collections.shuffle(bottom);
                next = new ArrayList();
                for (int i = 0; i < top.size(); i++) addPair(next, top.get(i), bottom.get(i));
                waitingList(cup).clear();
            } else if (phase != 7) {
                if (phase <= 2) next.addAll(waiting(cup, phase - 1));
                Collections.shuffle(next);
            }
            int nextPhase = phase + 1;
            boolean twoLegs = nextPhase >= 5 && nextPhase <= 8;
            G following = new G();
            following.a(knockout, next, Math.min(nextPhase, 8), twoLegs, 0, 0, 2, false);
            following.fb(nextPhase == COPA_PHASES ? COPA_FINAL_CODE : COPA_FIRST_CODE + nextPhase - 1);
            knockout.BH();
        } catch (Throwable error) {
            log("falha ao avancar a Copa do Brasil", error);
        }
    }

    public static boolean promotion(Z country) {
        try {
            if (country.jc() != BRAZIL || !a.SR.bk()) return false;
            ArrayList divisions = country.eb();
            if (divisions.size() != 4) return false;
            B aDiv = (B) divisions.get(0);
            B bDiv = (B) divisions.get(1);
            B cDiv = (B) divisions.get(2);
            B d = (B) divisions.get(3);
            if (!isSerieD(d.yi())) {
                migrate(bDiv, cDiv, d);
                return false;
            }
            int finished = season() - 1;
            int serieCDown = finished >= 2028 ? 6 : 2;
            aDiv.yi().ah(0, aDiv.getnRebaixados());
            bDiv.yi().ah(aDiv.getnRebaixados(), bDiv.getnRebaixados());
            cDiv.yi().ah(bDiv.getnRebaixados(), serieCDown);
            d.yi().ah(6, 0);
            ArrayList cDown = new ArrayList(cDiv.yi().yU());
            ArrayList dUp = new ArrayList(d.yi().yW());
            if (dUp.size() != 6 || cDown.size() != serieCDown) {
                log("acesso da Serie D com " + dUp.size() + " clubes e descenso da C com " + cDown.size(), null);
            }
            swap(aDiv, bDiv);
            swap(bDiv, cDiv);
            a.SR.bY().clear();
            for (int i = 0; i < cDown.size(); i++) {
                ah team = (ah) cDown.get(i);
                if (cDiv.ac(team)) continue;
                team.b(cDiv, 0);
                cDiv.yi().yK().remove(team);
                d.yi().yK().add(team);
                a.SR.bY().add(team);
            }
            for (int i = 0; i < dUp.size(); i++) {
                ah team = (ah) dUp.get(i);
                team.b(d, 1);
                d.yi().yK().remove(team);
                cDiv.yi().yK().add(team);
            }
            for (int i = 0; i < divisions.size(); i++) ((B) divisions.get(i)).yi().yI();
            d.yi().yJ();
            for (int i = 0; i < divisions.size(); i++) ((B) divisions.get(i)).BJ();
            return true;
        } catch (Throwable error) {
            log("falha no acesso e descenso", error);
            return false;
        }
    }

    private static void setField(Object target, String name, Object value) throws Exception {
        Field field = s.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(target, value);
    }

    private static void migrate(B serieB, B serieC, B serieD) {
        try {
            if (season() < 2027) return;
            s league = serieD.yi();
            if (league == null || league.ze() == 1068 || league.ze() == 1020) return;
            league.nTimes = SERIE_D_TEAMS;
            setField(league, "Zj", Integer.valueOf(SERIE_D_GROUPS));
            setField(league, "Zd", Integer.valueOf(4));
            setField(league, "duasVoltasMataMata", new boolean[]{true, true, true, true, true, true, true});
            serieD.setVagasSobemPeloMataMata(2);
            serieB.setVagasSobemPeloMataMata(2);
            serieB.b(new boolean[]{true, true, true});
            serieC.setnRebaixados(2);
            serieC.setRebaixadosDireto(2);
            log("carreira existente migrada para o formato 2026 a partir da proxima temporada", null);
        } catch (Throwable error) {
            log("falha ao migrar a carreira existente", error);
        }
    }

    private static void swap(B upper, B lower) {
        ArrayList down = new ArrayList(upper.yi().yU());
        ArrayList up = new ArrayList(lower.yi().yW());
        if (down.size() != up.size()) {
            log("listas de acesso e descenso de tamanhos diferentes entre " + upper.ip() + " e " + lower.ip(), null);
            return;
        }
        for (int i = 0; i < down.size(); i++) {
            ah relegated = (ah) down.get(i);
            ah promoted = (ah) up.get(i);
            if (upper.ac(relegated)) continue;
            relegated.b(upper, 0);
            promoted.b(lower, 1);
            upper.yi().yK().remove(relegated);
            lower.yi().yK().add(relegated);
            lower.yi().yK().remove(promoted);
            upper.yi().yK().add(promoted);
        }
    }
}
