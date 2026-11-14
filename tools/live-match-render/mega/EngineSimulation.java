package mega;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.Timer;

public final class EngineSimulation {
    private static final int FRAME_MS = 17;

    public static final class EngineTimer extends Timer {
        private static final long serialVersionUID = 1L;
        boolean on;
        long startedAt;
        EngineTimer(int delay) {
            super(delay, null);
            setInitialDelay(delay);
            setRepeats(false);
        }
        @Override public void start() { on = true; startedAt = SimClock.time; }
        @Override public void restart() { start(); }
        @Override public void stop() { on = false; }
        @Override public boolean isRunning() { return on; }
    }

    public static final class Host extends JPanel {
        private static final long serialVersionUID = 1L;
        static int GT;
        static int dB = 1;
        static int d = 700;
        static Boolean GZ = Boolean.TRUE;
        EngineTimer GO;
        Boolean GU = Boolean.FALSE;
        int GV = -1;
        int GW = 0;
        ArrayList<Object> vK = new ArrayList<Object>();
        Object KS;
        JLabel Hn = new JLabel("0 x 0");
        JLabel Ll = new JLabel("0'");
        EngineSimulation sim;
        public void qa() { sim.qa(); }
        public void a(Object row, Object match, Object action, int index) { sim.show((Act) action); }
    }

    public static final class Team {
        private final String name;
        Team(String name) { this.name = name; }
        public String getNome() { return name; }
        public int[] kj() { return new int[] {0, 0, 0, 0}; }
    }

    public static final class Player {
        private final String name;
        private final int position;
        private final int side;
        Player(String name, int position, int side) {
            this.name = name;
            this.position = position;
            this.side = side;
        }
        public String getNome() { return name; }
        public int getPosicao() { return position; }
        public int getLado() { return side; }
    }

    public static final class Act {
        final int type;
        final int subtype;
        final int minute;
        final int half;
        final Team team;
        final Player actor;
        final boolean pauses;
        final String label;
        boolean done;
        long shownAt = -1;
        long visualAt = -1;
        long cornerAt = -1;
        long activeAt = -1;
        Act(String label, int type, int subtype, int minute, int half, Team team, Player actor, boolean pauses) {
            this.label = label;
            this.type = type;
            this.subtype = subtype;
            this.minute = minute;
            this.half = half;
            this.team = team;
            this.actor = actor;
            this.pauses = pauses;
        }
        public int b() { return type; }
        public int el() { return subtype; }
        public int em() { return minute; }
        public int en() { return half; }
        public Object cu() { return team; }
        public Object eo() { return actor; }
        public Object ep() { return null; }
        public String er() { return null; }
        public boolean isDone() { return done; }
    }

    public static final class Match {
        final ArrayList<Object> actions = new ArrayList<Object>();
        final Map<String, List<Act>> script = new HashMap<String, List<Act>>();
        final List<String> calls = new ArrayList<String>();
        final Team home = new Team("Casa FC");
        final Team away = new Team("Fora FC");
        final ArrayList<Object> homePlayers = new ArrayList<Object>();
        final ArrayList<Object> awayPlayers = new ArrayList<Object>();
        final int[] score = new int[2];
        Match() {
            int[] positions = {0, 1, 2, 2, 1, 3, 3, 3, 3, 4, 4};
            int[] lado = {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0};
            for (int k = 0; k < 11; k++) {
                homePlayers.add(new Player("Casa " + (k + 1), positions[k], lado[k]));
                awayPlayers.add(new Player("Fora " + (k + 1), positions[k], lado[k]));
            }
        }
        public ArrayList<Object> hE() { return actions; }
        public void q(int minute, int half) {
            calls.add(half + ":" + minute);
            List<Act> list = script.get(half + ":" + minute);
            if (list != null) actions.addAll(list);
        }
        public int[] ib() { return new int[] {0, 0, 0}; }
        public int[] hA() { return new int[] {0, 0}; }
        public int[] hB() { return new int[] {0, 0}; }
        public int[] hC() { return new int[] {0, 0}; }
        public int[] hD() { return new int[] {0, 0}; }
        public int[] hz() { return new int[] {50, 50}; }
        public Object hc() { return home; }
        public Object hd() { return away; }
        public int dX() { return 0; }
        public ArrayList<Object> hp() { return homePlayers; }
        public ArrayList<Object> hq() { return awayPlayers; }
        public ArrayList<Object> hl() { return homePlayers; }
        public ArrayList<Object> hm() { return awayPlayers; }
    }

