package mega;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import javax.swing.JPanel;
import javax.swing.Timer;

public final class TacticalSimulation {
    public static final class FakeHost extends JPanel {
        private static final long serialVersionUID = 1L;
        static int GT = 10;
        static int dB = 1;
        Timer GO;
        Boolean GU = Boolean.FALSE;
        int GV = -1;
        Boolean GZ = Boolean.TRUE;
    }

    public static final class FakeNamed {
        private final String name;
        FakeNamed(String name) { this.name = name; }
        public String getNome() { return name; }
    }

    public static final class FakeAction {
        private final int type;
        private final int minute;
        private final FakeNamed team;
        private final FakeNamed actor;
        FakeAction(int type, int minute, FakeNamed team, FakeNamed actor) {
            this.type = type;
            this.minute = minute;
            this.team = team;
            this.actor = actor;
        }
        public int b() { return type; }
        public int el() { return 0; }
        public int em() { return minute; }
        public int en() { return 1; }
        public Object cu() { return team; }
        public Object eo() { return actor; }
        public Object ep() { return null; }
        public String er() { return null; }
        public boolean isDone() { return false; }
    }

    private static final double CONTACT = .024;
    private static final int FRAME_MS = 17;
    private final Map<String, Field> fields = new LinkedHashMap<String, Field>();
    private final LiveMatchPanel panel;
    private final Object[] home;
    private final Object[] away;
    private final Method tick;
    private final FakeHost host;

