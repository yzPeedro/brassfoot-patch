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

    public static final class FakePlayer {
        private final String name;
        private final int position;
        private final int side;
        FakePlayer(String name, int position, int side) {
            this.name = name;
            this.position = position;
            this.side = side;
        }
        public String getNome() { return name; }
        public int getPosicao() { return position; }
        public int getLado() { return side; }
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

    private Object dot(int side, int index) { return side == 0 ? home[index] : away[index]; }

    private int optFlag(String name) throws Exception {
        if (!has(name)) return 0;
        Object value = get(name);
        if (value instanceof Boolean) return ((Boolean) value).booleanValue() ? 1 : 0;
        return ((Number) value).intValue();
    }

    private boolean inPlay() throws Exception {
        return optFlag("restartPlay") == 0 && !b("restartActive") && i("cardFoulPhase") <= 1 && i("freeKickPhase") == 0
                && i("penaltyPhase") == 0 && !b("kickoffInProgress") && ((Number) get("simpleStoppageUntil")).longValue() == 0
                && i("ambientShotPhase") == 0 && i("pendingGoalStage") != 2 && d("ballX") > .01 && d("ballX") < .99
                && d("ballY") > .012 && d("ballY") < .988;
    }

    private int touching(double bx, double by, double reach) throws Exception {
        int best = -1;
        double bestGap = reach;
        for (int s = 0; s < 2; s++) {
            for (int k = 0; k < 11; k++) {
                Object o = dot(s, k);
                if (!active(o)) continue;
                double gap = Math.hypot(dx(o) - bx, dy(o) - by);
                if (gap <= bestGap) { bestGap = gap; best = s * 100 + k; }
            }
        }
        return best;
    }

    private static double speedOf(Object dot) throws Exception {
        return Math.hypot(dotField(dot, "velocityX").getDouble(dot), dotField(dot, "velocityY").getDouble(dot));
    }

    private boolean inOwnBox(int side, double x, double y) {
        double depth = 1.0 / 7.0;
        boolean deep = side == 0 ? x < depth : x > 1.0 - depth;
        return deep && Math.abs(y - .5) < .25;
    }

    private final class Audit {
        int lastTouch = -1;
        int keeperHeld = -1;
        int throwIns, corners, wrongRestarts;
        int tacklesOnKeeper, keeperStrips;
        int passes, passesToRival;
        int stationaryEpisodes, longStationary;
        double stationaryMs, stationaryRun, maxStationary;
        int whistles, whistlesWithoutContact;
        double whistleGapSum;
        double tackledSpeedSum, freeSpeedSum, tackleEntrySpeed, tackleRatioSum;
        int tackledFrames, freeFrames, tackleRatioFrames, tackleCarrier = -1;
        int backPasses, backPassesThroughBody;
        int freeAttackerPasses, freeAttackerBackPasses;
        double lineSpreadSum;
        int lineFrames, rigidLineFrames;
        int ballJumps, carrierDetached, frames;
        int finalPasses, finalPassWaits;
        double finalPassWaitMs, maxFinalPassWait, finalPassGapSum;
        boolean finalFlight, finalWaiting;
        double finalWaitRun;
        int ownGoalActor = -1, ownGoalSide = -1;
        boolean defenderControlled;
        final List<double[]> flights = new ArrayList<double[]>();

        String state() throws Exception {
            return String.format(Locale.ROOT, "side=%d player=%d loose=%s flight=%s tackle=%s cue=%d card=%d goal=%d restart=%d own=%d keeperLoss=%d last=%d ball=%.3f,%.3f to=%.3f,%.3f rs=%d rp=%d",
                    i("possessingSide"), i("possessingPlayer"), get("looseBall"), get("ballInFlight"), get("tackleActive"),
                    i("statCueActive"), i("cardFoulPhase"), i("pendingGoalStage"), optFlag("restartPlay"), optFlag("ownGoalStage"),
                    optFlag("keeperLossSide"), lastTouch, d("ballX"), d("ballY"), d("ballToX"), d("ballToY"), i("receivingSide"), i("receivingPlayer"));
        }

        void trace(String what) throws Exception {
            if (System.getProperty("trace") != null) System.out.println(what + " " + state());
        }

        double prevFromX = -1, prevFromY = -1;
        int sinceTouch, segments, segmentsAtTarget, rivalOnBall;
        String stationaryStart = "";

        String chaserGap() throws Exception {
            int cs = optFlag("looseSide"), c = optFlag("looseChaser"), r = optFlag("looseRival");
            double bx = d("ballX"), by = d("ballY");
            String out = "";
            if (c >= 0 && c < 11) out += String.format(Locale.ROOT, "%.3f", Math.hypot(dx(dot(cs, c)) - bx, dy(dot(cs, c)) - by));
            if (r >= 0 && r < 11) out += String.format(Locale.ROOT, "/%.3f", Math.hypot(dx(dot(1 - cs, r)) - bx, dy(dot(1 - cs, r)) - by));
            return out;
        }

        void frame() throws Exception {
            int preSide = i("possessingSide"), prePlayer = i("possessingPlayer");
            boolean preFlight = b("ballInFlight"), preLoose = b("looseBall"), preTackle = b("tackleActive");
            int preRestart = optFlag("restartPlay"), preCard = i("cardFoulPhase");
            boolean preFinal = b("goalFinalPassed");
            double pbx = d("ballX"), pby = d("ballY");
            Object preCarrier = prePlayer >= 0 && prePlayer < 11 ? dot(preSide, prePlayer) : null;
            double pvx = preCarrier == null ? 0 : dotField(preCarrier, "velocityX").getDouble(preCarrier);
            double pvy = preCarrier == null ? 0 : dotField(preCarrier, "velocityY").getDouble(preCarrier);
            double pcx = preCarrier == null ? 0 : dx(preCarrier), pcy = preCarrier == null ? 0 : dy(preCarrier);
            boolean preKeeperHands = !preFlight && !preLoose && prePlayer == 0 && preCarrier != null
                    && Math.hypot(pcx - pbx, pcy - pby) <= CONTACT * 1.5 && inOwnBox(preSide, pcx, pcy);
            boolean preInPlay = inPlay();
            step();
            frames++;
            boolean flight = b("ballInFlight"), loose = b("looseBall");
            double bx = d("ballX"), by = d("ballY");
            int side = i("possessingSide"), player = i("possessingPlayer");
            if (Math.hypot(bx - pbx, by - pby) > .05) ballJumps++;
            if (preKeeperHands) keeperHeld = preSide;
            if (flight && !preFlight) {
                keeperHeld = -1;
                if (side >= 0 && player >= 0 && player < 11) {
                    Object kicker = dot(side, player);
                    if (active(kicker) && Math.hypot(dx(kicker) - pbx, dy(kicker) - pby) <= CONTACT * 1.5) lastTouch = side * 100 + player;
                }
                int rs = i("receivingSide");
                double tx = d("ballToX"), ty = d("ballToY");
                flights.add(new double[] {pbx, pby, tx, ty, lastTouch});
                int passer = lastTouch;
                if (rs >= 0 && passer >= 0) {
                    int passerSide = passer / 100;
                    if (rs != passerSide) {
                        passesToRival++;
                        Object pc = preCarrier;
                        trace("RIVAL passer=" + passer + " preGap=" + (pc == null ? -1 : Math.hypot(pcx - pbx, pcy - pby)) + " pre=" + preSide + "/" + prePlayer + " preLoose=" + preLoose + " preFlight=" + preFlight + " sinceTouch=" + sinceTouch);
                    }
                    else {
                        passes++;
                        Object from = dot(passerSide, passer % 100);
                        double fx = dx(from), fy = dy(from);
                        double px = tx - pbx, py = ty - pby, pl = Math.hypot(px, py);
                        double vs = Math.hypot(pvx, pvy);
                        if (pl > .02 && passer == preSide * 100 + prePlayer) {
                            px /= pl;
                            py /= pl;
                            if (vs > .04 && (pvx * px + pvy * py) / vs < -.34) {
                                backPasses++;
                                if ((pbx - pcx) * px + (pby - pcy) * py < -.003) backPassesThroughBody++;
                            }
                        }
                        double here = progress(passerSide, fx);
                        Object[] rivals = passerSide == 0 ? away : home;
                        double nearest = 9;
                        for (int r = 1; r < 11; r++) {
                            if (active(rivals[r])) nearest = Math.min(nearest, Math.hypot(dx(rivals[r]) - fx, dy(rivals[r]) - fy));
                        }
                        if (here > .60 && nearest > .07 && passer % 100 != 0) {
                            freeAttackerPasses++;
                            if (progress(passerSide, tx) - progress(passerSide, pbx) < -.04) freeAttackerBackPasses++;
                        }
                    }
                }
                if (!preFinal && b("goalFinalPassed")) finalFlight = true;
            }
            if (!flight && preFlight && finalFlight) {
                finalFlight = false;
                finalPasses++;
                int scorerSide = i("pendingGoalSide"), scorer = i("pendingGoalActor");
                if (scorerSide >= 0 && scorer >= 0 && scorer < 11) {
                    Object s = dot(scorerSide, scorer);
                    double gap = Math.hypot(dx(s) - bx, dy(s) - by);
                    finalPassGapSum += gap;
                    if (gap > CONTACT * 1.5) { finalWaiting = true; finalWaitRun = 0; }
                }
            }
            if (finalWaiting) {
                int scorerSide = i("pendingGoalSide"), scorer = i("pendingGoalActor");
                if (scorerSide < 0 || scorer < 0 || flight
                        || Math.hypot(dx(dot(scorerSide, scorer)) - bx, dy(dot(scorerSide, scorer)) - by) <= CONTACT) {
                    finalWaiting = false;
                    if (finalWaitRun > 0) {
                        finalPassWaits++;
                        finalPassWaitMs += finalWaitRun;
                        maxFinalPassWait = Math.max(maxFinalPassWait, finalWaitRun);
                    }
                } else if (Math.hypot(bx - pbx, by - pby) < .0004) {
                    finalWaitRun += FRAME_MS;
                }
            }
            double fromX = d("ballFromX"), fromY = d("ballFromY");
            boolean segment = flight && preFlight && (Math.abs(fromX - prevFromX) > 1e-9 || Math.abs(fromY - prevFromY) > 1e-9);
            prevFromX = fromX;
            prevFromY = fromY;
            if (segment) {
                int t = touching(fromX, fromY, CONTACT * 1.5);
                if (t >= 0) lastTouch = t;
                double[] previous = flights.isEmpty() ? null : flights.get(flights.size() - 1);
                if (previous != null) {
                    segments++;
                    if (Math.hypot(previous[2] - fromX, previous[3] - fromY) < .01) segmentsAtTarget++;
                }
                flights.add(new double[] {fromX, fromY, d("ballToX"), d("ballToY"), lastTouch});
            }
            if (!flight) {
                int t = touching(bx, by, CONTACT);
                if (!loose && side >= 0 && player >= 0 && player < 11) {
                    Object c = dot(side, player);
                    if (active(c) && Math.hypot(dx(c) - bx, dy(c) - by) <= CONTACT) {
                        if (t >= 0 && t / 100 != side) {
                            rivalOnBall++;
                            if (rivalOnBall % 150 == 0) trace("ONBALL rival=" + t + " tackler=" + i("tackler") + " tackleSide=" + i("tackleSide") + " ctrl=" + (((Number) get("controlUntil")).longValue() - ((Number) get("virtualNow")).longValue()));
                        }
                        t = side * 100 + player;
                    }
                }
                if (t >= 0) sinceTouch = 0; else sinceTouch++;
                if (t >= 0) {
                    if (t != lastTouch && keeperHeld >= 0 && t / 100 != keeperHeld) keeperStrips++;
                    if (t != lastTouch) keeperHeld = -1;
                    lastTouch = t;
                }
            }
            int restart = optFlag("restartPlay");
            if (restart != 0 && preRestart == 0) {
                if (restart == 1) throwIns++;
                if (restart == 2) corners++;
                if (lastTouch >= 0 && i("restartPlaySide") == lastTouch / 100) { wrongRestarts++; trace("RESTART type=" + restart); }
            }
            if (b("tackleActive") && !preTackle && prePlayer == 0 && !preFlight && !preLoose && i("tackleSide") != preSide) tacklesOnKeeper++;
            if (b("tackleActive") && !preTackle && preCarrier != null && !preFlight && !preLoose) {
                tackleEntrySpeed = Math.hypot(pvx, pvy);
                tackleCarrier = preSide * 100 + prePlayer;
            }
            if (!b("tackleActive")) tackleCarrier = -1;
            if (tackleCarrier >= 0 && tackleEntrySpeed > .05 && side * 100 + player == tackleCarrier && !flight && !loose) {
                tackleRatioSum += speedOf(dot(side, player)) / tackleEntrySpeed;
                tackleRatioFrames++;
            }
            int card = i("cardFoulPhase");
            if (preCard == 1 && card != 1) {
                whistles++;
                int os = i("cardFoulOffenderSide"), o = i("cardFoulOffender");
                if (os >= 0 && o >= 0 && o < 11) {
                    Object off = dot(os, o);
                    double gap = Math.hypot(dx(off) - bx, dy(off) - by);
                    for (int k = 0; k < 11; k++) {
                        Object v = dot(1 - os, k);
                        if (active(v)) gap = Math.min(gap, Math.hypot(dx(off) - dx(v), dy(off) - dy(v)));
                    }
                    whistleGapSum += gap;
                    if (gap > CONTACT * 2.5) whistlesWithoutContact++;
                }
            }
            boolean nowInPlay = inPlay();
            if (frames > 90 && preInPlay && nowInPlay && !flight && touching(bx, by, CONTACT) < 0 && Math.hypot(bx - pbx, by - pby) < .0004) {
                if (stationaryRun == 0 && System.getProperty("trace") != null) stationaryStart = state() + " chaserGap=" + chaserGap();
                stationaryRun += FRAME_MS;
                stationaryMs += FRAME_MS;
            } else {
                if (stationaryRun >= 400) stationaryEpisodes++;
                if (stationaryRun >= Integer.getInteger("stationaryTrace", 900)) trace("STATIONARY start=[" + stationaryStart + "] ms=" + stationaryRun + " chaser=" + optFlag("looseChaser") + "/" + optFlag("looseSide") + " rival=" + optFlag("looseRival") + " cardEng=" + optFlag("cardFoulEngaged"));
                if (stationaryRun >= 1200) longStationary++;
                maxStationary = Math.max(maxStationary, stationaryRun);
                stationaryRun = 0;
            }
            if (!flight && !loose && side >= 0 && player >= 0 && player < 11) {
                Object c = dot(side, player);
                if (Math.hypot(dx(c) - bx, dy(c) - by) > CONTACT * 1.6 && optFlag("restartPlay") == 0) {
                    carrierDetached++;
                    if (carrierDetached % 200 == 1) trace("DETACHED gap=" + Math.hypot(dx(c) - bx, dy(c) - by) + " ra=" + get("restartActive") + " ko=" + get("kickoffInProgress") + " fk=" + i("freeKickPhase") + " pen=" + i("penaltyPhase") + " amb=" + i("ambientShotPhase") + " simple=" + get("simpleStoppageUntil"));
                }
                double want = Math.hypot(dotField(c, "targetX").getDouble(c) - dx(c), dotField(c, "targetY").getDouble(c) - dy(c));
                if (want > .03 && player != 0) {
                    if (b("tackleActive")) { tackledSpeedSum += speedOf(c); tackledFrames++; }
                    else if (nowInPlay) { freeSpeedSum += speedOf(c); freeFrames++; }
                }
            }
            if (ownGoalSide >= 0 && !flight && !loose && side == ownGoalSide && player == ownGoalActor) defenderControlled = true;
            if (nowInPlay && !loose && !flight) {
                int defending = 1 - side;
                double low = 9, high = -9;
                int count = 0;
                for (int k = 1; k < 11; k++) {
                    Object o = dot(defending, k);
                    if (!active(o) || dotField(o, "roleLine").getInt(o) != 1) continue;
                    double p = progress(defending, dx(o));
                    low = Math.min(low, p);
                    high = Math.max(high, p);
                    count++;
                }
                if (count >= 3) {
                    lineFrames++;
                    lineSpreadSum += high - low;
                    if (high - low < .02) rigidLineFrames++;
                }
            }
        }

        void put(Map<String, Object> out) {
            out.put("throwIns", Integer.valueOf(throwIns));
            out.put("corners", Integer.valueOf(corners));
            out.put("restartsToLastTouchTeam", Integer.valueOf(wrongRestarts));
            out.put("tacklesOnKeeper", Integer.valueOf(tacklesOnKeeper));
            out.put("keeperStripped", Integer.valueOf(keeperStrips));
            out.put("passes", Integer.valueOf(passes));
            out.put("passesAimedAtRival", Integer.valueOf(passesToRival));
            out.put("stationaryLooseEpisodes", Integer.valueOf(stationaryEpisodes));
            out.put("stationaryLooseOver1200ms", Integer.valueOf(longStationary));
            out.put("stationaryLooseMsPerMinute", round(stationaryMs / Math.max(1e-9, frames * FRAME_MS / 60000.0)));
            out.put("maxStationaryLooseMs", round(maxStationary));
            out.put("whistles", Integer.valueOf(whistles));
            out.put("whistlesWithoutContact", Integer.valueOf(whistlesWithoutContact));
            out.put("meanWhistleGap", round(whistleGapSum / Math.max(1, whistles)));
            out.put("carrierSpeedTackled", round(tackledSpeedSum / Math.max(1, tackledFrames)));
            out.put("carrierSpeedFree", round(freeSpeedSum / Math.max(1, freeFrames)));
            out.put("tackledSpeedRatio", round(tackleRatioSum / Math.max(1, tackleRatioFrames)));
            out.put("tackledRatioFrames", Integer.valueOf(tackleRatioFrames));
            out.put("backPasses", Integer.valueOf(backPasses));
            out.put("backPassesThroughBody", Integer.valueOf(backPassesThroughBody));
            out.put("freeAttackerPasses", Integer.valueOf(freeAttackerPasses));
            out.put("freeAttackerBackPasses", Integer.valueOf(freeAttackerBackPasses));
            out.put("meanBackLineSpread", round(lineSpreadSum / Math.max(1, lineFrames)));
            out.put("rigidBackLineShare", share(rigidLineFrames, lineFrames));
            out.put("ballJumpFrames", Integer.valueOf(ballJumps));
            out.put("rivalOnControlledBallFrames", Integer.valueOf(rivalOnBall));
            out.put("carrierDetachedFrames", Integer.valueOf(carrierDetached));
            out.put("finalPasses", Integer.valueOf(finalPasses));
            out.put("meanScorerGapAtFinalBall", round(finalPassGapSum / Math.max(1, finalPasses)));
            out.put("finalBallWaits", Integer.valueOf(finalPassWaits));
            out.put("maxFinalBallWaitMs", round(maxFinalPassWait));
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> auditPlay(int delay, long seed, double seconds) throws Exception {
        Audit audit = new Audit();
        Random pick = new Random(seed * 31L + delay);
        int frames = (int) Math.round(seconds * 1000 / FRAME_MS);
        int cueEvery = 6000 / FRAME_MS;
        int cues = 0;
        for (int frame = 0; frame < frames; frame++) {
            if (frame > 0 && frame % cueEvery == 0 && !b("preEventActive") && i("cardFoulPhase") == 0 && i("pendingGoalStage") == 0) {
                int kind = 1 + cues % 4;
                int side = pick.nextInt(2);
                if (kind == 2) side = 1 - i("possessingSide");
                if (kind == 3) side = i("possessingSide");
                cues++;
                set("preEventActive", Boolean.TRUE);
                set("preEventRemaining", Integer.valueOf(1));
                set("preEventDeadline", Long.valueOf(Long.MAX_VALUE));
                set("preEventStarted", get("virtualNow"));
                ((List<int[]>) get("statCueQueue")).add(new int[] {kind, side});
            }
            audit.frame();
        }
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("delayMs", Integer.valueOf(delay));
        out.put("seed", Long.valueOf(seed));
        out.put("seconds", Double.valueOf(seconds));
        out.put("statCues", Integer.valueOf(cues));
        audit.put(out);
        out.put("panelRuleViolations", Integer.valueOf(opt("ruleViolations")));
        return out;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> auditEvent(int delay, long seed, int kind) throws Exception {
        Random pick = new Random(seed * 7919L + kind);
        FakeNamed homeTeam = new FakeNamed("Casa FC"), awayTeam = new FakeNamed("Fora FC");
        set("homeTeamRef", homeTeam);
        set("awayTeamRef", awayTeam);
        Audit audit = new Audit();
        int warm = (int) ((4 + pick.nextInt(25)) * 1000L / FRAME_MS);
        for (int k = 0; k < warm; k++) audit.frame();
        int side = pick.nextInt(2);
        int actorIndex = kind == 1 ? 10 : kind == 9 ? 2 + pick.nextInt(2) : 2 + pick.nextInt(7);
        int actorSide = kind == 9 ? 1 - side : side;
        FakeNamed actor = new FakeNamed((actorSide == 0 ? "Casa " : "Fora ") + (actorIndex + 1));
        int type = kind == 9 ? 1 : kind;
        if (kind == 9) { audit.ownGoalSide = actorSide; audit.ownGoalActor = actorIndex; }
        FakeAction action = new FakeAction(type, 11, side == 0 ? homeTeam : awayTeam, actor);
        audit.flights.clear();
        audit.segmentsAtTarget = 0;
        set("preEventActive", Boolean.TRUE);
        set("preEventRemaining", Integer.valueOf(1));
        set("preEventDeadline", Long.valueOf(Long.MAX_VALUE));
        set("preEventStarted", get("virtualNow"));
        ((List<Object>) get("queuedEngineActions")).add(action);
        int climax = -1, frames = 0;
        int touchAtGoal = -1, goalFlights = -1, atTargetAtGoal = 0;
        for (; frames < 30000 / FRAME_MS; frames++) {
            audit.frame();
            if (type == 1 && touchAtGoal < 0 && (d("ballX") > .975 || d("ballX") < .025) && Math.abs(d("ballY") - .5) < .08) {
                touchAtGoal = audit.lastTouch;
                goalFlights = audit.flights.size();
                atTargetAtGoal = audit.segmentsAtTarget;
            }
            if (!b("preEventActive")) { climax = frames; break; }
        }
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("delayMs", Integer.valueOf(delay));
        out.put("seed", Long.valueOf(seed));
        out.put("type", kind == 1 ? "gol" : kind == 9 ? "gol-contra" : kind == 2 ? "amarelo" : "vermelho");
        out.put("climaxSeconds", climax < 0 ? Double.valueOf(-1) : round(climax * FRAME_MS / 1000.0));
        out.put("ballInNet", Boolean.valueOf(type != 1 || d("ballX") > .96 || d("ballX") < .04));
        if (kind == 9) {
            out.put("lastTouchByDefender", Boolean.valueOf(touchAtGoal == actorSide * 100 + actorIndex));
            out.put("lastTouchByDefendingTeam", Boolean.valueOf(touchAtGoal >= 0 && touchAtGoal / 100 == actorSide));
            out.put("defenderControlledBall", Boolean.valueOf(audit.defenderControlled));
            out.put("deflectionAtShotTarget", Boolean.valueOf(atTargetAtGoal > 0));
            int n = goalFlights < 0 ? audit.flights.size() : goalFlights;
            boolean onTarget = false;
            if (n >= 2) {
                double[] f = audit.flights.get(n - 2);
                double goalX = side == 0 ? 1.0 : 0.0;
                double dxv = f[2] - f[0];
                if (Math.abs(dxv) > 1e-6) {
                    double t = (goalX - f[0]) / dxv;
                    double y = f[1] + (f[3] - f[1]) * t;
                    onTarget = t > 0 && Math.abs(y - .5) < .06;
                }
            }
            out.put("shotOnTargetBeforeDeflection", Boolean.valueOf(onTarget));
            if (System.getProperty("trace") != null) {
                for (int k = Math.max(0, n - 4); k < n; k++) {
                    double[] f = audit.flights.get(k);
                    System.out.println(String.format(Locale.ROOT, "OWN side=%d flight %d from=%.3f,%.3f to=%.3f,%.3f touch=%d", side, k, f[0], f[1], f[2], f[3], (int) f[4]));
                }
            }
        }
        audit.put(out);
        out.put("panelRuleViolations", Integer.valueOf(opt("ruleViolations")));
        return out;
    }

    private Map<String, Object> auditSubstitution(int delay, long seed) throws Exception {
        Method update = LiveMatchPanel.class.getDeclaredMethod("updateLineup", home.getClass(), List.class, boolean.class);
        update.setAccessible(true);
        List<Object> players = new ArrayList<Object>();
        int[] positions = {0, 1, 2, 2, 1, 3, 3, 3, 3, 4, 4};
        int[] lado = {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0};
        for (int k = 0; k < 11; k++) {
            setDot(home[k], "known", Boolean.TRUE);
            players.add(new FakePlayer("Casa " + (k + 1), positions[k], lado[k]));
        }
        Audit audit = new Audit();
        Random pick = new Random(seed);
        int warm = (int) ((3 + pick.nextInt(15)) * 1000L / FRAME_MS);
        for (int k = 0; k < warm; k++) {
            if (k % 8 == 0) update.invoke(panel, home, players, Boolean.FALSE);
            audit.frame();
        }
        int target = -1;
        for (int k = 0; k < 60000 / FRAME_MS && target < 0; k++) {
            if (k % 8 == 0) update.invoke(panel, home, players, Boolean.FALSE);
            audit.frame();
            if (i("possessingSide") == 0 && !b("looseBall") && !b("ballInFlight") && i("possessingPlayer") > 0 && inPlay()) target = i("possessingPlayer");
        }
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("delayMs", Integer.valueOf(delay));
        out.put("seed", Long.valueOf(seed));
        if (target < 0) { out.put("swapped", Boolean.FALSE); return out; }
        String outgoing = "Casa " + (target + 1);
        players.set(target, new FakePlayer("Reserva " + (target + 1), positions[target], lado[target]));
        int swapFrame = -1;
        boolean inPlayAtSwap = false, ballRoleAtSwap = false;
        for (int k = 0; k < 40000 / FRAME_MS; k++) {
            boolean role = (i("possessingSide") == 0 && i("possessingPlayer") == target && !b("looseBall") && !b("ballInFlight"))
                    || (b("ballInFlight") && i("receivingSide") == 0 && i("receivingPlayer") == target)
                    || (b("looseBall") && i("looseSide") == 0 && i("looseChaser") == target);
            boolean playing = inPlay();
            if (k % 8 == 0) update.invoke(panel, home, players, Boolean.FALSE);
            audit.frame();
            Object o = home[target];
            if (!outgoing.equals(dotField(o, "fullName").get(o))) {
                swapFrame = k;
                inPlayAtSwap = playing && inPlay();
                ballRoleAtSwap = role;
                break;
            }
        }
        out.put("swapped", Boolean.valueOf(swapFrame >= 0));
        out.put("swapSeconds", swapFrame < 0 ? Double.valueOf(-1) : round(swapFrame * FRAME_MS / 1000.0));
        out.put("swapDuringPlay", Boolean.valueOf(inPlayAtSwap));
        out.put("swapWithBallRole", Boolean.valueOf(ballRoleAtSwap));
        return out;
    }

    private void setVelocity(Object dot, double vx, double vy) throws Exception {
        setDot(dot, "velocityX", Double.valueOf(vx));
        setDot(dot, "velocityY", Double.valueOf(vy));
    }

    private void giveBall(int side, int index) throws Exception {
        Object c = dot(side, index);
        set("possessingSide", Integer.valueOf(side));
        set("possessingPlayer", Integer.valueOf(index));
        set("looseBall", Boolean.FALSE);
        set("ballInFlight", Boolean.FALSE);
        set("tackleActive", Boolean.FALSE);
        double dir = side == 0 ? 1.0 : -1.0;
        set("ballX", Double.valueOf(dx(c) + dir * .01));
        set("ballY", Double.valueOf(dy(c)));
        set("ballFromX", Double.valueOf(dx(c) + dir * .01));
        set("ballFromY", Double.valueOf(dy(c)));
        set("ballToX", Double.valueOf(dx(c) + dir * .01));
        set("ballToY", Double.valueOf(dy(c)));
        set("footDirX", Double.valueOf(dir));
        set("footDirY", Double.valueOf(0));
        set("controlUntil", Long.valueOf(0));
        set("possessionPasses", Integer.valueOf(0));
    }

    @SuppressWarnings("unchecked")
    private void queueCue(int kind, int side) throws Exception {
        set("preEventActive", Boolean.TRUE);
        set("preEventRemaining", Integer.valueOf(1));
        set("preEventDeadline", Long.valueOf(Long.MAX_VALUE));
        set("preEventStarted", get("virtualNow"));
        ((List<int[]>) get("statCueQueue")).add(new int[] {kind, side});
    }

    private Map<String, Object> ruleScenario(String name, long seed) throws Exception {
        Audit audit = new Audit();
        audit.frames = 100;
        Map<String, Object> out = new LinkedHashMap<String, Object>();
        out.put("scenario", name);
        out.put("seed", Long.valueOf(seed));
        if ("lateral-pressionado".equals(name)) {
            double[][] h = {{.06,.50},{.30,.30},{.28,.45},{.28,.60},{.32,.80},{.46,.08},{.40,.35},{.42,.55},{.40,.75},{.55,.40},{.56,.60}};
            for (int k = 0; k < 11; k++) {
                place(home[k], h[k][0], h[k][1]);
                place(away[k], k == 0 ? .94 : h[k][0] + .012, k == 0 ? .5 : h[k][1] + .008);
            }
            place(away[5], .475, .095);
            giveBall(0, 5);
            boolean restart = false;
            int restartSide = -1, touchSide = -1;
            for (int f = 0; f < 420 && !restart; f++) {
                audit.frame();
                if (optFlag("restartPlay") == 1) {
                    restart = true;
                    restartSide = i("restartPlaySide");
                    touchSide = audit.lastTouch / 100;
                }
            }
            out.put("throwIn", Boolean.valueOf(restart));
            out.put("throwToLastTouchTeam", Boolean.valueOf(restart && restartSide == touchSide));
        } else if ("goleiro-com-a-bola".equals(name)) {
            double[][] h = {{.05,.50},{.20,.20},{.18,.42},{.18,.58},{.20,.80},{.34,.25},{.32,.45},{.33,.60},{.35,.78},{.46,.40},{.47,.60}};
            for (int k = 0; k < 11; k++) {
                place(home[k], h[k][0], h[k][1]);
                place(away[k], k == 0 ? .94 : Math.max(.10, h[k][0] + .05), k == 0 ? .5 : h[k][1] + .02);
            }
            place(away[10], .09, .52);
            giveBall(0, 0);
            set("controlUntil", Long.valueOf(((Number) get("virtualNow")).longValue() + 400L));
            queueCue(2, 1);
            boolean changed = false;
            for (int f = 0; f < 480 && !changed; f++) {
                audit.frame();
                if (i("possessingSide") == 1 && !b("looseBall") && !b("ballInFlight")) changed = true;
            }
            out.put("possessionChanged", Boolean.valueOf(changed));
            out.put("tacklesOnKeeper", Integer.valueOf(audit.tacklesOnKeeper));
            out.put("keeperStripped", Integer.valueOf(audit.keeperStrips));
            out.put("passesAimedAtRival", Integer.valueOf(audit.passesToRival));
        } else if ("atacante-livre".equals(name)) {
            double[][] h = {{.06,.50},{.30,.20},{.28,.42},{.28,.58},{.30,.80},{.48,.25},{.46,.45},{.47,.60},{.50,.78},{.72,.50},{.58,.62}};
            double[][] a = {{.95,.50},{.90,.15},{.92,.40},{.92,.62},{.90,.85},{.62,.20},{.60,.40},{.60,.62},{.62,.85},{.52,.40},{.52,.60}};
            for (int k = 0; k < 11; k++) {
                place(home[k], h[k][0], h[k][1]);
                place(away[k], a[k][0], a[k][1]);
            }
            giveBall(0, 9);
            int backward = 0, passes = 0, forwardMoves = 0;
            double startX = dx(home[9]);
            for (int f = 0; f < 240; f++) {
                boolean before = b("ballInFlight");
                double bx = d("ballX");
                int carrier = i("possessingPlayer");
                audit.frame();
                if (!before && b("ballInFlight") && carrier == 9 && i("receivingSide") == 0) {
                    passes++;
                    if (d("ballToX") - bx < -.04) backward++;
                    break;
                }
                if (i("possessingSide") != 0) break;
            }
            out.put("carrierProgress", round(dx(home[9]) - startX));
            out.put("passes", Integer.valueOf(passes));
            out.put("backwardPasses", Integer.valueOf(backward));
        } else if ("desarme-por-tras".equals(name)) {
            double[][] h = {{.06,.50},{.25,.20},{.24,.42},{.24,.58},{.25,.80},{.34,.25},{.40,.50},{.35,.65},{.36,.80},{.52,.30},{.52,.70}};
            double[][] a = {{.94,.50},{.80,.15},{.80,.40},{.80,.62},{.80,.85},{.62,.20},{.33,.50},{.62,.62},{.62,.85},{.66,.40},{.66,.60}};
            for (int k = 0; k < 11; k++) {
                place(home[k], h[k][0], h[k][1]);
                place(away[k], a[k][0], a[k][1]);
            }
            setVelocity(home[6], .11, 0);
            setVelocity(away[6], .12, 0);
            giveBall(0, 6);
            queueCue(2, 1);
            boolean won = false;
            for (int f = 0; f < 420 && !won; f++) {
                audit.frame();
                if (System.getProperty("tackleTrace") != null && f % 6 == 0) {
                    Object c = dot(i("possessingSide"), i("possessingPlayer"));
                    System.out.println(String.format(Locale.ROOT, "f=%d speed=%.3f want=%.3f tackle=%s tackler=%d gap=%.3f evade=%d ctrl=%d", f, speedOf(c),
                            Math.hypot(dotField(c, "targetX").getDouble(c) - dx(c), dotField(c, "targetY").getDouble(c) - dy(c)), get("tackleActive"), i("tackler"),
                            Math.hypot(dx(away[i("tackler") < 0 ? 6 : i("tackler")]) - d("ballX"), dy(away[i("tackler") < 0 ? 6 : i("tackler")]) - d("ballY")),
                            ((Number) get("tackleEvadeUntil")).longValue() - ((Number) get("virtualNow")).longValue(),
                            ((Number) get("controlUntil")).longValue() - ((Number) get("virtualNow")).longValue()));
                }
                if (i("possessingSide") == 1) won = true;
            }
            out.put("recovered", Boolean.valueOf(won));
            out.put("tackledSpeedRatio", round(audit.tackleRatioSum / Math.max(1, audit.tackleRatioFrames)));
            out.put("passesAimedAtRival", Integer.valueOf(audit.passesToRival));
        } else if ("passe-para-tras".equals(name)) {
            double[][] h = {{.06,.50},{.25,.20},{.24,.42},{.24,.58},{.25,.80},{.40,.50},{.45,.30},{.45,.70},{.55,.50},{.70,.35},{.70,.65}};
            for (int k = 0; k < 11; k++) {
                place(home[k], h[k][0], h[k][1]);
                place(away[k], k == 0 ? .94 : h[k][0] + .02, k == 0 ? .5 : h[k][1] + .01);
            }
            place(away[5], .70, .80);
            setVelocity(home[8], .10, 0);
            giveBall(0, 8);
            int backPasses = 0, throughBody = 0;
            for (int f = 0; f < 300; f++) {
                boolean before = b("ballInFlight");
                double bx = d("ballX"), by = d("ballY");
                int carrier = i("possessingPlayer");
                Object c = home[Math.max(0, Math.min(10, carrier))];
                double cx = dx(c), cy = dy(c);
                audit.frame();
                if (!before && b("ballInFlight") && i("possessingSide") == 0 && i("receivingSide") == 0) {
                    double px = d("ballToX") - bx, py = d("ballToY") - by, pl = Math.hypot(px, py);
                    if (px < -.04 && pl > .02) {
                        backPasses++;
                        if ((bx - cx) * px / pl + (by - cy) * py / pl < -.003) throughBody++;
                    }
                    break;
                }
                if (i("possessingSide") != 0) break;
            }
            out.put("backPasses", Integer.valueOf(backPasses));
            out.put("backPassesThroughBody", Integer.valueOf(throughBody));
        }
        return out;
    }

    private static void appendRow(StringBuilder json, boolean first, Map<String, Object> row) {
        if (!first) json.append(",\n");
        json.append("  ").append(toJson(row));
    }

    private static void runAudit(String[] args) throws Exception {
        String output = args[1];
        double seconds = Double.parseDouble(args[2]);
        int seeds = Integer.parseInt(args[3]);
        int eventRuns = Integer.parseInt(args[4]);
        String[] delays = args[5].split(",");
        StringBuilder json = new StringBuilder("{\n\"play\": [\n");
        boolean first = true;
        for (String raw : delays) {
            int delay = Integer.parseInt(raw.trim());
            for (int s = 0; s < seeds; s++) {
                TacticalSimulation sim = new TacticalSimulation(delay, 1000L + s);
                appendRow(json, first, sim.auditPlay(delay, 1000L + s, seconds));
                first = false;
                sim.host.GO.stop();
            }
        }
        json.append("\n],\n\"events\": [\n");
        first = true;
        for (String raw : delays) {
            int delay = Integer.parseInt(raw.trim());
            for (int r = 0; r < eventRuns; r++) {
                for (int kind : new int[] {1, 9, 2, 3}) {
                    TacticalSimulation sim = new TacticalSimulation(delay, 7000L + r);
                    appendRow(json, first, sim.auditEvent(delay, 7000L + r, kind));
                    first = false;
                    sim.host.GO.stop();
                }
            }
        }
        json.append("\n],\n\"rules\": [\n");
        first = true;
        String[] rules = {"lateral-pressionado", "goleiro-com-a-bola", "atacante-livre", "desarme-por-tras", "passe-para-tras"};
        for (String rule : rules) {
            for (int r = 0; r < Math.max(10, eventRuns * 5); r++) {
                TacticalSimulation sim = new TacticalSimulation(1200, 11000L + r);
                appendRow(json, first, sim.ruleScenario(rule, 11000L + r));
                first = false;
                sim.host.GO.stop();
            }
        }
        json.append("\n],\n\"substitutions\": [\n");
        first = true;
        for (String raw : delays) {
            int delay = Integer.parseInt(raw.trim());
            for (int r = 0; r < eventRuns; r++) {
                TacticalSimulation sim = new TacticalSimulation(delay, 9000L + r);
                appendRow(json, first, sim.auditSubstitution(delay, 9000L + r));
                first = false;
                sim.host.GO.stop();
            }
        }
        json.append("\n]\n}\n");
        PrintWriter writer = new PrintWriter(new FileWriter(new File(output)));
        writer.print(json);
        writer.close();
    }

    private static void run(String[] args) throws Exception {
        if ("audit".equals(args[0])) {
            runAudit(args);
            return;
        }
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