    public static final class Row {
        final Match match;
        Row(Match match) { this.match = match; }
        public Boolean ei() { return Boolean.TRUE; }
        public Object tR() { return match; }
        public Object tV() { return null; }
        public String ik() { return null; }
    }

    private final Host host = new Host();
    private final Match match = new Match();
    private final LiveMatchPanel panel;
    private final Method tick;
    private final Map<String, Field> fields = new HashMap<String, Field>();
    private long dialogUntil;
    private boolean restartAfterDialog;
    private final int dialogMs;
    private final List<Act> acts = new ArrayList<Act>();
    private final List<Long> goalMoments = new ArrayList<Long>();
    private long lastGoalMoment = -100000L;
    private final List<Long> penaltyMoments = new ArrayList<Long>();
    private boolean penaltySeen;
    private long pauseRequestedAt = -1;
    private final Map<String, Long> injuryIcons = new HashMap<String, Long>();
    private final Map<String, Long> cardMoments = new HashMap<String, Long>();
    private boolean cornerSeen;
    private int restartGoalShots;
    private double aerialGapMax = -1;
    private int aerialSamples;
    private int aerialFar;
    private boolean finalPassedBefore;
    private double ownGoalDeflectionMs = -1;
    private int stageBefore;
    private final List<Double> offFieldGoalX = new ArrayList<Double>();

    private EngineSimulation(int delay, long seed, int startMinute, int startHalf, int dialogMs) throws Exception {
        SimClock.reset();
        Host.GT = startMinute;
        Host.dB = startHalf;
        Host.d = delay;
        Host.GZ = Boolean.TRUE;
        this.dialogMs = dialogMs;
        host.sim = this;
        host.GO = new EngineTimer(delay);
        host.vK.add(new Row(match));
        host.KS = match;
        Constructor<LiveMatchPanel> constructor = LiveMatchPanel.class.getDeclaredConstructor(JPanel.class);
        constructor.setAccessible(true);
        panel = constructor.newInstance(host);
        ((Timer) field("timer").get(panel)).stop();
        panel.setSize(900, 420);
        field("random").set(panel, new Random(seed));
        tick = LiveMatchPanel.class.getDeclaredMethod("tickUnsafe");
        tick.setAccessible(true);
        host.GO.start();
    }

    private Field field(String name) throws Exception {
        Field cached = fields.get(name);
        if (cached != null) return cached;
        Field found = LiveMatchPanel.class.getDeclaredField(name);
        found.setAccessible(true);
        fields.put(name, found);
        return found;
    }

    private boolean has(String name) {
        try { field(name); return true; } catch (Exception ignored) { return false; }
    }

    private Object get(String name) throws Exception { return field(name).get(panel); }
    private double d(String name) throws Exception { return ((Number) get(name)).doubleValue(); }
    private int i(String name) throws Exception { return ((Number) get(name)).intValue(); }
    private boolean b(String name) throws Exception { return Boolean.TRUE.equals(get(name)); }
    private int opt(String name) throws Exception { return has(name) ? ((Number) get(name)).intValue() : 0; }

    private Act add(String label, int type, int subtype, int minute, int half, int teamSide, int actorSide, int actorIndex,
                    boolean pauses) {
        Team team = teamSide == 0 ? match.home : match.away;
        Player actor = (Player) (actorSide == 0 ? match.homePlayers : match.awayPlayers).get(actorIndex);
        Act act = new Act(label, type, subtype, minute, half, team, actor, pauses);
        String key = half + ":" + minute;
        List<Act> list = match.script.get(key);
        if (list == null) { list = new ArrayList<Act>(); match.script.put(key, list); }
        list.add(act);
        acts.add(act);
        return act;
    }