    private TacticalSimulation(int delay, long seed) throws Exception {
        host = new FakeHost();
        Timer clock = new Timer(delay, null);
        clock.setInitialDelay(delay);
        clock.start();
        host.GO = clock;
        Constructor<LiveMatchPanel> constructor = LiveMatchPanel.class.getDeclaredConstructor(JPanel.class);
        constructor.setAccessible(true);
        panel = constructor.newInstance(host);
        ((Timer) field("timer").get(panel)).stop();
        panel.setSize(900, 420);
        Field random = field("random");
        random.set(panel, new Random(seed));
        home = (Object[]) field("home").get(panel);
        away = (Object[]) field("away").get(panel);
        for (int i = 0; i < 11; i++) {
            setDot(home[i], "name", "Casa " + (i + 1));
            setDot(home[i], "fullName", "Casa " + (i + 1));
            setDot(away[i], "name", "Fora " + (i + 1));
            setDot(away[i], "fullName", "Fora " + (i + 1));
        }
        set("openingKickoffDone", Boolean.TRUE);
        set("engineStateInitialized", Boolean.TRUE);
        set("engineMinute", Integer.valueOf(10));
        set("engineHalf", Integer.valueOf(1));
        tick = LiveMatchPanel.class.getDeclaredMethod("tickUnsafe");
        tick.setAccessible(true);
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
    private void set(String name, Object value) throws Exception { field(name).set(panel, value); }
    private double d(String name) throws Exception { return ((Number) get(name)).doubleValue(); }
    private int i(String name) throws Exception { return ((Number) get(name)).intValue(); }
    private boolean b(String name) throws Exception { return Boolean.TRUE.equals(get(name)); }
    private int opt(String name) throws Exception { return opt(name, 0); }
    private int opt(String name, int fallback) throws Exception { return has(name) ? i(name) : fallback; }

    private static Field dotField(Object dot, String name) throws Exception {
        Field f = dot.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f;
    }

    private static double dx(Object dot) throws Exception { return dotField(dot, "currentX").getDouble(dot); }
    private static double dy(Object dot) throws Exception { return dotField(dot, "currentY").getDouble(dot); }
    private static boolean active(Object dot) throws Exception { return dotField(dot, "active").getBoolean(dot); }
    private static void setDot(Object dot, String name, Object value) throws Exception { dotField(dot, name).set(dot, value); }

    private void place(Object dot, double x, double y) throws Exception {
        setDot(dot, "currentX", Double.valueOf(x));
        setDot(dot, "currentY", Double.valueOf(y));
        setDot(dot, "targetX", Double.valueOf(x));
        setDot(dot, "targetY", Double.valueOf(y));
        setDot(dot, "velocityX", Double.valueOf(0));
        setDot(dot, "velocityY", Double.valueOf(0));
    }

    private long step() throws Exception {
        set("lastTickNanos", Long.valueOf(System.nanoTime() - FRAME_MS * 1000000L));
        set("lastRealMillis", Long.valueOf(System.currentTimeMillis() - FRAME_MS));
        long started = System.nanoTime();
        tick.invoke(panel);
        return System.nanoTime() - started;
    }

    private static double progress(int side, double x) { return side == 0 ? x : 1.0 - x; }

    private static double segmentGap(double ax, double ay, double bx, double by, double px, double py) {
        double full = Math.hypot(bx - ax, by - ay);
        if (full > .07) {
            ax += (bx - ax) / full * .035;
            ay += (by - ay) / full * .035;
        }
        double vx = bx - ax, vy = by - ay;
        double length = vx * vx + vy * vy;
        double t = length <= 1e-9 ? 0 : Math.max(0, Math.min(1, ((px - ax) * vx + (py - ay) * vy) / length));
        double cx = ax + vx * t - px, cy = ay + vy * t - py;
        return Math.sqrt(cx * cx + cy * cy);
    }

    private double offsideLine(int attackingSide) throws Exception {
        Object[] defenders = attackingSide == 0 ? away : home;
        double first = -1, second = -1;
        for (Object dot : defenders) {
            if (!active(dot)) continue;
            double p = progress(attackingSide, dx(dot));
            if (p > first) { second = first; first = p; }
            else if (p > second) second = p;
        }
        return Math.max(.5, second);
    }

    private Map<String, Object> openPlay(int delay, long seed, double seconds) throws Exception {
        int frames = (int) Math.round(seconds * 1000 / FRAME_MS);
        double[] lastHome = new double[22];
        double[] lastAway = new double[22];
        double lastBallX = d("ballX"), lastBallY = d("ballY");
        boolean wasFlight = false;
        int lastSide = i("possessingSide");
        long totalNanos = 0, worstNanos = 0;
        List<Long> costs = new ArrayList<Long>();
        int passes = 0, forward = 0, backward = 0, lateral = 0, switches = 0, through = 0;
        int intercepted = 0, blockedLane = 0, offsideReceptions = 0, pingPong = 0;
        int possessionChanges = 0, carrierGap = 0, ballJumps = 0, playerJumps = 0;
        double laneSum = 0, lengthSum = 0;
        int swarmFrames = 0, swarmSum = 0, offsideStanding = 0, attackerFrames = 0;
        int homeFrames = 0, controlledFrames = 0;
        int[] lastPassers = {-1, -1, -1};
        double[] recentGain = new double[3];
        int dribbles = 0;
        long lastDribbleUntil = 0;
        int[] dribbleKinds = new int[7];
        int throwIns = 0, corners = 0, counters = 0, lastRestart = 0, lastCounter = -1, misplacedCorners = 0, misplacedThrows = 0;
        for (int k = 0; k < 22; k++) {
            Object dot = k < 11 ? home[k] : away[k - 11];
            lastHome[k] = dx(dot);
            lastAway[k] = dy(dot);
        }
        for (int frame = 0; frame < frames; frame++) {
            int side = i("possessingSide");
            int player = i("possessingPlayer");
            double bx = d("ballX"), by = d("ballY");
            long cost = step();
            totalNanos += cost;
            worstNanos = Math.max(worstNanos, cost);
            costs.add(Long.valueOf(cost));
            boolean flight = b("ballInFlight");
            boolean loose = b("looseBall");
            double nbx = d("ballX"), nby = d("ballY");
            if (flight && !wasFlight) {
                int receivingSide = i("receivingSide");
                int receiver = i("receivingPlayer");
                double toX = d("ballToX"), toY = d("ballToY");
                if (receivingSide >= 0 && receiver >= 0) {
                    passes++;
                    double gain = progress(side, toX) - progress(side, bx);
                    double length = Math.hypot(toX - bx, toY - by);
                    lengthSum += length;
                    if (receivingSide != side) intercepted++;
                    else {
                        if (gain > .04) forward++;
                        else if (gain < -.04) backward++;
                        else lateral++;
                        if (Math.abs(toY - by) > .34) switches++;
                        Object[] rivals = side == 0 ? away : home;
                        double gap = 9;
                        for (int r = 1; r < rivals.length; r++) {
                            if (!active(rivals[r])) continue;
                            gap = Math.min(gap, segmentGap(bx, by, toX, toY, dx(rivals[r]), dy(rivals[r])));
                        }
                        laneSum += Math.min(gap, .3);
                        if (gap < .022) blockedLane++;
                        Object[] team = side == 0 ? home : away;
                        double receiverProgress = progress(side, dx(team[receiver]));
                        double line = offsideLine(side);
                        if (receiver > 0 && receiverProgress > line + .012 && receiverProgress > progress(side, bx) + .012) {
                            offsideReceptions++;
                        }
                        if (gain > .12 && length > .18) through++;
                        if (lastPassers[1] == receiver && lastPassers[0] == player
                                && recentGain[0] + recentGain[1] + gain < .03) pingPong++;
                        lastPassers[2] = lastPassers[1];
                        lastPassers[1] = lastPassers[0];
                        lastPassers[0] = player;
                        recentGain[2] = recentGain[1];
                        recentGain[1] = recentGain[0];
                        recentGain[0] = gain;
                    }
                }
            }
            wasFlight = flight;
            int newSide = i("possessingSide");
            if (newSide != lastSide && !loose) {
                possessionChanges++;
                lastSide = newSide;
                lastPassers[0] = lastPassers[1] = lastPassers[2] = -1;
            }
            if (!flight && !loose && (!has("restartPlay") || i("restartPlay") == 0)) {
                Object[] team = newSide == 0 ? home : away;
                int carrier = i("possessingPlayer");
                if (carrier >= 0 && carrier < 11 && Math.hypot(dx(team[carrier]) - nbx, dy(team[carrier]) - nby) > CONTACT * 1.6) {
                    carrierGap++;
                }
                controlledFrames++;
                if (newSide == 0) homeFrames++;
            }
            if (Math.hypot(nbx - lastBallX, nby - lastBallY) > .05) ballJumps++;
            lastBallX = nbx;
            lastBallY = nby;
            Object[] defending = newSide == 0 ? away : home;
            int near = 0;
            for (int r = 1; r < 11; r++) {
                if (active(defending[r]) && Math.hypot(dx(defending[r]) - nbx, dy(defending[r]) - nby) < .12) near++;
            }
            swarmSum += near;
            if (near >= 4) swarmFrames++;
            Object[] attacking = newSide == 0 ? home : away;
            double line = offsideLine(newSide);
            for (int r = 1; r < 11; r++) {
                if (!active(attacking[r])) continue;
                attackerFrames++;
                double p = progress(newSide, dx(attacking[r]));
                if (p > line + .03 && p > progress(newSide, nbx) + .03) offsideStanding++;
            }
            for (int k = 0; k < 22; k++) {
                Object dot = k < 11 ? home[k] : away[k - 11];
                double x = dx(dot), y = dy(dot);
                if (Math.hypot(x - lastHome[k], y - lastAway[k]) > .012) playerJumps++;
                lastHome[k] = x;
                lastAway[k] = y;
            }
            if (has("dribbleUntil")) {
                long until = ((Number) get("dribbleUntil")).longValue();
                if (until != 0 && until != lastDribbleUntil) {
                    dribbles++;
                    if (has("dribbleKind")) dribbleKinds[i("dribbleKind")]++;
                }
                lastDribbleUntil = until;
            }
            if (has("restartPlay")) {
                int restart = i("restartPlay");
                if (restart == 2 && i("restartPhase") >= 1 && Math.min(nbx, 1 - nbx) > .03) misplacedCorners++;
                if (restart == 1 && i("restartPhase") >= 1 && Math.min(nby, 1 - nby) > .03) misplacedThrows++;
                if (restart != lastRestart && restart == 1) throwIns++;
                if (restart != lastRestart && restart == 2) corners++;
                lastRestart = restart;
                int counterSide = i("counterSide");
                if (counterSide >= 0 && counterSide != lastCounter) counters++;
                lastCounter = counterSide;
            }
        }
        java.util.Collections.sort(costs);
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        double minutes = seconds / 60.0;
        out.put("delayMs", Integer.valueOf(delay));
        out.put("seed", Long.valueOf(seed));
        out.put("seconds", Double.valueOf(seconds));
        out.put("passes", Integer.valueOf(passes));
        out.put("passesPerMinute", round(passes / minutes));
        out.put("forwardShare", share(forward, passes - intercepted));
        out.put("backwardShare", share(backward, passes - intercepted));
        out.put("lateralShare", share(lateral, passes - intercepted));
        out.put("switchesOfPlay", Integer.valueOf(switches));
        out.put("progressivePasses", Integer.valueOf(through));
        out.put("passesToRival", Integer.valueOf(intercepted));
        out.put("passesThroughRival", Integer.valueOf(blockedLane));
        out.put("meanLaneClearance", round(laneSum / Math.max(1, passes - intercepted)));
        out.put("meanPassLength", round(lengthSum / Math.max(1, passes)));
        out.put("offsideReceptions", Integer.valueOf(offsideReceptions));
        out.put("pingPongReturns", Integer.valueOf(pingPong));
        out.put("possessionChanges", Integer.valueOf(possessionChanges));
        out.put("homeControlShare", share(homeFrames, controlledFrames));
        out.put("carrierDetachedFrames", Integer.valueOf(carrierGap));
        out.put("ballJumpFrames", Integer.valueOf(ballJumps));
        out.put("playerJumpFrames", Integer.valueOf(playerJumps));
        out.put("meanDefendersNearBall", round(swarmSum / (double) frames));
        out.put("swarmFrameShare", share(swarmFrames, frames));
        out.put("offsidePositionShare", share(offsideStanding, attackerFrames));
        out.put("dribbles", Integer.valueOf(dribbles));
        out.put("throwIns", Integer.valueOf(throwIns));
        out.put("corners", Integer.valueOf(corners));
        out.put("misplacedRestartFrames", Integer.valueOf(misplacedCorners + misplacedThrows));
        out.put("counterAttacks", Integer.valueOf(counters));
        out.put("dribbleKinds", java.util.Arrays.toString(dribbleKinds));
        out.put("meanTickMicros", round(totalNanos / 1000.0 / frames));
        out.put("p99TickMicros", round(costs.get((int) (costs.size() * .99)).longValue() / 1000.0));
        out.put("worstTickMicros", round(worstNanos / 1000.0));
        return out;
    }

    private Map<String, Object> scenario(String name, double[][] homeSpots, double[][] awaySpots, int carrier, long seed)
            throws Exception {
        for (int k = 0; k < 11; k++) {
            place(home[k], homeSpots[k][0], homeSpots[k][1]);
            place(away[k], awaySpots[k][0], awaySpots[k][1]);
        }
        Object c = home[carrier];
        set("possessingSide", Integer.valueOf(0));
        set("possessingPlayer", Integer.valueOf(carrier));
        set("looseBall", Boolean.FALSE);
        set("ballInFlight", Boolean.FALSE);
        set("ballX", Double.valueOf(dx(c) + .01));
        set("ballY", Double.valueOf(dy(c)));
        set("controlUntil", Long.valueOf(0));
        double startX = dx(c) + .01, startY = dy(c);
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("scenario", name);
        out.put("seed", Long.valueOf(seed));
        String outcome = "none";
        for (int frame = 0; frame < 240; frame++) {
            step();
            if (b("ballInFlight")) {
                int rs = i("receivingSide"), rp = i("receivingPlayer");
                double toX = d("ballToX"), toY = d("ballToY");
                double gain = toX - startX;
                double gap = 9;
                for (int r = 1; r < 11; r++) gap = Math.min(gap, segmentGap(startX, startY, toX, toY, dx(away[r]), dy(away[r])));
                outcome = rs != 0 ? "rival" : rp == carrier ? "self" : gain > .04 ? "forward" : gain < -.04 ? "back" : "lateral";
                out.put("receiver", Integer.valueOf(rp));
                out.put("gain", round(gain));
                out.put("lateralShift", round(Math.abs(toY - startY)));
                out.put("laneClearance", round(gap));
                out.put("offside", Boolean.valueOf(rs == 0 && rp > 0 && dx(home[rp]) > offsideLineX() + .012 && dx(home[rp]) > startX));
                break;
            }
            if (has("dribbleUntil") && ((Number) get("dribbleUntil")).longValue() != 0) { outcome = "dribble"; break; }
            if (b("tackleActive") || i("possessingSide") != 0) { outcome = "turnover"; break; }
        }
        if ("none".equals(outcome) && Math.hypot(d("ballX") - startX, d("ballY") - startY) > .04) outcome = "carry";
        out.put("outcome", outcome);
        return out;
    }

    private double offsideLineX() throws Exception { return offsideLine(0); }

    private static Double round(double value) { return Double.valueOf(Math.round(value * 1000.0) / 1000.0); }
    private static Double share(int part, int total) { return round(total <= 0 ? 0 : part / (double) total); }

    private static double[][] baseHome() {
        return new double[][] {{.06,.50},{.20,.16},{.18,.38},{.18,.62},{.20,.84},{.36,.18},{.34,.40},{.34,.60},{.36,.82},{.50,.38},{.50,.62}};
    }

    private static double[][] baseAway() {
        return new double[][] {{.94,.50},{.80,.16},{.82,.38},{.82,.62},{.80,.84},{.66,.18},{.66,.40},{.66,.60},{.66,.82},{.56,.40},{.56,.60}};
    }

    private static Object[] scenarios() {
        List<Object[]> list = new ArrayList<Object[]>();
        double[][] h = baseHome(), a = baseAway();
        h[6] = new double[] {.46,.50}; h[2] = new double[] {.30,.44}; h[9] = new double[] {.58,.50};
        a[9] = new double[] {.49,.47}; a[10] = new double[] {.48,.54}; a[6] = new double[] {.60,.50};
        list.add(new Object[] {"A-pressao-dupla", h, a, Integer.valueOf(6)});
        h = baseHome(); a = baseAway();
        h[5] = new double[] {.56,.12}; h[8] = new double[] {.56,.86}; h[6] = new double[] {.48,.30};
        a[5] = new double[] {.60,.10}; a[6] = new double[] {.60,.22}; a[7] = new double[] {.62,.32}; a[9] = new double[] {.58,.16};
        a[10] = new double[] {.52,.26}; a[8] = new double[] {.66,.40}; a[4] = new double[] {.80,.44};
        list.add(new Object[] {"B-corredor-oposto-livre", h, a, Integer.valueOf(5)});
        h = baseHome(); a = baseAway();
        h[7] = new double[] {.40,.50}; h[9] = new double[] {.62,.36}; h[10] = new double[] {.60,.66}; h[8] = new double[] {.52,.84};
        a = new double[][] {{.94,.50},{.82,.20},{.84,.40},{.84,.60},{.82,.80},{.36,.30},{.38,.62},{.30,.50},{.33,.80},{.28,.40},{.30,.66}};
        list.add(new Object[] {"C-contra-ataque", h, a, Integer.valueOf(7)});
        h = baseHome(); a = baseAway();
        h[7] = new double[] {.58,.50}; h[10] = new double[] {.82,.46}; h[9] = new double[] {.70,.30};
        a[2] = new double[] {.76,.40}; a[3] = new double[] {.76,.58}; a[1] = new double[] {.75,.18}; a[4] = new double[] {.75,.82};
        a[6] = new double[] {.64,.42}; a[7] = new double[] {.64,.58};
        list.add(new Object[] {"D-linha-de-impedimento", h, a, Integer.valueOf(7)});
        h = baseHome(); a = new double[][] {{.94,.50},{.82,.26},{.84,.42},{.84,.58},{.82,.74},{.74,.24},{.73,.42},{.73,.58},{.74,.76},{.66,.42},{.66,.58}};
        h[3] = new double[] {.46,.56};
        list.add(new Object[] {"E-defesa-organizada", h, a, Integer.valueOf(3)});
        h = baseHome(); a = baseAway();
        h[2] = new double[] {.12,.40}; h[3] = new double[] {.12,.62}; h[6] = new double[] {.24,.46};
        a[9] = new double[] {.16,.36}; a[10] = new double[] {.18,.60}; a[6] = new double[] {.28,.48}; a[5] = new double[] {.26,.24};
        list.add(new Object[] {"F-saida-pressionada", h, a, Integer.valueOf(2)});
        return list.toArray();
    }

    public static void main(String[] args) {
        try {
            run(args);
        } catch (Throwable error) {
            error.printStackTrace();
            System.exit(1);
        }
        System.exit(0);
    }

    private void sheet(String output, double seconds, int columns, int rows, double interval) throws Exception {
        int width = 900, height = 420;
        double scale = .5;
        int cellW = (int) (width * scale), cellH = (int) (height * scale);
        java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(cellW * columns, cellH * rows,
                java.awt.image.BufferedImage.TYPE_INT_RGB);
        java.awt.Graphics2D g = image.createGraphics();
        Method paint = LiveMatchPanel.class.getDeclaredMethod("paintComponent", java.awt.Graphics.class);
        paint.setAccessible(true);
        int warm = (int) Math.round(Math.abs(seconds) * 1000 / FRAME_MS);
        for (int k = 0; k < warm; k++) {
            step();
            if (seconds < 0 && i("restartPlay") == 2) {
                seconds = k * FRAME_MS / 1000.0;
                if (System.getProperty("trace") != null) {
                    for (int q = 0; q < 200; q++) {
                        System.out.println(String.format(Locale.ROOT, "%d ball=%.3f,%.3f to=%.3f,%.3f from=%.3f,%.3f flight=%s phase=%d restart=%d side=%d taker=%d loose=%s",
                                q, d("ballX"), d("ballY"), d("ballToX"), d("ballToY"), d("ballFromX"), d("ballFromY"), get("ballInFlight"), i("restartPhase"), i("restartPlay"), i("restartPlaySide"), i("restartTaker"), get("looseBall")));
                        step();
                    }
                }
                break;
            }
        }
        int every = (int) Math.round(interval * 1000 / FRAME_MS);
        for (int cell = 0; cell < columns * rows; cell++) {
            for (int k = 0; k < every; k++) step();
            java.awt.Graphics2D cellGraphics = (java.awt.Graphics2D) g.create((cell % columns) * cellW, (cell / columns) * cellH, cellW, cellH);
            cellGraphics.scale(scale, scale);
            paint.invoke(panel, cellGraphics);
            cellGraphics.setColor(java.awt.Color.YELLOW);
            cellGraphics.setFont(new java.awt.Font("Dialog", java.awt.Font.BOLD, 22));
            String label = "t=" + String.format(Locale.ROOT, "%.1f", seconds + (cell + 1) * interval) + "s posse="
                    + (i("possessingSide") == 0 ? "azul" : "vermelho") + (i("restartPlay") == 1 ? " LATERAL" : i("restartPlay") == 2 ? " ESCANTEIO" : "")
                    + (i("counterSide") >= 0 ? " CONTRA" : "") + (((Number) get("dribbleUntil")).longValue() != 0 ? " DRIBLE" + i("dribbleKind") : "");
            cellGraphics.drawString(label, 14, 30);
            cellGraphics.dispose();
        }
        g.dispose();
        javax.imageio.ImageIO.write(image, "png", new File(output));
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> inject(int delay, long seed, int type, boolean duringRestart, int minute) throws Exception {
        Random pick = new Random(seed * 7919L);
        FakeNamed homeTeam = new FakeNamed("Casa FC"), awayTeam = new FakeNamed("Fora FC");
        set("homeTeamRef", homeTeam);
        set("awayTeamRef", awayTeam);
        int warm = (int) ((4 + pick.nextInt(30)) * 1000L / FRAME_MS);
        for (int k = 0; k < warm; k++) step();
        boolean restartSeen = false;
        if (duringRestart) {
            for (int k = 0; k < 120000 / FRAME_MS && !restartSeen; k++) {
                step();
                if (opt("restartPlay") != 0 && opt("restartPhase") >= 1) restartSeen = true;
            }
        }
        boolean restartBefore = opt("restartPlay") != 0;
        boolean counterBefore = opt("counterSide", -1) >= 0;
        boolean dribbleBefore = ((Number) get("dribbleUntil")).longValue() != 0;
        int side = pick.nextInt(2);
        FakeNamed actor = new FakeNamed((side == 0 ? "Casa " : "Fora ") + (type == 1 ? 10 : 4 + pick.nextInt(4)));
        FakeAction action = new FakeAction(type, minute, side == 0 ? homeTeam : awayTeam, actor);
        set("preEventActive", Boolean.TRUE);
        set("preEventRemaining", Integer.valueOf(1));
        set("preEventDeadline", Long.valueOf(Long.MAX_VALUE));
        set("preEventStarted", get("virtualNow"));
        ((List<Object>) get("queuedEngineActions")).add(action);
        double lastX = d("ballX"), lastY = d("ballY");
        int frames = 0, jumps = 0;
        boolean restartAborted = false, started = false;
        int climaxFrame = -1;
        for (; frames < 30000 / FRAME_MS; frames++) {
            step();
            if (restartBefore && opt("restartPlay") == 0) restartAborted = true;
            if (i("pendingGoalStage") != 0 || i("cardFoulPhase") != 0) started = true;
            double x = d("ballX"), y = d("ballY");
            if (Math.hypot(x - lastX, y - lastY) > .05) jumps++;
            lastX = x;
            lastY = y;
            if (!b("preEventActive")) { climaxFrame = frames; break; }
        }
        boolean goalInNet = type != 1 || d("ballX") > .96 || d("ballX") < .04;
        int resumed = -1;
        for (int k = 0; k < 15000 / FRAME_MS; k++) {
            boolean before = b("ballInFlight");
            step();
            if (i("pendingGoalStage") == 0 && i("cardFoulPhase") == 0 && !b("restartActive") && !b("kickoffInProgress")
                    && !before && b("ballInFlight") && i("receivingSide") >= 0) { resumed = k; break; }
        }
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("delayMs", Integer.valueOf(delay));
        out.put("seed", Long.valueOf(seed));
        out.put("type", type == 1 ? "gol" : "amarelo");
        out.put("restartBefore", Boolean.valueOf(restartBefore));
        out.put("counterBefore", Boolean.valueOf(counterBefore));
        out.put("dribbleBefore", Boolean.valueOf(dribbleBefore));
        out.put("restartAborted", Boolean.valueOf(restartAborted || !restartBefore));
        out.put("animationStarted", Boolean.valueOf(started));
        out.put("climaxSeconds", climaxFrame < 0 ? Double.valueOf(-1) : round(climaxFrame * FRAME_MS / 1000.0));
        out.put("ballInNetAtClimax", Boolean.valueOf(goalInNet));
        out.put("ballJumps", Integer.valueOf(jumps));
        out.put("playResumedSeconds", resumed < 0 ? Double.valueOf(-1) : round(resumed * FRAME_MS / 1000.0));
        return out;
    }

    private static void run(String[] args) throws Exception {
        if ("events".equals(args[0])) {
            StringBuilder json = new StringBuilder("[\n");
            boolean first = true;
            int runs = Integer.parseInt(args[2]);
            for (String raw : args[3].split(",")) {
                int delay = Integer.parseInt(raw.trim());
                for (int r = 0; r < runs; r++) {
                    for (int type : new int[] {1, 2}) {
                        TacticalSimulation sim = new TacticalSimulation(delay, 7000L + r);
                        Map<String, Object> result = sim.inject(delay, 7000L + r, type, r % 2 == 0, 11);
                        if (!first) json.append(",\n");
                        first = false;
                        json.append("  ").append(toJson(result));
                        sim.host.GO.stop();
                    }
                }
            }
            json.append("\n]\n");
            PrintWriter writer = new PrintWriter(new FileWriter(new File(args[1])));
            writer.print(json);
            writer.close();
            return;
        }
        if ("sheet".equals(args[0])) {
            TacticalSimulation sim = new TacticalSimulation(Integer.parseInt(args[2]), Long.parseLong(args[3]));
            sim.set("homeColor", new java.awt.Color(12, 64, 196));
            sim.set("awayColor", new java.awt.Color(200, 22, 34));
            sim.set("awayAccent", new java.awt.Color(16, 16, 16));
            sim.sheet(args[1], Double.parseDouble(args[4]), 3, 4, Double.parseDouble(args[5]));
            sim.host.GO.stop();
            return;
        }
        String output = args[0];
        double seconds = Double.parseDouble(args[1]);
        int seeds = Integer.parseInt(args[2]);
        int scenarioSeeds = Integer.parseInt(args[3]);
        String[] delays = args[4].split(",");
        StringBuilder json = new StringBuilder("{\n  \"openPlay\": [\n");
        boolean first = true;
        for (String raw : delays) {
            int delay = Integer.parseInt(raw.trim());
            for (int s = 0; s < seeds; s++) {
                long seed = 1000L + s;
                TacticalSimulation sim = new TacticalSimulation(delay, seed);
                Map<String, Object> result = sim.openPlay(delay, seed, seconds);
                if (!first) json.append(",\n");
                first = false;
                json.append("    ").append(toJson(result));
                sim.host.GO.stop();
            }
        }
        json.append("\n  ],\n  \"scenarios\": [\n");
        first = true;
        for (Object raw : scenarios()) {
            Object[] spec = (Object[]) raw;
            for (int s = 0; s < scenarioSeeds; s++) {
                TacticalSimulation sim = new TacticalSimulation(1200, 5000L + s);
                Map<String, Object> result = sim.scenario((String) spec[0], (double[][]) spec[1], (double[][]) spec[2],
                        ((Integer) spec[3]).intValue(), 5000L + s);
                if (!first) json.append(",\n");
                first = false;
                json.append("    ").append(toJson(result));
                sim.host.GO.stop();
            }
        }
        json.append("\n  ]\n}\n");
        PrintWriter writer = new PrintWriter(new FileWriter(new File(output)));
        writer.print(json);
        writer.close();
    }

    private static String toJson(Map<String, Object> map) {
        StringBuilder out = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            if (!first) out.append(", ");
            first = false;
            out.append('"').append(entry.getKey()).append("\": ");
            Object value = entry.getValue();
            if (value instanceof Number || value instanceof Boolean) out.append(String.format(Locale.ROOT, "%s", value));
            else out.append('"').append(String.valueOf(value)).append('"');
        }
        return out.append('}').toString();
    }
}