    void qa() {
        Host.GT++;
        if (Host.dB == 1 && Host.GT > 48) {
            Host.GT = 0;
            Host.dB = 2;
        } else if (Host.dB == 2 && Host.GT >= 51) {
            host.GU = Boolean.TRUE;
            return;
        }
        host.Ll.setText(Host.GT + "'");
        try {
            LiveMatchPanel.engineStep(match, Host.GT, Host.dB);
        } catch (Throwable error) {
            throw new RuntimeException(error);
        }
        for (Object value : new ArrayList<Object>(match.actions)) {
            Act act = (Act) value;
            if (act.done || act.half != Host.dB || act.minute > Host.GT) continue;
            show(act);
        }
        if (SimClock.dialog) {
            restartAfterDialog = true;
            return;
        }
        if (host.GV >= 0) {
            Host.GZ = Boolean.FALSE;
            SimClock.dialog = true;
            dialogUntil = SimClock.time + dialogMs;
            restartAfterDialog = true;
            return;
        }
        host.GO.restart();
    }

    void show(Act act) {
        if (act.done) return;
        act.done = true;
        act.shownAt = SimClock.time;
        if (act.type == 1) {
            int side = act.team == match.home ? 0 : 1;
            match.score[side]++;
            host.Hn.setText(match.score[0] + " x " + match.score[1]);
        }
        if (act.pauses && !SimClock.dialog) {
            SimClock.dialog = true;
            dialogUntil = SimClock.time + dialogMs;
            restartAfterDialog = false;
        }
    }

    private void frame() throws Exception {
        SimClock.time += FRAME_MS;
        if (SimClock.dialog && SimClock.time >= dialogUntil) {
            SimClock.dialog = false;
            if (restartAfterDialog) {
                Host.GZ = Boolean.TRUE;
                host.GV = -1;
                host.GO.restart();
            }
            restartAfterDialog = false;
        }
        if (!SimClock.dialog && host.GO.on && SimClock.time - host.GO.startedAt >= Host.d && !Boolean.TRUE.equals(host.GU)) {
            host.GO.on = false;
            qa();
        }
        SimClock.runLater();
        field("lastTickNanos").set(panel, Long.valueOf(System.nanoTime() - FRAME_MS * 1000000L));
        tick.invoke(panel);
        SimClock.runLater();
        observe();
    }

    @SuppressWarnings("unchecked")
    private void observe() throws Exception {
        long now = SimClock.time;
        double x = d("ballX"), y = d("ballY");
        int goalStage = i("pendingGoalStage");
        boolean arrived = stageBefore == 2 && goalStage == 0 && Math.abs(y - .5) < .12;
        if (arrived || (x > 1.0 || x < 0) && Math.abs(y - .5) < .10) {
            if (now - lastGoalMoment > 2500L) {
                if (System.getProperty("trace") != null) System.out.println(String.format(Locale.ROOT, "GOALMOMENT t=%d x=%.3f y=%.3f stage=%d restart=%d amb=%d", now, x, y, i("pendingGoalStage"), opt("restartPlay"), opt("ambientShotPhase")));
                goalMoments.add(Long.valueOf(now));
                offFieldGoalX.add(Double.valueOf(x));
            } else if (!offFieldGoalX.isEmpty()) {
                double last = offFieldGoalX.get(offFieldGoalX.size() - 1).doubleValue();
                if (Math.abs(x - .5) > Math.abs(last - .5)) offFieldGoalX.set(offFieldGoalX.size() - 1, Double.valueOf(x));
            }
            lastGoalMoment = now;
        }
        if (i("penaltyPhase") != 0 && !penaltySeen) { penaltyMoments.add(Long.valueOf(now)); penaltySeen = true; }
        if (i("penaltyPhase") == 0) penaltySeen = false;
        if (opt("restartPlay") == 2) cornerSeen = true;
        for (String key : (Collection<String>) get("injured")) if (!injuryIcons.containsKey(key)) injuryIcons.put(key, Long.valueOf(now));
        for (String key : (Collection<String>) get("yellowCarded")) if (!cardMoments.containsKey("y" + key)) cardMoments.put("y" + key, Long.valueOf(now));
        for (String key : (Collection<String>) get("redCarded")) if (!cardMoments.containsKey("r" + key)) cardMoments.put("r" + key, Long.valueOf(now));
        boolean finalPassed = b("goalFinalPassed");
        if (finalPassed && !finalPassedBefore && b("curveActive") && i("pendingGoalStage") == 1) {
            Object[] team = (Object[]) get(i("pendingGoalSide") == 0 ? "home" : "away");
            Object scorer = team[i("pendingGoalActor")];
            double gap = Math.hypot(dot(scorer, "currentX") - d("plannedSpotX"), dot(scorer, "currentY") - d("plannedSpotY"));
            aerialSamples++;
            if (System.getProperty("trace") != null) System.out.println(String.format(Locale.ROOT, "AERIAL t=%d gap=%.3f variant=%d hurry=%s force=%s gt=%d", now, gap, i("goalVariant"), get("hurryMode"), get("forceShot"), Host.GT));
            aerialGapMax = Math.max(aerialGapMax, gap);
            if (gap > .20) aerialFar++;
        }
        finalPassedBefore = finalPassed;
        int stage = i("pendingGoalStage");
        if (stage == 2 && stageBefore == 1 && b("ownGoalActive")) ownGoalDeflectionMs = i("moveDuration");
        stageBefore = stage;
        for (Act act : acts) {
            if (act.activeAt < 0 && act.type == 1 && stage == 1) act.activeAt = now;
            if (act.type == 1 && act.subtype == 5 && cornerSeen && act.cornerAt < 0) act.cornerAt = now;
        }
    }

    private static double dot(Object dot, String name) throws Exception {
        Field f = dot.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f.getDouble(dot);
    }

    private String key(Act act) {
        int side = act.actor.getNome().startsWith("Casa") ? 0 : 1;
        return side + ":" + act.actor.getNome().toLowerCase(Locale.ROOT).trim();
    }

    private Map<String, Object> run(String name, double seconds, long requestPauseAfterActive) throws Exception {
        int frames = (int) (seconds * 1000 / FRAME_MS);
        long firstActive = -1;
        for (int k = 0; k < frames; k++) {
            frame();
            if (System.getProperty("trace") != null && pauseRequestedAt > 0 && k % 30 == 0 && i("pendingGoalStage") == 1) System.out.println(String.format(Locale.ROOT, "HURRY t=%d stage=%d var=%d poss=%d/%d actor=%d flight=%s loose=%s esc=%d", SimClock.time - pauseRequestedAt, i("pendingGoalStage"), i("goalVariant"), i("possessingSide"), i("possessingPlayer"), i("pendingGoalActor"), get("ballInFlight"), get("looseBall"), i("escalation")));
            if (requestPauseAfterActive > 0 && pauseRequestedAt < 0) {
                boolean building = i("pendingGoalStage") == 1 || i("cardFoulPhase") == 1 || opt("injuryPhase") == 1;
                if (building && firstActive < 0) firstActive = SimClock.time;
                if (firstActive > 0 && SimClock.time - firstActive >= requestPauseAfterActive) {
                    host.GV = 0;
                    pauseRequestedAt = SimClock.time;
                }
            }
            boolean allShown = true;
            for (Act act : acts) if (!act.done) allShown = false;
            if (allShown && k > 60 && !SimClock.dialog && i("pendingGoalStage") == 0 && !b("restartActive")) {
                for (int extra = 0; extra < 120; extra++) frame();
                break;
            }
        }
        List<Long> goals = new ArrayList<Long>(goalMoments);
        int goalIndex = 0;
        int shownBeforeVisual = 0, neverAnimated = 0, notShown = 0;
        double maxLag = 0;
        List<Map<String, Object>> events = new ArrayList<Map<String, Object>>();
        for (Act act : acts) {
            long visual = -1;
            if (act.type == 1 && act.subtype == 3) {
                visual = penaltyMoments.isEmpty() ? -1 : penaltyMoments.remove(0).longValue();
            } else if (act.type == 1) {
                if (goalIndex < goals.size()) visual = goals.get(goalIndex++).longValue();
            } else if (act.type == 2) {
                Long at = cardMoments.get("y" + key(act));
                visual = at == null ? -1 : at.longValue();
            } else if (act.type == 3 || act.type == 4) {
                Long at = cardMoments.get("r" + key(act));
                visual = at == null ? -1 : at.longValue();
            } else if (act.type == 5) {
                Long at = injuryIcons.get(key(act));
                visual = at == null ? -1 : at.longValue();
            }
            act.visualAt = visual;
            Map<String, Object> row = new LinkedHashMap<String, Object>();
            row.put("event", act.label);
            row.put("shown", Boolean.valueOf(act.shownAt >= 0));
            row.put("animated", Boolean.valueOf(visual >= 0));
            if (act.shownAt < 0) notShown++;
            if (visual < 0) neverAnimated++;
            if (act.shownAt >= 0 && visual >= 0) {
                long lag = act.shownAt - visual;
                row.put("shownAfterVisualMs", Long.valueOf(lag));
                if (lag < -80) shownBeforeVisual++;
                maxLag = Math.max(maxLag, lag);
            } else if (act.shownAt >= 0) {
                shownBeforeVisual++;
            }
            if (act.type == 5 && visual >= 0 && act.shownAt >= 0) row.put("injuryLeadMs", Long.valueOf(act.shownAt - visual));
            if (act.subtype == 5) row.put("cornerBeforeGoal", Boolean.valueOf(act.cornerAt >= 0 && (visual < 0 || act.cornerAt <= visual)));
            events.add(row);
        }
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("scenario", name);
        out.put("delayMs", Integer.valueOf(Host.d));
        out.put("events", Integer.valueOf(acts.size()));
        out.put("shownBeforeAnimation", Integer.valueOf(shownBeforeVisual));
        out.put("neverAnimated", Integer.valueOf(neverAnimated));
        out.put("notShownByEngine", Integer.valueOf(notShown));
        out.put("maxShownAfterVisualMs", Double.valueOf(maxLag));
        if (pauseRequestedAt > 0) {
            long first = Long.MAX_VALUE;
            for (Act act : acts) if (act.visualAt >= 0) first = Math.min(first, act.visualAt);
            out.put("pauseToVisualMs", first == Long.MAX_VALUE ? Long.valueOf(-1) : Long.valueOf(first - pauseRequestedAt));
        }
        if (aerialSamples > 0) {
            out.put("aerialFinalBalls", Integer.valueOf(aerialSamples));
            out.put("aerialScorerFar", Integer.valueOf(aerialFar));
            out.put("aerialScorerGapMax", Double.valueOf(Math.round(aerialGapMax * 1000) / 1000.0));
        }
        if (ownGoalDeflectionMs >= 0) out.put("ownGoalDeflectionMs", Double.valueOf(ownGoalDeflectionMs));
        int offField = 0;
        for (Double gx : offFieldGoalX) if (gx.doubleValue() > 1.0 || gx.doubleValue() < 0) offField++;
        out.put("goalsLeavingScreen", Integer.valueOf(offField));
        out.put("goalMoments", Integer.valueOf(goalMoments.size()));
        out.put("forcedReleases", Integer.valueOf(opt("syncForcedReleases")));
        out.put("panelRuleViolations", Integer.valueOf(opt("ruleViolations")));
        out.put("detail", events);
        return out;
    }

    private static Map<String, Object> scenario(String name, int delay, long seed) throws Exception {
        Random pick = new Random(seed * 131L + name.hashCode());
        int dialog = 3000;
        if (name.equals("vermelho-e-gol-dialogo-longo")) dialog = 30000;
        int startMinute = 0, startHalf = 1;
        if (name.startsWith("segundo-tempo")) startMinute = 46;
        else if (!name.startsWith("abertura")) startMinute = 20;
        EngineSimulation sim = new EngineSimulation(delay, seed, startMinute, startHalf, dialog);
        int side = pick.nextInt(2);
        int scorer = 9 + pick.nextInt(2);
        long pauseAfter = 0;
        double seconds = 140;
        if (name.equals("abertura-gol")) {
            sim.add("gol", 1, 0, 1, 1, side, side, scorer, false);
        } else if (name.equals("abertura-dois-gols")) {
            sim.add("gol", 1, 0, 1, 1, side, side, scorer, false);
            sim.add("gol", 1, 0, 1, 1, 1 - side, 1 - side, 9, false);
        } else if (name.equals("abertura-amarelo")) {
            sim.add("amarelo", 2, 0, 1, 1, side, side, 3 + pick.nextInt(5), false);
        } else if (name.equals("abertura-lesao")) {
            sim.add("lesao", 5, 0, 1, 1, side, side, 2 + pick.nextInt(8), true);
        } else if (name.equals("abertura-penalti")) {
            sim.add("penalti", 1, 3, 1, 1, side, side, scorer, false);
        } else if (name.equals("segundo-tempo-minuto-zero")) {
            sim.add("gol", 1, 0, 0, 2, side, side, scorer, false);
            sim.add("amarelo", 2, 0, 1, 2, 1 - side, 1 - side, 4, false);
            seconds = 200;
        } else if (name.equals("pausa-durante-gol")) {
            sim.add("gol", 1, 0, 22, 1, side, side, scorer, false);
            pauseAfter = 1500;
        } else if (name.equals("pausa-durante-amarelo")) {
            sim.add("amarelo", 2, 0, 22, 1, side, side, 5, false);
            pauseAfter = 600;
        } else if (name.equals("vermelho-e-gol-dialogo-longo")) {
            sim.add("vermelho", 3, 0, 22, 1, side, side, 4, true);
            sim.add("gol", 1, 0, 22, 1, 1 - side, 1 - side, 9, false);
            sim.add("gol", 1, 0, 24, 1, side, side, 10, false);
            seconds = 200;
        } else if (name.equals("lesao-no-jogo")) {
            sim.add("lesao", 5, 0, 22, 1, side, side, 2 + pick.nextInt(8), true);
        } else if (name.equals("gol-olimpico")) {
            sim.add("gol olimpico", 1, 5, 22, 1, side, side, 7, false);
        } else if (name.equals("gol-contra")) {
            sim.add("gol contra", 1, 0, 22, 1, side, 1 - side, 2 + pick.nextInt(2), false);
        }
        Map<String, Object> out = sim.run(name, seconds, pauseAfter);
        out.put("seed", Long.valueOf(seed));
        return out;
    }

    private static final String[] SCENARIOS = {
        "abertura-gol", "abertura-dois-gols", "abertura-amarelo", "abertura-lesao", "abertura-penalti",
        "segundo-tempo-minuto-zero", "pausa-durante-gol", "pausa-durante-amarelo", "vermelho-e-gol-dialogo-longo",
        "lesao-no-jogo", "gol-olimpico", "gol-contra"
    };

    public static void main(String[] args) throws Exception {
        String output = args[0];
        int seeds = Integer.parseInt(args[1]);
        String[] speeds = args[2].split(",");
        StringBuilder json = new StringBuilder("[\n");
        boolean first = true;
        for (String speed : speeds) {
            int delay = Integer.parseInt(speed.trim());
            for (String name : SCENARIOS) {
                for (int seed = 1; seed <= seeds; seed++) {
                    Map<String, Object> row;
                    try {
                        row = scenario(name, delay, seed);
                    } catch (Throwable error) {
                        row = new LinkedHashMap<String, Object>();
                        row.put("scenario", name);
                        row.put("delayMs", Integer.valueOf(delay));
                        row.put("seed", Long.valueOf(seed));
                        Throwable cause = error.getCause() != null ? error.getCause() : error;
                        row.put("error", String.valueOf(cause));
                    }
                    if (!first) json.append(",\n");
                    first = false;
                    json.append(toJson(row));
                }
            }
        }
        json.append("\n]\n");
        Writer writer = new OutputStreamWriter(new FileOutputStream(new File(output)), "UTF-8");
        try {
            writer.write(json.toString());
        } finally {
            writer.close();
        }
    }

    @SuppressWarnings("unchecked")
    private static String toJson(Object value) {
        if (value == null) return "null";
        if (value instanceof String) return "\"" + ((String) value).replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
        if (value instanceof Number || value instanceof Boolean) return String.valueOf(value);
        if (value instanceof Map) {
            StringBuilder out = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<String, Object> entry : ((Map<String, Object>) value).entrySet()) {
                if (!first) out.append(", ");
                first = false;
                out.append(toJson(entry.getKey())).append(": ").append(toJson(entry.getValue()));
            }
            return out.append("}").toString();
        }
        if (value instanceof List) {
            StringBuilder out = new StringBuilder("[");
            boolean first = true;
            for (Object item : (List<Object>) value) {
                if (!first) out.append(", ");
                first = false;
                out.append(toJson(item));
            }
            return out.append("]").toString();
        }
        return toJson(String.valueOf(value));
    }
}
