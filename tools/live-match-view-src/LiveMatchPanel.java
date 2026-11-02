package mega;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.Container;
import java.awt.Dialog;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GraphicsEnvironment;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.SecondaryLoop;
import java.awt.RenderingHints;
import java.awt.Toolkit;
import java.awt.Window;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import javax.swing.JLabel;
import javax.swing.ImageIcon;
import javax.swing.JLayeredPane;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import javax.swing.table.TableModel;

public final class LiveMatchPanel extends JPanel {
    private static final long serialVersionUID = 1L;
    private static final Color GRASS = new Color(21, 91, 48);
    private static final Color GRASS_ALT = new Color(24, 103, 54);
    private static final Color LINE = new Color(235, 247, 236, 205);
    private static final Color SHADOW = new Color(0, 0, 0, 90);
    private static final Color NAME_BACK = new Color(0, 0, 0, 170);
    private static final Color CARD_YELLOW = new Color(255, 218, 35);
    private static final Color CARD_RED = new Color(225, 45, 45);
    private static final Color CARD_EDGE = new Color(15, 15, 15);
    private static final Color EVENT_BACK = new Color(4, 25, 20, 225);
    private static final Color EVENT_TITLE = new Color(187, 238, 211);
    private static final BasicStroke STROKE_2 = new BasicStroke(2f);
    private static final Font NAME_FONT = new Font("Tahoma", Font.BOLD, 10);
    private static final Font EVENT_FONT = new Font("Tahoma", Font.BOLD, 13);
    private static final double CONTACT = .024;
    private static final boolean DEBUG_TOOLS = false;
    private static final String[] DEBUG_LABELS = {
        "Falta 4 na barreira", "Falta 3 na barreira", "Falta 2 na barreira", "Falta 1 na barreira",
        "Pênalti", "Falta comum", "Cartão amarelo", "Cartão vermelho", "Lesão", "Gol", "Gol contra",
        "Substituição"
    };
    private static final double FIELD_RATIO = 105.0 / 68.0;
    private static LiveMatchPanel active;
    private static final double BALL_FOOT = .011;
    private static boolean firstLayerCheck;
    private static boolean attachedLogged;
    static { diagnostic("class_loaded", null); }
    private final JPanel host;
    private final Timer timer;
    private final Random random = new Random();
    private final Dot[] home = new Dot[11];
    private final Dot[] away = new Dot[11];
    private final Set<String> yellowCarded = new HashSet<String>();
    private final Set<String> redCarded = new HashSet<String>();
    private final Set<String> injured = new HashSet<String>();
    private static final List<Object[]> SKIPPED_STEPS = new ArrayList<Object[]>();
    private Object preSimMatch;
    private int preSimMinute = -99;
    private int preSimHalf = -99;
    private boolean preEventActive;
    private int preEventRemaining;
    private long preEventDeadline;
    private long preEventStarted;
    private int preEventMinute = -99;
    private int preEventHalf = -99;
    private final Set<String> animatedKeys = new HashSet<String>();
    private int[] homeTactics;
    private Object penaltyActionRef;
    private boolean penaltyDebug;
    private long penaltyPauseUntil;
    private long penaltyResolvedAt;
    private int penaltyScoreBefore = -1;
    private volatile Object penaltyLoop;
    private boolean penaltyBuild;
    private int penaltyFouler = -1;
    private long penaltyFoulDeadline;
    private boolean cardFoulEngaged;
    private long cardFoulStarted;
    private double cardFoulSpotX = .5;
    private double cardFoulSpotY = .5;
    private long penaltySettleDeadline;
    private long substitutionHoldSince;
    private int goalVariant;
    private int goalReboundPhase;
    private double footDirX = 1.0;
    private double footDirY;
    private final Rectangle[] debugButtons = new Rectangle[DEBUG_LABELS.length * 2];
    private final double[][] kickLayoutX = new double[2][11];
    private final double[][] kickLayoutY = new double[2][11];
    private int freeKickOutcome;
    private long freeKickPauseUntil;
    private double freeKickUx;
    private double freeKickUy;
    private double wallCenterX;
    private double wallCenterY;
    private boolean curveActive;
    private double curveCX;
    private double curveCY;
    private double ballLift;
    private boolean ownGoalActive;
    private boolean cardFoulFreeKick;
    private int cardFoulKicker = -1;
    private int ownGoalDefender = -1;
    private int ownGoalStage;
    private int[] awayTactics;
    private List<String> previousLog = Collections.emptyList();
    private String homeName = "Mandante";
    private String awayName = "Visitante";
    private String score = "0 x 0";
    private String visibleScore = "0 x 0";
    private String goalEventText;
    private String minute = "";
    private String event = "A partida está em andamento";
    private Object homeTeamRef;
    private Object awayTeamRef;
    private String previousActionKey;
    private String plannedActionKey;
    private final List<Integer> plannedRoute = new ArrayList<Integer>();
    private int plannedSide;
    private int plannedActor = -1;
    private int plannedAssist = -1;
    private int plannedCardVictim = -1;
    private int plannedType = -1;
    private int plannedSubtype = -1;
    private int plannedMinute = -1;
    private double plannedSpotX = .50;
    private double plannedSpotY = .50;
    private int pendingGoalStage;
    private int pendingGoalSide = -1;
    private int pendingGoalActor = -1;
    private boolean restartActive;
    private long restartStarted;
    private long restartEarliest;
    private long restartDeadline;
    private int kickoffSide;
    private int kickoffPlayerA = 9;
    private int kickoffPlayerB = 10;
    private int plannedCirculationPasses;
    private int possessionPasses;
    private int engineMinute;
    private int engineHalf = 1;
    private boolean engineStateInitialized;
    private BufferedImage otherMatchesImage;
    private Color homeColor = new Color(43, 137, 214);
    private Color awayColor = new Color(235, 238, 242);
    private Color homeAccent = Color.WHITE;
    private Color awayAccent = new Color(30, 42, 54);
    private Color homeStripe;
    private Color awayStripe;
    private Color homeKeeper = new Color(57, 255, 20);
    private Color awayKeeper = new Color(255, 140, 0);
    private Object kitHomeRef;
    private Object kitAwayRef;
    private double ballX = .50;
    private double ballY = .50;
    private double ballFromX = .50;
    private double ballFromY = .50;
    private double ballToX = .50;
    private double ballToY = .50;
    private long moveStarted = System.currentTimeMillis();
    private int moveDuration = 1200;
    private boolean ballInFlight;
    private long controlUntil;
    private long simpleStoppageUntil;
    private int penaltyPhase;
    private int penaltySide;
    private int penaltyActor;
    private int penaltyOutcome;
    private double penaltyShotY;
    private long penaltyReadyAfter;
    private long penaltyDeadline;
    private int freeKickPhase;
    private int freeKickSide;
    private int freeKickActor;
    private int freeKickWall;
    private long freeKickReadyAfter;
    private long freeKickDeadline;
    private int ambientShotPhase;
    private int ambientShotSide;
    private int ambientShotOutcome;
    private double ambientShotY;
    private int cardFoulPhase;
    private int cardFoulOffenderSide;
    private int cardFoulOffender;
    private int cardFoulTaker;
    private long cardFoulReadyAfter;
    private long cardFoulDeadline;
    private String cardFoulEvent;
    private String cardFoulKey;
    private boolean cardFoulRed;
    private final int[] officialShots = {-1, -1};
    private final int[] officialTackles = {-1, -1};
    private final int[] officialPassErrors = {-1, -1};
    private final int[] officialFouls = {-1, -1};
    private int homePossessionTarget = 50;
    private int pendingStatShotSide = -1;
    private int pendingStatRecoverySide = -1;
    private int pendingStatFoulOffenderSide = -1;
    private int possessingSide;
    private int possessingPlayer = 9;
    private int receivingSide = -1;
    private int receivingPlayer = -1;
    private boolean looseBall;
    private int looseSide = -1;
    private int looseChaser = -1;
    private long looseSince;
    private boolean tackleActive;
    private int tackleSide = -1;
    private int tackler = -1;
    private long tackleDeadline;
    private int pendingStatTackleSide = -1;
    private boolean kickoffInProgress;
    private long kickoffDeadline;
    private int kickoffBackPass = -1;
    private boolean openingKickoffDone;
    private boolean halfStartPending;
    private long goalStageDeadline;
    private int goalBuildPasses;
    private int goalBuildTarget;
    private boolean goalFinalPassed;
    private Object matchRef;
    private boolean clockHeld;
    private final List<Object> queuedEngineActions = new ArrayList<Object>();
    private Rectangle otherMatchesArea;
    private Component otherMatchesSource;
    private double otherMatchesScale;
    private long lastTickNanos;
    private double frameSeconds = .016;
    private long virtualNow = System.currentTimeMillis();
    private long lastRealMillis;
    private double urgency = 1.0;
    private double motion = 1.0;
    private int gameTick;
    private String gameTickKey = "";
    private long minuteStartedReal;
    private final Map<Object, Integer> actionDue = new IdentityHashMap<Object, Integer>();
    private int activeDue = -1;
    private int restartDue = -1;
    private long fireAtReal;
    private long heldMinuteDue;
    private long holdStartedReal;
    private int frames;
    private boolean everShown;
    private boolean laidOut;
    private long stoppageSince;
    private String stoppageSignature = "";
    private long penaltyStartedAt;
    private boolean endHandled;
    private boolean clearanceAfterTackle;
    private boolean actionsBaselined;
    private static final String[] BALL_MODELS = {
        "Adidas Telstar 1970", "Adidas Tango 1978", "Adidas Azteca 1986", "Adidas Fevernova 2002",
        "Adidas Teamgeist 2006", "Adidas Jabulani 2010", "Adidas Brazuca 2014", "Adidas Telstar 18",
        "Adidas Al Rihla 2022", "Adidas UCL Finale", "Nike Ordem", "Penalty S11"
    };
    private static final Color[] BALL_ACCENTS = {
        new Color(20, 20, 20), new Color(20, 45, 140), new Color(205, 25, 35), new Color(240, 120, 20),
        new Color(25, 140, 60), new Color(120, 40, 160), new Color(200, 160, 20), new Color(0, 150, 200)
    };
    private static final Color[] REFEREE_KITS = {
        new Color(18, 18, 18), new Color(235, 235, 40), new Color(205, 25, 40), new Color(35, 75, 200),
        new Color(140, 210, 40), new Color(230, 80, 160), new Color(120, 125, 135)
    };
    private static final String[] REFEREES = {
        "Arnaldo Cezar Coelho", "José Roberto Wright", "Armando Marques", "Romualdo Arppi Filho",
        "Dulcídio Wanderley Boschilia", "Margarida", "Carlos Eugênio Simon", "Márcio Rezende de Freitas",
        "Oscar Roberto Godói", "Leonardo Gaciba", "Sálvio Spínola Fagundes Filho", "Wilson Luiz Seneme",
        "Heber Roberto Lopes", "Paulo César de Oliveira", "Sandro Meira Ricci", "Wilton Pereira Sampaio",
        "Anderson Daronco", "Raphael Claus", "Leandro Pedro Vuaden", "Marcelo de Lima Henrique",
        "Ramon Abatti Abel", "Bruno Arleu de Araújo", "Savio Pereira Sampaio", "Rafael Rodrigo Klein",
        "Paulo Cesar Zanovelli", "Edina Alves Batista", "Luiz Flávio de Oliveira", "Flávio Rodrigues de Souza"
    };
    private final int ballStyle = new Random().nextInt(BALL_MODELS.length);
    private Color ballAccent;
    private Color refereeKit;
    private final String refereeName = REFEREES[new Random().nextInt(REFEREES.length)];
    private double refX = .45;
    private double refY = .62;
    private double refVX;
    private double refVY;
    private double refAnchorX = .5;
    private double refAnchorY = .5;
    private int pitchCondition = -1;
    private BufferedImage pitchImage;
    private String pitchKey = "";
    private final List<int[]> statCueQueue = new ArrayList<int[]>();
    private final List<int[]> pendingStatCues = new ArrayList<int[]>();
    private int statCueActive;
    private static final Font NAME_FONT_LIGHT = new Font("Tahoma", Font.BOLD, 9);
    private double ballSpin;
    private double lastBallX = .5;
    private double lastBallY = .5;

    private LiveMatchPanel(JPanel host) {
        this.host = host;
        setOpaque(true);
        setBackground(GRASS);
        setDoubleBuffered(true);
        setFocusable(false);
        initializeFormation(home, false);
        initializeFormation(away, true);
        timer = new Timer(frameDelay(), new ActionListener() {
            @Override public void actionPerformed(ActionEvent event) {
                tick();
            }
        });
        timer.setCoalesce(true);
        active = this;
        MouseAdapter forwarder = new MouseAdapter() {
            @Override public void mousePressed(MouseEvent event) {
                if (!handleDebugClick(event)) forwardMouse(event);
            }
            @Override public void mouseReleased(MouseEvent event) { forwardMouse(event); }
            @Override public void mouseClicked(MouseEvent event) { forwardMouse(event); }
        };
        if (DEBUG_TOOLS) addMouseListener(forwarder);
        timer.start();
    }

    private void forwardMouse(MouseEvent event) {
        Rectangle area = otherMatchesArea;
        Component source = otherMatchesSource;
        double scale = otherMatchesScale;
        if (area == null || source == null || scale <= 0 || !area.contains(event.getPoint())) return;
        int sx = (int) ((event.getX() - area.x) / scale);
        int sy = (int) ((event.getY() - area.y) / scale);
        Component target = SwingUtilities.getDeepestComponentAt(source, sx, sy);
        if (target == null) return;
        Point point = SwingUtilities.convertPoint(source, sx, sy, target);
        target.dispatchEvent(new MouseEvent(target, event.getID(), event.getWhen(), event.getModifiersEx(),
                point.x, point.y, event.getClickCount(), event.isPopupTrigger(), event.getButton()));
    }

    public static void engineStep(Object match, int minute, int half) throws Throwable {
        synchronized (SKIPPED_STEPS) {
            for (int i = 0; i < SKIPPED_STEPS.size(); i++) {
                Object[] entry = SKIPPED_STEPS.get(i);
                if (entry[0] == match && ((Integer) entry[1]).intValue() == minute
                        && ((Integer) entry[2]).intValue() == half) {
                    SKIPPED_STEPS.remove(i);
                    return;
                }
            }
        }
        runEngineStep(match, minute, half);
    }

    private static void runEngineStep(Object match, int minute, int half) throws Throwable {
        Method method = match.getClass().getMethod("q", int.class, int.class);
        try {
            method.invoke(match, Integer.valueOf(minute), Integer.valueOf(half));
        } catch (java.lang.reflect.InvocationTargetException error) {
            throw error.getCause() == null ? error : error.getCause();
        }
    }

    private void updatePreSimulation(long now) {
        if (matchEnded() || insideEngineStep() || penaltyPhase != 0 || halfStartPending || !openingKickoffDone) return;
        Object clock = readField(host, "GO");
        if (!(clock instanceof Timer)) return;
        if (!((Timer) clock).isRunning() && !clockHeld) return;
        if (Boolean.FALSE.equals(readField(host, "GZ"))) return;
        Object row = currentLiveRow();
        Object match = matchFromLiveRow(row);
        if (row == null || match == null || match == row) return;
        int minuteNow = integer(readField(host, "GT"), -1);
        int half = integer(readField(host, "dB"), 1);
        if (minuteNow < 0) return;
        int next = minuteNow + 1;
        if ((half == 1 && next > 48) || (half == 2 && next >= 51)) return;
        if (!(preSimMatch == match && preSimMinute == next && preSimHalf == half)) {
            preSimMatch = match;
            preSimMinute = next;
            preSimHalf = half;
            if (!Boolean.TRUE.equals(invoke(row, "ei"))) return;
            int[] limits = intArray(invoke(match, "ib"));
            if (limits == null || limits.length <= half || limits[half] > next) return;
            int[][] before = statArrays(match);
            try {
                runEngineStep(match, next, half);
                synchronized (SKIPPED_STEPS) {
                    SKIPPED_STEPS.add(new Object[] { match, Integer.valueOf(next), Integer.valueOf(half) });
                    while (SKIPPED_STEPS.size() > 8) SKIPPED_STEPS.remove(0);
                }
            } catch (Throwable error) {
                diagnostic("presim_failed", error);
                return;
            }
            capturePreSimStats(match, before);
        }
        if (preEventMinute == next && preEventHalf == half) return;
        Object value = invoke(match, "hE");
        if (!(value instanceof List<?>)) return;
        List<Object> visual = new ArrayList<Object>();
        for (Object candidate : (List<?>) value) {
            if (Boolean.TRUE.equals(invoke(candidate, "isDone"))) continue;
            if (integer(invoke(candidate, "em"), -1) != next || integer(invoke(candidate, "en"), -1) != half) continue;
            int type = integer(invoke(candidate, "b"), -1);
            if (type != 1 && type != 2 && type != 3 && type != 4 && type != 5) continue;
            String key = engineActionKey(candidate);
            if (key == null || animatedKeys.contains(key)) continue;
            visual.add(candidate);
        }
        preEventMinute = next;
        preEventHalf = half;
        List<int[]> cues = new ArrayList<int[]>(pendingStatCues);
        pendingStatCues.clear();
        for (Object action : visual) {
            int type = integer(invoke(action, "b"), -1);
            int subtype = integer(invoke(action, "el"), -1);
            int side = sameTeam(invoke(action, "cu"), awayTeamRef) ? 1 : 0;
            if (type == 1 && subtype != 3) removeCue(cues, 1, side);
            if (type == 1 && subtype == 4) removeCue(cues, 4, 1 - side);
            if (type == 2 || type == 3 || type == 4) removeCue(cues, 4, side);
        }
        if (visual.isEmpty() && cues.isEmpty()) return;
        preEventActive = true;
        preEventRemaining = visual.size() + cues.size();
        statCueQueue.clear();
        statCueQueue.addAll(cues);
        preEventDeadline = Long.MAX_VALUE;
        preEventStarted = now;
        for (Object action : visual) {
            animatedKeys.add(engineActionKey(action));
            actionDue.put(action, Integer.valueOf(gameTick + 1));
            queuedEngineActions.add(action);
        }
    }

    private int[][] statArrays(Object match) {
        String[] names = {"hA", "hB", "hC", "hD"};
        int[][] result = new int[4][];
        for (int i = 0; i < 4; i++) {
            int[] value = intArray(invoke(match, names[i]));
            result[i] = value == null ? null : value.clone();
        }
        return result;
    }

    private void capturePreSimStats(Object match, int[][] before) {
        pendingStatCues.clear();
        int[][] after = statArrays(match);
        int[] kinds = {1, 2, 3, 4};
        for (int i = 0; i < 4; i++) {
            if (before[i] == null || after[i] == null) continue;
            for (int side = 0; side < 2 && side < after[i].length && side < before[i].length; side++) {
                int delta = after[i][side] - before[i][side];
                for (int k = 0; k < delta && k < 2; k++) pendingStatCues.add(new int[] { kinds[i], side });
            }
        }
        if (after[0] != null && after[0].length >= 2) { officialShots[0] = after[0][0]; officialShots[1] = after[0][1]; }
        if (after[1] != null && after[1].length >= 2) { officialTackles[0] = after[1][0]; officialTackles[1] = after[1][1]; }
        if (after[2] != null && after[2].length >= 2) { officialPassErrors[0] = after[2][0]; officialPassErrors[1] = after[2][1]; }
        if (after[3] != null && after[3].length >= 2) { officialFouls[0] = after[3][0]; officialFouls[1] = after[3][1]; }
        Collections.sort(pendingStatCues, new Comparator<int[]>() {
            @Override public int compare(int[] a, int[] b) {
                int pa = a[0] == 1 ? 0 : a[0] == 4 ? 1 : 2, pb = b[0] == 1 ? 0 : b[0] == 4 ? 1 : 2;
                return pa - pb;
            }
        });
        while (pendingStatCues.size() > maxStatCues()) pendingStatCues.remove(pendingStatCues.size() - 1);
    }

    private void removeCue(List<int[]> cues, int kind, int side) {
        for (int i = 0; i < cues.size(); i++) {
            if (cues.get(i)[0] == kind && cues.get(i)[1] == side) {
                cues.remove(i);
                return;
            }
        }
    }

    private void startStatCue(long now, int[] cue) {
        int kind = cue[0], side = cue[1];
        if (preEventDeadline == Long.MAX_VALUE) preEventDeadline = now + 16000L;
        plannedActionKey = null;
        plannedRoute.clear();
        Dot[] team = side == 0 ? home : away;
        Dot[] rivals = side == 0 ? away : home;
        if (kind == 1) {
            statCueActive = 1;
            pendingStatShotSide = side;
            controlUntil = Math.min(controlUntil, now + 200L);
        } else if (kind == 2) {
            if (possessingSide == side) { onClimax(); return; }
            statCueActive = 2;
            startTackle(now, side, nearestActive(team, ballX, ballY, -1, false));
        } else if (kind == 3) {
            if (possessingSide != side || !carrierHasBall()) { onClimax(); return; }
            statCueActive = 3;
            double ahead = ballX + (side == 0 ? .14 : -.14);
            int rival = nearestActive(rivals, ahead, ballY, -1, false);
            beginPassTo(1 - side, rival, now, 520 + random.nextInt(260));
        } else {
            statCueActive = 4;
            int offender = nearestActive(team, ballX, ballY, -1, false);
            startCardFoul(now, side, offender, "Falta de " + team[offender].name, null, false);
        }
    }

    private void completeStatCue(int kind) {
        if (statCueActive != kind) return;
        statCueActive = 0;
        onClimax();
    }

    private void onClimax() {
        if (!preEventActive) return;
        preEventRemaining--;
        if (preEventRemaining <= 0) fireEngineMinute();
    }

    private void fireEngineMinute() {
        preEventActive = false;
        preEventRemaining = 0;
    }

    private long clockNow() {
        return virtualNow;
    }

    private int minuteDelay() {
        Object clock = readField(host, "GO");
        if (clock instanceof Timer && ((Timer) clock).getInitialDelay() > 0) return ((Timer) clock).getInitialDelay();
        try {
            Field field = host.getClass().getDeclaredField("d");
            field.setAccessible(true);
            int delay = field.getInt(null);
            if (delay > 0) return delay;
        } catch (Throwable ignored) {
        }
        return 700;
    }

    private void advanceClock(boolean running) {
        long real = System.currentTimeMillis();
        long elapsed = lastRealMillis == 0 ? 0 : Math.max(0L, Math.min(100L, real - lastRealMillis));
        lastRealMillis = real;
        int delay = minuteDelay();
        observeGameMinute(real);
        urgency = 1.0;
        motion = 1.0;
        if (running) virtualNow += Math.round(elapsed * urgency);
    }

    private void observeGameMinute(long real) {
        String key = readField(host, "dB") + ":" + readField(host, "GT");
        if (key.equals(gameTickKey)) return;
        gameTickKey = key;
        gameTick++;
        minuteStartedReal = real;
    }

    private int lateness() {
        if (activeDue >= 0 && !hasAnimationStoppage() && pendingGoalStage == 0 && !ballInFlight) activeDue = -1;
        if (restartDue >= 0 && !restartActive && !kickoffInProgress) restartDue = -1;
        int due = Integer.MAX_VALUE;
        for (Object action : queuedEngineActions) {
            Integer value = actionDue.get(action);
            due = Math.min(due, value == null ? gameTick : value.intValue());
        }
        if (activeDue >= 0) due = Math.min(due, activeDue);
        if (restartDue >= 0) due = Math.min(due, restartDue);
        if (due == Integer.MAX_VALUE || gameTick < due) return 0;
        return gameTick - due + 1;
    }

    private long goalBudget() {
        return minuteDelay() >= 1200 ? 2500L : 1200L;
    }

    private boolean holdWanted() {
        if (matchEnded() || penaltyLoop != null) return false;
        if (pendingGoalStage != 0 || cardFoulPhase == 1 || freeKickPhase != 0 || restartActive || penaltyPhase != 0) {
            return true;
        }
        for (Object action : queuedEngineActions) {
            int type = integer(invoke(action, "b"), -1);
            if (type >= 1 && type <= 5) return true;
        }
        return false;
    }

    private void holdGameClock() {
        if (clockHeld || fireAtReal != 0 || matchEnded() || isDecisionDialogOpen()) return;
        if (Boolean.FALSE.equals(readField(host, "GZ"))) return;
        Object value = readField(host, "GO");
        if (!(value instanceof Timer) || !((Timer) value).isRunning()) return;
        ((Timer) value).stop();
        clockHeld = true;
        holdStartedReal = System.currentTimeMillis();
        heldMinuteDue = minuteStartedReal + minuteDelay();
    }

    private void releaseGameClock() {
        if (!clockHeld || fireAtReal != 0) return;
        fireAtReal = Math.max(System.currentTimeMillis(), heldMinuteDue);
    }

    private void updateHeldClock() {
        if (fireAtReal != 0 && System.currentTimeMillis() >= fireAtReal) {
            fireAtReal = 0;
            fireHeldMinute();
        }
        boolean wanted = holdWanted() && !pauseRequested();
        if (wanted) holdGameClock();
        else releaseGameClock();
    }

    private void fireHeldMinute() {
        if (!clockHeld) return;
        clockHeld = false;
        final Object clock = readField(host, "GO");
        if (matchEnded() || Boolean.FALSE.equals(readField(host, "GZ"))) return;
        SwingUtilities.invokeLater(new Runnable() {
            @Override public void run() {
                try {
                    host.getClass().getMethod("qa").invoke(host);
                } catch (Throwable error) {
                    diagnostic("fire_minute_failed", error);
                    if (clock instanceof Timer && !matchEnded()) ((Timer) clock).restart();
                }
            }
        });
    }

    private int maxStatCues() {
        int delay = minuteDelay();
        return delay >= 2000 ? 2 : delay >= 1200 ? 1 : 0;
    }

    private double viewX(double x) {
        return engineHalf == 2 ? 1.0 - x : x;
    }

    private boolean insideEngineStep() {
        return penaltyLoop != null || isDecisionDialogOpen();
    }

    private int tactic(int side, int index, int fallback) {
        int[] values = side == 0 ? homeTactics : awayTactics;
        if (values == null || values.length <= index) return fallback;
        return values[index];
    }

    private static int frameDelay() {
        try {
            int refresh = GraphicsEnvironment.getLocalGraphicsEnvironment()
                    .getDefaultScreenDevice().getDisplayMode().getRefreshRate();
            if (refresh <= 0) refresh = 60;
            refresh = Math.max(30, Math.min(144, refresh));
            return Math.max(7, Math.round(1000f / refresh));
        } catch (Throwable ignored) { return 16; }
    }

    public static void install(final JPanel host) {
        diagnostic("install_called host=" + (host == null ? "null" : host.getClass().getName())
                + " edt=" + SwingUtilities.isEventDispatchThread(), null);
        if (host == null) return;
        Runnable action = new Runnable() {
            @Override public void run() {
            try {
                diagnostic("install_action children=" + host.getComponentCount()
                        + " size=" + host.getWidth() + "x" + host.getHeight(), null);
                for (Component child : host.getComponents()) {
                    if (child instanceof LiveMatchPanel) return;
                }
                if (active != null && active.host == host) return;
                new LiveMatchPanel(host);
                diagnostic("panel_created", null);
            } catch (Throwable error) {
                showInstallError(host, error);
            }
            }
        };
        if (SwingUtilities.isEventDispatchThread()) action.run();
        else SwingUtilities.invokeLater(action);
    }

    private static void showInstallError(JPanel host, Throwable error) {
        diagnostic("install_error", error);
        try {
            String detail = error.getClass().getSimpleName();
            if (error.getMessage() != null && error.getMessage().trim().length() > 0) {
                detail += ": " + error.getMessage().trim();
            }
            JOptionPane.showMessageDialog(host,
                    "O campo ao vivo não pôde ser carregado.\n\n" + detail,
                    "Prévia do jogo ao vivo", JOptionPane.ERROR_MESSAGE);
        } catch (Throwable ignored) {
        }
    }

    private void initializeFormation(Dot[] team, boolean mirror) {
        double[][] formation = {
            {.06,.50}, {.18,.16}, {.18,.38}, {.18,.62}, {.18,.84},
            {.32,.16}, {.34,.39}, {.34,.61}, {.32,.84}, {.46,.36}, {.46,.64}
        };
        for (int i = 0; i < team.length; i++) {
            double x = mirror ? 1.0 - formation[i][0] : formation[i][0];
            team[i] = new Dot(x, formation[i][1], "Jogador " + (i + 1), mirror);
        }
    }

    private void tick() {
        try {
            tickUnsafe();
            watchdog();
        } catch (Throwable error) {
            diagnostic("tick_failed", error);
            failSafeReset("tick_failed");
        }
    }

    private void watchdog() {
        long now = System.currentTimeMillis();
        if (matchEnded()) {
            if (!endHandled) {
                endHandled = true;
                failSafeReset("match_end");
            }
            return;
        }
        boolean dialog = isDecisionDialogOpen();
        if (clockHeld && fireAtReal == 0 && !dialog && now - holdStartedReal > holdLimit()) failSafeReset("hold_timeout");
        String signature = pendingGoalStage + ":" + restartActive + ":" + kickoffInProgress + ":" + penaltyPhase
                + ":" + freeKickPhase + ":" + cardFoulPhase + ":" + (simpleStoppageUntil != 0) + ":" + preEventActive;
        if (!signature.equals(stoppageSignature)) {
            stoppageSignature = signature;
            stoppageSince = now;
        }
        if ((hasAnimationStoppage() || preEventActive) && !dialog && penaltyLoop == null && !halfStartPending
                && now - stoppageSince > 18000L) {
            failSafeReset("stoppage_timeout " + signature);
        }
        if (penaltyPhase != 0) {
            if (penaltyStartedAt == 0) penaltyStartedAt = now;
            else if (now - penaltyStartedAt > 25000L && penaltyLoop == null && !dialog) {
                failSafeReset("penalty_timeout");
            }
        } else {
            penaltyStartedAt = 0;
        }
    }

    private long holdLimit() {
        if (freeKickPhase != 0 || (cardFoulPhase == 1 && cardFoulFreeKick)) return 26000L;
        if (restartActive || kickoffInProgress) return 16000L;
        if (cardFoulPhase == 1) return 14000L;
        return 9000L;
    }

    private void failSafeReset(String reason) {
        diagnostic("failsafe " + reason, null);
        try {
            exitPenaltyLoop();
        } catch (Throwable ignored) {
            penaltyLoop = null;
        }
        restartActive = false;
        kickoffInProgress = false;
        halfStartPending = false;
        pendingGoalStage = 0;
        penaltyPhase = 0;
        penaltyBuild = false;
        penaltyFouler = -1;
        freeKickPhase = 0;
        cardFoulPhase = 0;
        cardFoulFreeKick = false;
        ambientShotPhase = 0;
        simpleStoppageUntil = 0;
        tackleActive = false;
        clearanceAfterTackle = false;
        ownGoalActive = false;
        ownGoalStage = 0;
        goalReboundPhase = 0;
        preEventActive = false;
        preEventRemaining = 0;
        queuedEngineActions.clear();
        actionDue.clear();
        statCueQueue.clear();
        pendingStatCues.clear();
        activeDue = -1;
        restartDue = -1;
        statCueActive = 0;
        curveActive = false;
        ballLift = 0;
        ballInFlight = false;
        receivingSide = -1;
        receivingPlayer = -1;
        stoppageSince = 0;
        penaltyStartedAt = 0;
        if (Double.isNaN(ballX) || Double.isNaN(ballY)) {
            ballX = .5;
            ballY = .5;
        }
        ballX = clamp(ballX, .02, .98);
        ballY = clamp(ballY, .03, .97);
        ballFromX = ballToX = ballX;
        ballFromY = ballToY = ballY;
        Dot[] team = possessingSide == 0 ? home : away;
        looseBall = true;
        looseSide = possessingSide == 1 ? 1 : 0;
        looseChaser = nearestActive(team, ballX, ballY, -1, true);
        looseSince = clockNow();
        controlUntil = 0;
        fireAtReal = 0;
        fireHeldMinute();
    }

    private void tickUnsafe() {
        ensureVisibleLayer();
        long nanos = System.nanoTime();
        if (lastTickNanos != 0) frameSeconds = clamp((nanos - lastTickNanos) / 1e9, .004, .05);
        lastTickNanos = nanos;
        frames++;
        if (frames % 8 == 0) syncFromGame();
        boolean penaltyAnimating = penaltyPhase >= 1 && penaltyPhase <= 4;
        if (isDecisionDialogOpen() && !penaltyAnimating) {
            advanceClock(false);
            repaint();
            return;
        }
        advanceClock(true);
        long now = clockNow();
        updatePreSimulation(now);
        if (preEventActive && (now >= preEventDeadline || now - preEventStarted > 40000L)) fireEngineMinute();
        if (frames % Math.max(1, (int) Math.round(12 / motion)) == 0) updatePlayerTargets();
        else refreshBallRoleTargets();
        updatePlayerPositions();
        updateHeldClock();
        if (lateness() > 0) statCueQueue.clear();
        if (!hasAnimationStoppage() && !queuedEngineActions.isEmpty()) {
            if (preEventActive && preEventDeadline == Long.MAX_VALUE) preEventDeadline = now + 16000L;
            applyEngineAction(queuedEngineActions.remove(0));
        } else if (preEventActive && queuedEngineActions.isEmpty() && statCueActive == 0 && !statCueQueue.isEmpty()
                && !hasAnimationStoppage() && !ballInFlight && !looseBall && !tackleActive) {
            startStatCue(now, statCueQueue.remove(0));
        }
        if (!hasClockStoppage() && queuedEngineActions.isEmpty() && pendingGoalStage == 0) visibleScore = score;
        if (simpleStoppageUntil != 0 && now >= simpleStoppageUntil) {
            simpleStoppageUntil = 0;
            controlUntil = now + 500L;
        }
        if (simpleStoppageUntil != 0) {
            repaint();
            return;
        }
        maybeStartOpeningKickoff(now);
        if (!openingKickoffDone && !restartActive) {
            repaint();
            return;
        }
        updateGoalRestart(now);
        updateKickoff(now);
        updatePendingGoal(now);
        updatePenalty(now);
        updateFreeKick(now);
        updateAmbientShot(now);
        updateCardFoul(now);
        reconcileBall(now);
        double travelled = distance(lastBallX, lastBallY, ballX, ballY);
        if (travelled < .2) ballSpin += travelled * 160.0;
        lastBallX = ballX;
        lastBallY = ballY;
        if (ballInFlight) {
            double t = Math.min(1.0, (now - moveStarted) / (moveDuration * urgency / motion));
            double eased = t * t * (3.0 - 2.0 * t);
            if (curveActive) {
                double inv = 1.0 - eased;
                ballX = inv * inv * ballFromX + 2 * inv * eased * curveCX + eased * eased * ballToX;
                ballY = inv * inv * ballFromY + 2 * inv * eased * curveCY + eased * eased * ballToY;
                ballLift = Math.sin(Math.PI * t);
            } else {
                ballX = ballFromX + (ballToX - ballFromX) * eased;
                ballY = ballFromY + (ballToY - ballFromY) * eased;
                ballLift = 0;
            }
            if (t >= 1.0) handleBallArrival(now);
        } else if (penaltyPhase == 0 && freeKickPhase == 0 && ambientShotPhase == 0
                && cardFoulPhase <= 1 && !restartActive) {
            if (looseBall) {
                updateLooseBall(now);
            } else {
                if (tackleActive) updateTackle(now);
                followBallCarrier();
                if (!tackleActive && !kickoffInProgress && now >= controlUntil
                        && engineRunning() && carrierHasBall()) {
                    if (pendingGoalStage == 1) goalBuildStep(now);
                    else if (pendingGoalStage == 0) advanceBall(now);
                }
            }
        }
        repaint();
    }

    private void handleBallArrival(long now) {
        ballInFlight = false;
        curveActive = false;
        ballLift = 0;
        completeStatCue(3);
        if (receivingSide >= 0 && receivingPlayer >= 0) {
            looseBall = true;
            looseSide = receivingSide;
            looseChaser = receivingPlayer;
            looseSince = now;
            receivingSide = -1;
            receivingPlayer = -1;
        }
        if (penaltyPhase != 0) {
            handlePenaltyArrival(now);
            return;
        }
        if (freeKickPhase != 0) {
            handleFreeKickArrival(now);
            return;
        }
        if (ambientShotPhase != 0) {
            handleAmbientShotArrival(now);
            return;
        }
        if (ownGoalStage == 1 && pendingGoalStage == 1) {
            ownGoalStage = 0;
            ballFromX = ballX;
            ballFromY = ballY;
            ballToX = pendingGoalSide == 0 ? .988 : .012;
            ballToY = .44 + random.nextDouble() * .12;
            pendingGoalStage = 2;
            moveStarted = now;
            moveDuration = 340;
            ballInFlight = true;
            return;
        }
        if (goalReboundPhase == 1 && pendingGoalStage == 1) {
            goalReboundPhase = 0;
            sendBallTo(now, plannedSpotX, plannedSpotY, 450, pendingGoalSide, pendingGoalActor);
            return;
        }
        if (pendingGoalStage == 2) {
            looseBall = false;
            pendingGoalStage = 0;
            ownGoalActive = false;
            ownGoalDefender = -1;
            onClimax();
            releaseGameClock();
            beginGoalRestart(now, pendingGoalSide);
            return;
        }
        if (restartActive) {
            looseBall = false;
            return;
        }
        if (looseBall) updateLooseBall(now);
    }

    private void reconcileBall(long now) {
        if (ballInFlight) {
            if (moveDuration <= 0) moveDuration = 300;
            if (receivingSide >= 0) {
                Dot[] team = receivingSide == 0 ? home : away;
                if (receivingPlayer < 0 || receivingPlayer >= team.length || !team[receivingPlayer].active) {
                    receivingPlayer = nearestActive(team, ballToX, ballToY, -1, true);
                }
            }
            return;
        }
        ballX = clamp(ballX, .005, .995);
        ballY = clamp(ballY, .01, .99);
        if (looseBall) {
            if (looseSide != 0 && looseSide != 1) looseSide = possessingSide;
            if (now - looseSince > 6000L) {
                Dot[] team = looseSide == 0 ? home : away;
                looseChaser = nearestActive(team, ballX, ballY, -1, true);
                looseSince = now;
            }
        }
    }

    private void updateLooseBall(long now) {
        if (!looseBall) return;
        Dot[] team = looseSide == 0 ? home : away;
        if (looseChaser < 0 || looseChaser >= team.length || !team[looseChaser].active) {
            looseChaser = nearestActive(team, ballX, ballY, -1, true);
            looseSince = now;
        }
        Dot chaser = team[looseChaser];
        if (distance(chaser.currentX, chaser.currentY, ballX, ballY) <= CONTACT) {
            looseBall = false;
            possessingSide = looseSide;
            possessingPlayer = looseChaser;
            int control = 220 + random.nextInt(380);
            if (random.nextInt(100) < 22) control += 450 + random.nextInt(600);
            controlUntil = now + control;
            if (kickoffInProgress && looseSide == kickoffSide && looseChaser == kickoffPlayerB) {
                kickoffInProgress = false;
                controlUntil = now + 450L;
            }
            return;
        }
        if (now - looseSince > 2600L) {
            int closer = nearestActive(team, ballX, ballY, -1, true);
            if (closer != looseChaser) {
                looseChaser = closer;
                looseSince = now;
            }
        }
    }

    private boolean carrierHasBall() {
        Dot[] team = possessingSide == 0 ? home : away;
        if (possessingPlayer < 0 || possessingPlayer >= team.length) return false;
        Dot carrier = team[possessingPlayer];
        if (!carrier.active) {
            looseBall = true;
            looseSide = possessingSide;
            looseChaser = nearestActive(team, ballX, ballY, possessingPlayer, true);
            looseSince = clockNow();
            return false;
        }
        return distance(carrier.currentX, carrier.currentY, ballX, ballY) <= CONTACT;
    }

    private void startTackle(long now, int side, int player) {
        Dot[] team = side == 0 ? home : away;
        if (player < 1 || player >= team.length || !team[player].active) {
            player = nearestActive(team, ballX, ballY, -1, false);
        }
        tackleActive = true;
        tackleSide = side;
        tackler = player;
        tackleDeadline = now + 4200L;
    }

    private void updateTackle(long now) {
        if (!tackleActive) return;
        if (tackleSide == possessingSide) {
            tackleActive = false;
            return;
        }
        Dot[] team = tackleSide == 0 ? home : away;
        if (tackler < 0 || tackler >= team.length || !team[tackler].active) {
            tackler = nearestActive(team, ballX, ballY, -1, false);
        }
        Dot dot = team[tackler];
        if (distance(dot.currentX, dot.currentY, ballX, ballY) <= CONTACT) {
            tackleActive = false;
            possessionPasses = 0;
            completeStatCue(2);
            if (clearanceAfterTackle) {
                clearanceAfterTackle = false;
                double direction = tackleSide == 0 ? 1.0 : -1.0;
                double targetX = clamp(ballX + direction * (.28 + random.nextDouble() * .16), .12, .88);
                double targetY = .20 + random.nextDouble() * .60;
                int receiver = nearestActive(team, targetX, targetY, tackler, false);
                double travel = distance(ballX, ballY, targetX, targetY);
                possessingSide = tackleSide;
                possessingPlayer = tackler;
                event = "Afastou: " + dot.name;
                sendBallTo(now, team[receiver].currentX + direction * .02, team[receiver].currentY,
                        (int) (600 + travel * 1400), tackleSide, receiver);
                return;
            }
            possessingSide = tackleSide;
            possessingPlayer = tackler;
            controlUntil = now + 420L + random.nextInt(260);
            return;
        }
        if (now >= tackleDeadline) {
            tackleActive = false;
            completeStatCue(2);
            sendBallTo(now, dot.currentX, dot.currentY, 520, tackleSide, tackler);
        }
    }

    private void sendBallTo(long now, double x, double y, int duration, int side, int player) {
        looseBall = false;
        receivingSide = side;
        receivingPlayer = player;
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = clamp(x, .02, .98);
        ballToY = clamp(y, .03, .97);
        moveStarted = now;
        moveDuration = Math.max(250, duration);
        ballInFlight = true;
    }

    private boolean engineRunning() {
        if (clockHeld) return true;
        Object value = readField(host, "GO");
        return value instanceof Timer && ((Timer) value).isRunning() && !matchEnded();
    }

    private boolean matchEnded() {
        return Boolean.TRUE.equals(readField(host, "GU"));
    }

    private boolean pauseRequested() {
        return integer(readField(host, "GV"), -1) >= 0;
    }

    private void maybeStartOpeningKickoff(long now) {
        if (openingKickoffDone || !engineStateInitialized) return;
        openingKickoffDone = true;
        if (engineMinute > 2 || engineHalf != 1) return;
        event = "Os times entram em campo";
        beginHalfStart(now, 0);
    }

    private void beginHalfStart(long now, int side) {
        clearSetPieces();
        resetBallControl();
        plannedRoute.clear();
        plannedActionKey = null;
        double walked = .6;
        long real = System.currentTimeMillis();
        int entry = 0;
        for (Dot[] team : new Dot[][] { home, away }) {
            boolean awaySide = team == away;
            for (int i = 0; i < team.length; i++) {
                Dot dot = team[i];
                if (!dot.active) continue;
                double sideX = .5 + (awaySide ? .012 : -.012) * (1 + entry % 4);
                double sideY = .975 - (entry % 3) * .008;
                dot.currentX = sideX + (dot.x - sideX) * walked;
                dot.currentY = sideY + (dot.y - sideY) * walked;
                dot.velocityX = 0;
                dot.velocityY = 0;
                dot.entering = walked < 1.0;
                dot.fadeStart = walked < 1.0 ? 0 : real;
                entry++;
            }
        }
        refX = .5;
        refY = .985;
        refVX = 0;
        refVY = 0;
        ballInFlight = false;
        curveActive = false;
        ballLift = 0;
        ballX = ballFromX = ballToX = .5;
        ballY = ballFromY = ballToY = .5;
        restartActive = true;
        kickoffInProgress = false;
        halfStartPending = true;
        restartStarted = now;
        restartEarliest = now + 1500L;
        restartDeadline = now + 25000L;
        restartDue = gameTick + 1;
        kickoffSide = side;
        Dot[] kickoffTeam = side == 0 ? home : away;
        kickoffPlayerA = nearestActive(kickoffTeam, .50, .46, -1, false);
        kickoffPlayerB = nearestActive(kickoffTeam, .50, .54, kickoffPlayerA, false);
        possessingSide = side;
        possessingPlayer = kickoffPlayerA;
        possessionPasses = 0;
    }

    private boolean isDecisionDialogOpen() {
        Window root = SwingUtilities.getWindowAncestor(host);
        for (Window window : Window.getWindows()) {
            if (!(window instanceof Dialog) || !window.isShowing()) continue;
            Dialog dialog = (Dialog) window;
            if (dialog.isModal() && window != root) return true;
        }
        return false;
    }

    private boolean hasClockStoppage() {
        return preEventActive || hasAnimationStoppage();
    }

    private boolean hasAnimationStoppage() {
        return restartActive || kickoffInProgress || pendingGoalStage != 0 || penaltyPhase != 0
                || freeKickPhase != 0 || cardFoulPhase != 0 || simpleStoppageUntil != 0;
    }

    private void followBallCarrier() {
        if (restartActive || looseBall || ballInFlight) return;
        Dot[] side = possessingSide == 0 ? home : away;
        int player = Math.max(0, Math.min(side.length - 1, possessingPlayer));
        Dot carrier = side[player];
        if (!carrier.active) return;
        double speed = Math.sqrt(carrier.velocityX * carrier.velocityX + carrier.velocityY * carrier.velocityY);
        double wantX = speed > .004 ? carrier.velocityX / speed : (possessingSide == 0 ? 1.0 : -1.0);
        double wantY = speed > .004 ? carrier.velocityY / speed : 0;
        footDirX = footDirX * .88 + wantX * .12;
        footDirY = footDirY * .88 + wantY * .12;
        double dirLength = Math.max(.001, Math.sqrt(footDirX * footDirX + footDirY * footDirY));
        double dirX = footDirX / dirLength;
        double dirY = footDirY / dirLength;
        double footX = carrier.currentX + dirX * BALL_FOOT;
        double footY = carrier.currentY + dirY * BALL_FOOT;
        if (distance(carrier.currentX, carrier.currentY, ballX, ballY) > CONTACT * 1.5) {
            looseBall = true;
            looseSide = possessingSide;
            looseChaser = player;
            looseSince = clockNow();
            return;
        }
        ballX += (footX - ballX) * .30;
        ballY += (footY - ballY) * .30;
        ballFromX = ballToX = ballX;
        ballFromY = ballToY = ballY;
    }

    private void ensureVisibleLayer() {
        if (!host.isShowing()) {
            if (everShown) {
                timer.stop();
                if (getParent() != null) getParent().remove(this);
                if (active == this) active = null;
                diagnostic("panel_stopped host_no_longer_showing", null);
            }
            return;
        }
        everShown = true;
        if (laidOut) return;
        if (host.getWidth() <= 0 || host.getHeight() <= 0) return;
        laidOut = true;
        try {
            openFieldSpace();
        } catch (Throwable error) {
            diagnostic("layout_failed", error);
        }
    }

    private void fitScrollPanes(Component component) {
        if (component instanceof JScrollPane) {
            JScrollPane scroll = (JScrollPane) component;
            scroll.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
            scroll.getVerticalScrollBar().setUnitIncrement(16);
            Container parent = scroll.getParent();
            if (parent != null && parent != host && scroll.getY() + scroll.getHeight() > parent.getHeight()) {
                scroll.setBounds(scroll.getX(), scroll.getY(), scroll.getWidth(),
                        Math.max(24, parent.getHeight() - scroll.getY()));
            }
            scroll.revalidate();
            return;
        }
        if (component instanceof Container) {
            for (Component child : ((Container) component).getComponents()) fitScrollPanes(child);
        }
    }

    private void openFieldSpace() {
        int width = host.getWidth();
        int height = host.getHeight();
        Component[] children = host.getComponents();
        Rectangle[] bounds = new Rectangle[children.length];
        StringBuilder before = new StringBuilder("layout_before host=" + width + "x" + height);
        int headerBottom = 0;
        for (int i = 0; i < children.length; i++) {
            bounds[i] = children[i].getBounds();
            before.append(" | ").append(children[i].getClass().getName()).append(' ').append(bounds[i]);
            Rectangle r = bounds[i];
            if (r.y < 150 && r.height < height / 2 && r.width > 0) {
                headerBottom = Math.max(headerBottom, r.y + r.height);
            }
        }
        diagnostic(before.toString(), null);
        if (headerBottom <= 0) headerBottom = 165;
        List<Integer> lower = new ArrayList<Integer>();
        int lowerTop = Integer.MAX_VALUE;
        for (int i = 0; i < children.length; i++) {
            Rectangle r = bounds[i];
            if (r.height >= height - 20 && r.y <= 2) continue;
            if (r.y >= headerBottom - 4) {
                lower.add(Integer.valueOf(i));
                lowerTop = Math.min(lowerTop, r.y);
            }
        }
        int tableHeight = Math.max(150, (int) (height * .25));
        int fieldTop = headerBottom + 6;
        int fieldBottom = height - tableHeight - 6;
        if (fieldBottom - fieldTop < 280) fieldBottom = Math.min(height - 120, fieldTop + 280);
        host.setLayout(null);
        for (int i = 0; i < children.length; i++) children[i].setBounds(bounds[i]);
        if (!lower.isEmpty()) {
            int shift = fieldBottom + 6 - lowerTop;
            for (Integer boxed : lower) {
                int i = boxed.intValue();
                Rectangle r = bounds[i];
                int y = r.y + shift;
                int h = Math.max(24, Math.min(r.height, height - y - 2));
                children[i].setBounds(r.x, y, r.width, h);
            }
        }
        for (Integer boxed : lower) fitScrollPanes(children[boxed.intValue()]);
        host.add(this);
        setBounds(15, fieldTop, width - 30, fieldBottom - fieldTop);
        setVisible(true);
        host.revalidate();
        host.repaint();
        StringBuilder after = new StringBuilder("layout_after field=" + getBounds());
        for (Integer boxed : lower) {
            after.append(" | ").append(children[boxed.intValue()].getClass().getName())
                    .append(' ').append(children[boxed.intValue()].getBounds());
        }
        diagnostic(after.toString(), null);
    }

    private static synchronized void diagnostic(String stage, Throwable error) {
        PrintWriter output = null;
        try {
            String base = System.getenv("LOCALAPPDATA");
            if (base == null || base.trim().length() == 0) base = System.getProperty("user.home");
            File folder = new File(base, "BrassfootPatch2026");
            if (!folder.isDirectory()) folder.mkdirs();
            output = new PrintWriter(new FileWriter(new File(folder, "live-match-debug.log"), true));
            output.println(new Date() + " | " + stage
                    + (error == null ? "" : " | " + error.getClass().getName() + ": " + error.getMessage()));
        } catch (Throwable ignored) {
        } finally {
            if (output != null) output.close();
        }
    }

    private void advanceBall(long now) {
        if (restartActive) return;
        if (cardFoulPhase == 1 && possessingSide != cardFoulOffenderSide) {
            cardFoulBuildStep(now);
            return;
        }
        if (engineMinute <= 0 && !openingKickoffDone) return;
        if (kickoffBackPass >= 0) {
            int back = kickoffBackPass;
            kickoffBackPass = -1;
            if (possessingSide == kickoffSide) {
                beginPassTo(kickoffSide, back, now, 620 + random.nextInt(200));
                return;
            }
        }
        if (plannedActionKey == null && applyPendingStatCue(now)) return;
        if (!plannedRoute.isEmpty()) {
            int next = plannedRoute.remove(0).intValue();
            if (possessingSide != plannedSide) {
                startTackle(now, plannedSide, next);
            } else if (next != possessingPlayer) {
                beginPassTo(plannedSide, next, now, 520 + random.nextInt(360));
            } else {
                controlUntil = now + 380L;
            }
            return;
        }
        if (plannedActionKey != null) {
            startPlannedCirculation(now);
            return;
        }
        startContextPass(now);
    }

    private void updatePendingGoal(long now) {
        if (pendingGoalStage != 1 || ballInFlight || looseBall || pendingGoalActor < 0) return;
        Dot[] scoring = pendingGoalSide == 0 ? home : away;
        Dot actor = scoring[Math.min(scoring.length - 1, pendingGoalActor)];
        boolean actorHasBall = possessingSide == pendingGoalSide && possessingPlayer == pendingGoalActor
                && distance(actor.currentX, actor.currentY, ballX, ballY) <= CONTACT;
        if (!actorHasBall) {
            if (goalStageDeadline > 0 && now >= goalStageDeadline + 9000L && !tackleActive) {
                goalStageDeadline = now;
                double toBall = distance(actor.currentX, actor.currentY, ballX, ballY);
                sendBallTo(now, actor.currentX, actor.currentY,
                        (int) Math.max(450, Math.min(1600, toBall / .5 * 1000.0)),
                        pendingGoalSide, pendingGoalActor);
            }
            return;
        }
        boolean atSpot = distance(actor.currentX, actor.currentY, plannedSpotX, plannedSpotY) <= .035;
        boolean plausible = isPlausibleShot(pendingGoalSide, plannedSubtype, actor.currentX, actor.currentY);
        if (ownGoalActive && ownGoalDefender >= 0 && (atSpot || plausible)) {
            Dot[] defenders = pendingGoalSide == 0 ? away : home;
            Dot defender = defenders[ownGoalDefender];
            ownGoalStage = 1;
            sendBallTo(now, defender.currentX, defender.currentY, 460, -1, -1);
            receivingSide = -1;
            receivingPlayer = -1;
            return;
        }
        if (penaltyBuild && (atSpot || plausible)) {
            Dot[] defenders = pendingGoalSide == 0 ? away : home;
            if (penaltyFouler < 0) {
                penaltyFouler = nearestActive(defenders, ballX, ballY, -1, false);
                penaltyFoulDeadline = now + 3000L;
            }
            Dot fouler = defenders[penaltyFouler];
            if (distance(fouler.currentX, fouler.currentY, ballX, ballY) <= CONTACT * 1.6 || now >= penaltyFoulDeadline) {
                int side = pendingGoalSide;
                int fouled = pendingGoalActor;
                pendingGoalStage = 0;
                penaltyBuild = false;
                penaltyFouler = -1;
                startPenaltySetup(now, side, fouled);
                onClimax();
                releaseGameClock();
            }
            return;
        }
        if (!atSpot && !plausible) {
            if (goalStageDeadline > 0 && now >= goalStageDeadline + 8000L
                    && attackProgress(pendingGoalSide, actor.currentX) >= .60) {
                plannedSpotX = actor.currentX;
                plannedSpotY = actor.currentY;
            }
            return;
        }
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = pendingGoalSide == 0 ? .985 : .015;
        ballToY = .42 + random.nextDouble() * .16;
        pendingGoalStage = 2;
        goalStageDeadline = 0;
        moveStarted = now;
        moveDuration = 720;
        ballInFlight = true;
    }

    private void cardFoulBuildStep(long now) {
        int side = possessingSide;
        Dot[] team = side == 0 ? home : away;
        Dot carrier = team[Math.max(0, Math.min(team.length - 1, possessingPlayer))];
        if (cardFoulFreeKick && !cardFoulEngaged) {
            if (attackProgress(side, carrier.currentX) >= .58) {
                controlUntil = now + 250L;
                return;
            }
            int next = now - cardFoulStarted >= 4500L
                    ? nearestActive(team, cardFoulSpotX, cardFoulSpotY, possessingPlayer, false)
                    : aheadTeammate(team, side, carrier, possessingPlayer, -1);
            double travel = distance(team[next].currentX, team[next].currentY, carrier.currentX, carrier.currentY);
            beginPassTo(side, next, now, (int) (480 + travel * 1400));
            return;
        }
        if (!cardFoulEngaged) {
            steerTowardOffender(now);
            return;
        }
        controlUntil = now + 250L;
    }

    private void steerTowardOffender(long now) {
        Dot[] team = possessingSide == 0 ? home : away;
        Dot[] offenders = cardFoulOffenderSide == 0 ? home : away;
        Dot offender = offenders[Math.max(0, Math.min(offenders.length - 1, cardFoulOffender))];
        Dot carrier = team[Math.max(0, Math.min(team.length - 1, possessingPlayer))];
        double carrierGap = distance(carrier.currentX, carrier.currentY, offender.currentX, offender.currentY);
        int best = -1;
        double bestGap = carrierGap - .05;
        for (int i = 1; i < team.length; i++) {
            if (i == possessingPlayer || !team[i].active) continue;
            if (distance(team[i].currentX, team[i].currentY, carrier.currentX, carrier.currentY) > .36) continue;
            double gap = distance(team[i].currentX, team[i].currentY, offender.currentX, offender.currentY)
                    + random.nextDouble() * .04;
            if (gap < bestGap) { bestGap = gap; best = i; }
        }
        if (best >= 0) beginPassTo(possessingSide, best, now, 560 + random.nextInt(320));
        else controlUntil = now + 300L;
    }

    private double attackProgress(int side, double x) {
        return side == 0 ? x : 1.0 - x;
    }

    private void goalBuildStep(long now) {
        int side = pendingGoalSide;
        int scorer = pendingGoalActor;
        Dot[] team = side == 0 ? home : away;
        if (possessingSide != side) {
            startTackle(now, side, nearestActive(team, ballX, ballY, scorer, false));
            return;
        }
        Dot carrier = team[Math.max(0, Math.min(team.length - 1, possessingPlayer))];
        double progress = attackProgress(side, carrier.currentX);
        if (possessingPlayer == scorer) {
            if (progress >= .62) {
                controlUntil = now + 250L;
                return;
            }
            int partner = aheadTeammate(team, side, carrier, possessingPlayer, scorer);
            goalBuildPasses++;
            beginPassTo(side, partner, now, 560 + random.nextInt(260));
            return;
        }
        Dot scorerDot = team[scorer];
        double runGap = distance(scorerDot.currentX, scorerDot.currentY, plannedSpotX, plannedSpotY);
        boolean timeUp = now >= goalStageDeadline;
        boolean assistReady = plannedAssist >= 0 && possessingPlayer == plannedAssist;
        boolean finalPass = (timeUp || goalBuildPasses >= goalBuildTarget && (progress >= .45 || assistReady)
                || progress >= .66) && (runGap <= .32 || now >= goalStageDeadline + 3000L);
        if (finalPass && !penaltyBuild && goalVariant == 1 && !carrier.wideRole && progress < .70) {
            int wide = -1;
            double bestWide = Double.MAX_VALUE;
            for (int i = 1; i < team.length; i++) {
                if (i == scorer || i == possessingPlayer || !team[i].active || !team[i].wideRole) continue;
                if (attackProgress(side, team[i].currentX) < .58) continue;
                double d = distance(team[i].currentX, team[i].currentY, carrier.currentX, carrier.currentY);
                if (d < bestWide && d < .40) { bestWide = d; wide = i; }
            }
            if (wide >= 0) {
                goalVariant = 3;
                goalBuildPasses++;
                beginPassTo(side, wide, now, 620 + random.nextInt(260));
                return;
            }
        }
        if (finalPass && !penaltyBuild && goalVariant == 2 && progress >= .60 && runGap <= .16) {
            Dot keeper = side == 0 ? away[0] : home[0];
            goalReboundPhase = 1;
            goalFinalPassed = true;
            sendBallTo(now, keeper.currentX, keeper.currentY, 380, -1, -1);
            receivingSide = -1;
            receivingPlayer = -1;
            return;
        }
        if (!finalPass && plannedAssist >= 0 && plannedAssist != scorer && !assistReady
                && team[plannedAssist].active && goalBuildPasses + 1 >= goalBuildTarget) {
            goalBuildPasses++;
            beginPassTo(side, plannedAssist, now, 560 + random.nextInt(300));
            return;
        }
        if (!finalPass) {
            goalBuildPasses++;
            beginPassTo(side, aheadTeammate(team, side, carrier, possessingPlayer, scorer), now,
                    560 + random.nextInt(320));
            return;
        }
        Dot actor = team[scorer];
        double ballTravel = distance(ballX, ballY, plannedSpotX, plannedSpotY);
        double runTravel = distance(actor.currentX, actor.currentY, plannedSpotX, plannedSpotY);
        int duration = (int) Math.max(650, Math.min(2600,
                Math.max(ballTravel / .55 * 1000.0, runTravel / .135 * 1000.0 * .9)));
        if (goalVariant == 3) duration = Math.max(duration, 900);
        goalFinalPassed = true;
        sendBallTo(now, plannedSpotX, plannedSpotY, duration, side, scorer);
    }

    private int aheadTeammate(Dot[] team, int side, Dot carrier, int carrierIndex, int excluded) {
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        double direction = side == 0 ? 1.0 : -1.0;
        for (int i = 1; i < team.length; i++) {
            if (i == carrierIndex || i == excluded || !team[i].active) continue;
            double dx = (team[i].currentX - carrier.currentX) * direction;
            double dy = team[i].currentY - carrier.currentY;
            double d = Math.sqrt(dx * dx + dy * dy);
            if (d > .36 || dx < -.03) continue;
            double focusBias = tactic(side, 3, 0) == 1 ? (team[i].wideRole ? -.07 : 0)
                    : (team[i].wideRole ? .05 : 0);
            double score = d * .6 - dx * .9 + focusBias + random.nextDouble() * .08;
            if (score < bestScore) { bestScore = score; best = i; }
        }
        return best >= 0 ? best : nearestProgressivePlayer(team, carrier, carrierIndex);
    }

    private boolean applyPendingStatCue(long now) {
        if (cardFoulPhase != 0) return false;
        if (pendingStatFoulOffenderSide >= 0) {
            int offenderSide = pendingStatFoulOffenderSide;
            pendingStatFoulOffenderSide = -1;
            Dot[] offenders = offenderSide == 0 ? home : away;
            int offender = nearestActive(offenders, ballX, ballY, -1, false);
            startCardFoul(now, offenderSide, offender, "Falta de " + offenders[offender].fullName, null, false);
            return true;
        }
        if (pendingStatTackleSide >= 0) {
            int side = pendingStatTackleSide;
            pendingStatTackleSide = -1;
            if (side != possessingSide) {
                Dot[] team = side == 0 ? home : away;
                startTackle(now, side, nearestActive(team, ballX, ballY, -1, false));
                return true;
            }
        }
        if (pendingStatRecoverySide >= 0) {
            int recoverySide = pendingStatRecoverySide;
            pendingStatRecoverySide = -1;
            if (recoverySide != possessingSide) {
                Dot[] recovering = recoverySide == 0 ? home : away;
                double aheadX = ballX + (possessingSide == 0 ? .16 : -.16);
                int player = nearestActive(recovering, aheadX, ballY, -1, false);
                beginPassTo(recoverySide, player, now, 520 + random.nextInt(260));
                return true;
            }
        }
        if (pendingStatShotSide >= 0) {
            int shotSide = pendingStatShotSide;
            Dot[] shooting = shotSide == 0 ? home : away;
            if (possessingSide != shotSide) {
                startTackle(now, shotSide, nearestActive(shooting, ballX, ballY, -1, false));
                return true;
            }
            Dot carrier = shooting[Math.max(0, Math.min(shooting.length - 1, possessingPlayer))];
            boolean inRange = shotSide == 0 ? carrier.currentX >= .68 : carrier.currentX <= .32;
            if (inRange) {
                pendingStatShotSide = -1;
                startAmbientShot(now);
            } else {
                int receiver = nearestActive(shooting, shotSide == 0 ? .78 : .22,
                        .36 + random.nextDouble() * .28, possessingPlayer, false);
                beginPassTo(shotSide, receiver, now, 620 + random.nextInt(260));
            }
            return true;
        }
        return false;
    }

    private double spotX(int side) {
        return side == 0 ? .885 : .115;
    }

    private void startPenaltySetup(long now, int side, int fouled) {
        resetBallControl();
        plannedRoute.clear();
        plannedActionKey = null;
        pendingGoalStage = 0;
        penaltyBuild = false;
        cardFoulPhase = 0;
        freeKickPhase = 0;
        ambientShotPhase = 0;
        penaltyPhase = 1;
        penaltySide = side;
        penaltyActor = -1;
        penaltyActionRef = null;
        penaltyScoreBefore = -1;
        penaltyReadyAfter = now + 1600L;
        penaltyDeadline = now + 25000L;
        penaltySettleDeadline = 0;
        event = "Pênalti!";
        Dot[] players = side == 0 ? home : away;
        possessingSide = side;
        possessingPlayer = fouled >= 0 ? fouled : nearestActive(players, ballX, ballY, -1, false);
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = spotX(side);
        ballToY = .50;
        moveStarted = now;
        moveDuration = 700;
        ballInFlight = true;
    }

    public static void beforePenaltyKick(Object row, Object action) {
        LiveMatchPanel panel = active;
        if (panel == null) return;
        try {
            panel.runPenaltyKick(row, action);
        } catch (Throwable error) {
            diagnostic("penalty_hook_failed", error);
        }
    }

    private void runPenaltyKick(Object row, Object action) {
        if (!isShowing() || row == null || row != currentLiveRow()) return;
        long now = clockNow();
        int side = sameTeam(invoke(action, "cu"), awayTeamRef) ? 1 : 0;
        if (penaltyPhase == 0 || penaltySide != side) startPenaltySetup(now, side, -1);
        Dot[] players = side == 0 ? home : away;
        int taker = findPlayer(playerName(invoke(action, "eo")), players);
        if (taker < 0) taker = nearestActive(players, spotX(side) - (side == 0 ? .12 : -.12), .50, -1, false);
        penaltyActor = taker;
        penaltySettleDeadline = 0;
        penaltyActionRef = action;
        penaltyDebug = false;
        penaltyScoreBefore = scoreFor(side);
        String key = engineActionKey(action);
        if (key != null) animatedKeys.add(key);
        penaltyPhase = 2;
        SecondaryLoop loop = Toolkit.getDefaultToolkit().getSystemEventQueue().createSecondaryLoop();
        penaltyLoop = loop;
        Timer guard = new Timer(10000, new ActionListener() {
            @Override public void actionPerformed(ActionEvent event) { exitPenaltyLoop(); }
        });
        guard.setRepeats(false);
        guard.start();
        loop.enter();
        guard.stop();
        penaltyLoop = null;
    }

    private void exitPenaltyLoop() {
        Object loop = penaltyLoop;
        penaltyLoop = null;
        if (loop instanceof SecondaryLoop) ((SecondaryLoop) loop).exit();
    }

    private int scoreFor(int side) {
        String text = labelText(host, "Hn", labelText(host, "Lm", score));
        if (text == null) return -1;
        String[] parts = text.split("[xX]");
        if (parts.length < 2) return -1;
        try {
            return Integer.parseInt(parts[side].replaceAll("[^0-9]", ""));
        } catch (Throwable ignored) {
            return -1;
        }
    }

    private void updatePenalty(long now) {
        if (penaltyPhase == 0) return;
        Dot[] shooting = penaltySide == 0 ? home : away;
        double direction = penaltySide == 0 ? 1.0 : -1.0;
        if (penaltyPhase == 1) {
            if (penaltyDebug && now >= penaltyReadyAfter && !ballInFlight) {
                penaltyActor = nearestActive(shooting, spotX(penaltySide) - direction * .12, .50, -1, false);
                penaltyPhase = 2;
            } else if (now >= penaltyDeadline) {
                penaltyPhase = 0;
                recoverToKeeper(now, 1 - penaltySide);
            }
            return;
        }
        if (ballInFlight || penaltyActor < 0) return;
        Dot taker = shooting[Math.min(shooting.length - 1, penaltyActor)];
        if (penaltyPhase == 2) {
            if (penaltySettleDeadline == 0) penaltySettleDeadline = now + 4000L;
            if (!formationReady() && now < penaltySettleDeadline) return;
            if (distance(taker.currentX, taker.currentY, spotX(penaltySide) - direction * .05, .50) <= .014) {
                penaltyPhase = 3;
                penaltyPauseUntil = now + 1000L;
            }
        } else if (penaltyPhase == 3) {
            if (now >= penaltyPauseUntil) penaltyPhase = 4;
        } else if (penaltyPhase == 4) {
            if (distance(taker.currentX, taker.currentY, ballX, ballY) > .022) return;
            possessingSide = penaltySide;
            possessingPlayer = penaltyActor;
            ballFromX = ballX;
            ballFromY = ballY;
            ballToX = penaltySide == 0 ? .972 : .028;
            ballToY = .45 + random.nextDouble() * .10;
            penaltyShotY = ballToY;
            moveStarted = now;
            moveDuration = 420;
            ballInFlight = true;
            event = "Cobrança: " + taker.name;
        } else if (penaltyPhase == 5) {
            if (penaltyLoop != null || isDecisionDialogOpen()) return;
            boolean goal = penaltyDebug ? random.nextInt(100) < 75
                    : penaltyScoreBefore >= 0 && scoreFor(penaltySide) > penaltyScoreBefore;
            penaltyResolvedAt = now;
            if (goal) {
                penaltyPhase = 6;
                ballFromX = ballX;
                ballFromY = ballY;
                ballToX = penaltySide == 0 ? .992 : .008;
                ballToY = penaltyShotY;
                moveDuration = 260;
                event = "Gol de pênalti!";
            } else {
                penaltyPhase = 7;
                boolean saved = random.nextBoolean();
                ballFromX = ballX;
                ballFromY = ballY;
                ballToX = saved ? (penaltySide == 0 ? .93 : .07) : (penaltySide == 0 ? 1.0 : 0.0);
                ballToY = saved ? .50 + (random.nextDouble() - .5) * .25 : (random.nextBoolean() ? .30 : .70);
                moveDuration = saved ? 520 : 420;
                Dot keeper = penaltySide == 0 ? away[0] : home[0];
                event = saved ? "Defesa do goleiro: " + keeper.name : "Pênalti desperdiçado";
            }
            moveStarted = now;
            ballInFlight = true;
        }
    }

    private void handlePenaltyArrival(long now) {
        if (penaltyPhase == 1) {
            ballFromX = ballToX = ballX = spotX(penaltySide);
            ballFromY = ballToY = ballY = .50;
            controlUntil = Long.MAX_VALUE;
        } else if (penaltyPhase == 4) {
            penaltyPhase = 5;
            exitPenaltyLoop();
        } else if (penaltyPhase == 6) {
            penaltyPhase = 0;
            beginGoalRestart(now, penaltySide);
        } else if (penaltyPhase == 7) {
            penaltyPhase = 0;
            recoverToKeeper(now, 1 - penaltySide);
        }
    }

    private int wallFor(int side, double x, double y) {
        double goalX = side == 0 ? 1.0 : 0.0;
        double dx = (goalX - x) * FIELD_RATIO;
        double dy = .5 - y;
        double distanceToGoal = Math.sqrt(dx * dx + dy * dy);
        int wall = distanceToGoal < .30 ? 4 : distanceToGoal < .42 ? 3 : distanceToGoal < .55 ? 2 : 1;
        if (Math.abs(y - .5) > .26) wall = Math.max(1, wall - 1);
        return wall;
    }

    private void startFreeKick(long now, int side, int actor, double spotX, double spotY, int wall, int outcome) {
        resetBallControl();
        plannedRoute.clear();
        plannedActionKey = null;
        pendingGoalStage = 0;
        cardFoulPhase = 0;
        freeKickPhase = 1;
        freeKickSide = side;
        Dot[] shooting = side == 0 ? home : away;
        if (actor < 1 || actor >= shooting.length || !shooting[actor].active) {
            actor = nearestActive(shooting, spotX, spotY, -1, false);
        }
        freeKickActor = actor;
        freeKickWall = Math.max(1, Math.min(5, wall));
        freeKickOutcome = outcome;
        freeKickPauseUntil = 0;
        plannedSpotX = clamp(spotX, .05, .95);
        plannedSpotY = clamp(spotY, .08, .92);
        freeKickReadyAfter = now + 2000L;
        freeKickDeadline = now + 9000L;
        possessingSide = side;
        possessingPlayer = actor;
        computeFreeKickLayout();
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = plannedSpotX;
        ballToY = plannedSpotY;
        moveStarted = now;
        moveDuration = 700;
        ballInFlight = true;
    }

    private void computeFreeKickLayout() {
        int side = freeKickSide;
        double direction = side == 0 ? 1.0 : -1.0;
        double goalX = side == 0 ? 1.0 : 0.0;
        double bx = plannedSpotX, by = plannedSpotY;
        double dx = (goalX - bx) * FIELD_RATIO;
        double dy = .5 - by;
        double length = Math.max(.001, Math.sqrt(dx * dx + dy * dy));
        double ux = dx / length, uy = dy / length;
        freeKickUx = ux / FIELD_RATIO;
        freeKickUy = uy;
        double wallDistance = 9.15 / 68.0;
        wallCenterX = bx + ux * wallDistance / FIELD_RATIO;
        wallCenterY = by + uy * wallDistance;
        double px = -uy, py = ux;
        double nearSign = by < .5 ? -1.0 : 1.0;
        if (py * nearSign < 0) { px = -px; py = -py; }
        double spacing = .052;
        int wall = freeKickWall;
        Dot[] shooting = side == 0 ? home : away;
        Dot[] defending = side == 0 ? away : home;
        List<Integer> attackers = sortedOutfield(shooting, freeKickActor, true);
        List<Integer> defenders = sortedOutfield(defending, -1, true);
        for (int i = 0; i < 11; i++) {
            kickLayoutX[0][i] = kickLayoutX[1][i] = -1;
        }
        int defendingSide = 1 - side;
        for (int k = 0; k < wall && !defenders.isEmpty(); k++) {
            int index = defenders.remove(0).intValue();
            double offset = (k - (wall - 1) / 2.0 + .5) * spacing;
            kickLayoutX[defendingSide][index] = clamp(wallCenterX + px * offset / FIELD_RATIO, .02, .98);
            kickLayoutY[defendingSide][index] = clamp(wallCenterY + py * offset, .05, .95);
        }
        kickLayoutX[defendingSide][0] = side == 0 ? .968 : .032;
        kickLayoutY[defendingSide][0] = .5 - nearSign * .04;
        double[][] boxSlots = new double[5][2];
        for (int k = 0; k < 5; k++) {
            boxSlots[k][0] = goalX - direction * (.065 + (k % 2) * .032);
            boxSlots[k][1] = .34 + k * .08;
        }
        int slot = 0;
        List<double[]> markTargets = new ArrayList<double[]>();
        for (Integer boxed : new ArrayList<Integer>(attackers)) {
            int index = boxed.intValue();
            if (slot < 4) {
                kickLayoutX[side][index] = boxSlots[slot][0];
                kickLayoutY[side][index] = boxSlots[slot][1];
                markTargets.add(new double[] { boxSlots[slot][0], boxSlots[slot][1] });
            } else if (slot == 4) {
                kickLayoutX[side][index] = clamp(bx - px * .07 / FIELD_RATIO - direction * .01, .03, .97);
                kickLayoutY[side][index] = clamp(by - py * .07, .05, .95);
            } else if (slot < 7) {
                double edgeY = slot == 5 ? .30 : .70;
                kickLayoutX[side][index] = goalX - direction * .175;
                kickLayoutY[side][index] = edgeY;
                markTargets.add(new double[] { goalX - direction * .175, edgeY });
            } else {
                kickLayoutX[side][index] = .5 - direction * (.06 + (slot % 2) * .05);
                kickLayoutY[side][index] = slot % 3 == 0 ? .32 : slot % 3 == 1 ? .55 : .74;
            }
            slot++;
        }
        List<Integer> markers = new ArrayList<Integer>(defenders);
        Collections.reverse(markers);
        int mark = 0;
        for (Integer boxed : markers) {
            int index = boxed.intValue();
            if (mark < markTargets.size()) {
                double[] target = markTargets.get(mark);
                kickLayoutX[defendingSide][index] = clamp(target[0] + direction * .02, .02, .98);
                kickLayoutY[defendingSide][index] = clamp(target[1] + (mark % 2 == 0 ? .02 : -.02), .05, .95);
            } else {
                kickLayoutX[defendingSide][index] = .5 - direction * (.04 + (mark % 2) * .03);
                kickLayoutY[defendingSide][index] = mark % 2 == 0 ? .40 : .62;
            }
            mark++;
        }
        kickLayoutX[side][0] = side == 0 ? .06 : .94;
        kickLayoutY[side][0] = .50;
    }

    private List<Integer> sortedOutfield(final Dot[] team, int excluded, final boolean attackingFirst) {
        List<Integer> result = new ArrayList<Integer>();
        for (int i = 1; i < team.length; i++) {
            if (i != excluded && team[i].active) result.add(Integer.valueOf(i));
        }
        Collections.sort(result, new Comparator<Integer>() {
            @Override public int compare(Integer left, Integer right) {
                int a = team[left.intValue()].roleLine, b = team[right.intValue()].roleLine;
                if (a != b) return attackingFirst ? b - a : a - b;
                return left.intValue() - right.intValue();
            }
        });
        return result;
    }

    private void updateFreeKick(long now) {
        if (freeKickPhase == 0) return;
        if (freeKickPhase == 1) {
            if (!ballInFlight && now >= freeKickReadyAfter && (formationReady() || now >= freeKickDeadline)) {
                freeKickPhase = 2;
                controlUntil = Long.MAX_VALUE;
            }
            return;
        }
        if (ballInFlight) return;
        Dot[] shooting = freeKickSide == 0 ? home : away;
        Dot taker = shooting[Math.min(shooting.length - 1, freeKickActor)];
        if (freeKickPhase == 2) {
            double backX = plannedSpotX - freeKickUx * .055;
            double backY = plannedSpotY - freeKickUy * .055;
            if (freeKickPauseUntil == 0 && distance(taker.currentX, taker.currentY, backX, backY) <= .016) {
                freeKickPauseUntil = now + 1000L;
            }
            if (freeKickPauseUntil != 0 && now >= freeKickPauseUntil) freeKickPhase = 3;
            if (freeKickPauseUntil == 0 && now >= freeKickDeadline + 6000L) freeKickPhase = 3;
            return;
        }
        if (freeKickPhase != 3 || distance(taker.currentX, taker.currentY, ballX, ballY) > .022) return;
        int side = freeKickSide;
        double goalX = side == 0 ? .992 : .008;
        double nearSign = plannedSpotY < .5 ? -1.0 : 1.0;
        Dot keeper = side == 0 ? away[0] : home[0];
        freeKickPhase = 4;
        possessingSide = side;
        possessingPlayer = freeKickActor;
        ballFromX = ballX;
        ballFromY = ballY;
        if (freeKickOutcome == 2) {
            ballToX = wallCenterX;
            ballToY = wallCenterY;
            curveActive = false;
            moveDuration = 360;
            event = "Na barreira!";
        } else {
            boolean farPost = random.nextInt(100) < 65;
            double targetY = .5 + (farPost ? -nearSign : nearSign) * (.055 + random.nextDouble() * .025);
            ballToX = freeKickOutcome == 1 ? (side == 0 ? .955 : .045) : goalX;
            ballToY = freeKickOutcome == 1 ? keeper.currentY + (targetY - keeper.currentY) * .6 : targetY;
            double midX = (ballFromX + ballToX) / 2, midY = (ballFromY + ballToY) / 2;
            double bendSign = farPost ? nearSign : -nearSign;
            curveCX = midX;
            curveCY = clamp(midY + bendSign * (.07 + random.nextDouble() * .03), .03, .97);
            curveActive = true;
            moveDuration = 900 + random.nextInt(150);
            event = "Cobrança de falta: " + taker.name;
        }
        moveStarted = now;
        ballInFlight = true;
    }

    private void handleFreeKickArrival(long now) {
        if (freeKickPhase == 1) {
            ballFromX = ballToX = ballX = plannedSpotX;
            ballFromY = ballToY = ballY = plannedSpotY;
            controlUntil = Long.MAX_VALUE;
        } else if (freeKickPhase == 4) {
            int side = freeKickSide;
            freeKickPhase = 0;
            if (freeKickOutcome == 0) {
                onClimax();
                releaseGameClock();
                beginGoalRestart(now, side);
            } else if (freeKickOutcome == 1) {
                event = "Defesa do goleiro";
                recoverToKeeper(now, 1 - side);
            } else {
                Dot[] defenders = side == 0 ? away : home;
                looseBall = true;
                looseSide = 1 - side;
                looseChaser = nearestActive(defenders, ballX, ballY, -1, false);
                looseSince = now;
            }
        }
    }

    private void resetBallControl() {
        looseBall = false;
        tackleActive = false;
        receivingSide = -1;
        receivingPlayer = -1;
    }

    private void startAmbientShot(long now) {
        ambientShotPhase = 1;
        ambientShotSide = possessingSide;
        ambientShotOutcome = random.nextBoolean() ? 1 : 2;
        ambientShotY = ambientShotOutcome == 1 ? .41 + random.nextDouble() * .18
                : (random.nextBoolean() ? .385 : .615);
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = ambientShotSide == 0 ? (ambientShotOutcome == 1 ? .955 : .982)
                : (ambientShotOutcome == 1 ? .045 : .018);
        ballToY = ambientShotY;
        moveStarted = now;
        moveDuration = 620 + random.nextInt(220);
        ballInFlight = true;
    }

    private void handleAmbientShotArrival(long now) {
        ambientShotPhase = 2;
        controlUntil = now + 420L;
        completeStatCue(1);
    }

    private void updateAmbientShot(long now) {
        if (ambientShotPhase != 2 || now < controlUntil) return;
        ambientShotPhase = 0;
        recoverToKeeper(now, 1 - ambientShotSide);
    }

    private void recoverToKeeper(long now, int keeperSide) {
        double goalKickX = keeperSide == 0 ? .07 : .93;
        boolean outOfPlay = ballX < .02 || ballX > .98;
        double targetX = outOfPlay ? goalKickX : clamp(ballX, .03, .97);
        double targetY = outOfPlay ? .50 : clamp(ballY, .30, .70);
        double travel = distance(ballX, ballY, targetX, targetY);
        if (travel < CONTACT) {
            looseBall = true;
            looseSide = keeperSide;
            looseChaser = 0;
            looseSince = now;
            return;
        }
        sendBallTo(now, targetX, targetY, (int) Math.max(380, Math.min(1500, travel / .35 * 1000.0)),
                keeperSide, 0);
    }

    private void startCardFoul(long now, int offenderSide, int offender, String foulEvent,
                               String cardKey, boolean red) {
        plannedRoute.clear();
        plannedActionKey = null;
        cardFoulPhase = 1;
        cardFoulFreeKick = false;
        cardFoulOffenderSide = offenderSide;
        cardFoulOffender = offender;
        cardFoulEvent = foulEvent;
        cardFoulKey = cardKey;
        cardFoulRed = red;
        cardFoulTaker = -1;
        cardFoulReadyAfter = 0;
        cardFoulStarted = now;
        cardFoulDeadline = now + 11000L;
        cardFoulEngaged = false;
    }

    private void updateCardFoul(long now) {
        if (cardFoulPhase == 0) return;
        int takerSide = 1 - cardFoulOffenderSide;
        Dot[] takerTeam = takerSide == 0 ? home : away;
        Dot[] offenders = cardFoulOffenderSide == 0 ? home : away;
        if (cardFoulPhase == 1) {
            if (cardFoulOffender < 0 || cardFoulOffender >= offenders.length
                    || !offenders[cardFoulOffender].active) {
                cardFoulOffender = nearestActive(offenders, ballX, ballY, -1, false);
            }
            if (possessingSide == cardFoulOffenderSide && !looseBall && !ballInFlight && !tackleActive) {
                startTackle(now, takerSide, nearestActive(takerTeam, ballX, ballY, -1, false));
            }
            boolean takerHasBall = !ballInFlight && !looseBall && possessingSide == takerSide;
            if (cardFoulFreeKick) {
                if (!cardFoulEngaged && takerHasBall && attackProgress(takerSide, ballX) >= .58) {
                    cardFoulOffender = nearestActive(offenders, ballX, ballY, -1, false);
                    cardFoulEngaged = true;
                }
            } else if (!cardFoulEngaged) {
                Dot candidate = offenders[cardFoulOffender];
                double reach = distance(candidate.currentX, candidate.currentY, ballX, ballY);
                if (reach < .22 || now - cardFoulStarted >= 3500L) cardFoulEngaged = true;
            }
            Dot offender = offenders[cardFoulOffender];
            double gap = distance(offender.currentX, offender.currentY, ballX, ballY);
            boolean contact = cardFoulEngaged && takerHasBall && gap <= CONTACT * 1.6;
            if (contact || now >= cardFoulDeadline) blowCardFoul(now);
            return;
        }
        if (cardFoulPhase == 2) {
            if (now < cardFoulReadyAfter) return;
            cardFoulPhase = 3;
            cardFoulDeadline = now + 5000L;
            return;
        }
        Dot taker = takerTeam[cardFoulTaker];
        if (distance(taker.currentX, taker.currentY, ballX, ballY) > CONTACT) {
            if (now < cardFoulDeadline) return;
            cardFoulTaker = nearestActive(takerTeam, ballX, ballY, -1, false);
            cardFoulDeadline = now + 5000L;
            return;
        }
        possessingSide = takerSide;
        possessingPlayer = cardFoulTaker;
        int receiver = nearestProgressivePlayer(takerTeam, taker, cardFoulTaker);
        cardFoulPhase = 0;
        controlUntil = now;
        beginPassTo(takerSide, receiver, now, 720 + random.nextInt(260));
    }

    private void blowCardFoul(long now) {
        int takerSide = 1 - cardFoulOffenderSide;
        completeStatCue(4);
        Dot[] foulers = cardFoulOffenderSide == 0 ? home : away;
        Dot[] victims = takerSide == 0 ? home : away;
        if (possessingSide == takerSide && !looseBall && possessingPlayer >= 0 && possessingPlayer < victims.length
                && cardFoulOffender >= 0 && cardFoulOffender < foulers.length) {
            Dot fouler = foulers[cardFoulOffender];
            Dot victim = victims[possessingPlayer];
            victim.velocityX += fouler.velocityX * .5;
            victim.velocityY += fouler.velocityY * .5;
        }
        if (!cardFoulFreeKick) releaseGameClock();
        if (cardFoulFreeKick) {
            cardFoulFreeKick = false;
            cardFoulPhase = 0;
            tackleActive = false;
            if (ballInFlight) {
                ballInFlight = false;
                ballFromX = ballToX = ballX;
                ballFromY = ballToY = ballY;
            }
            double goalX = takerSide == 0 ? 1.0 : 0.0;
            double direction = takerSide == 0 ? 1.0 : -1.0;
            double spotX = ballX;
            double spotY = ballY;
            double fromGoal = Math.abs(goalX - spotX);
            if (fromGoal < .175 && Math.abs(spotY - .5) < .27) spotX = goalX - direction * .18;
            if (Math.abs(goalX - spotX) > .42) spotX = goalX - direction * .40;
            glideToStop(home);
            glideToStop(away);
            event = "Falta perigosa";
            startFreeKick(now, takerSide, cardFoulKicker, spotX, spotY, wallFor(takerSide, spotX, spotY), 0);
            return;
        }
        Dot[] takerTeam = takerSide == 0 ? home : away;
        tackleActive = false;
        if (ballInFlight) {
            ballInFlight = false;
            ballFromX = ballToX = ballX;
            ballFromY = ballToY = ballY;
        }
        receivingSide = -1;
        receivingPlayer = -1;
        cardFoulTaker = possessingSide == takerSide && !looseBall
                ? possessingPlayer : nearestActive(takerTeam, ballX, ballY, -1, false);
        looseBall = false;
        possessingSide = takerSide;
        possessingPlayer = cardFoulTaker;
        controlUntil = Long.MAX_VALUE;
        if (cardFoulEvent != null) event = cardFoulEvent;
        if (cardFoulKey != null) onClimax();
        if (cardFoulKey != null) {
            if (cardFoulRed) {
                yellowCarded.remove(cardFoulKey);
                redCarded.add(cardFoulKey);
            } else {
                yellowCarded.add(cardFoulKey);
            }
        }
        glideToStop(home);
        glideToStop(away);
        cardFoulPhase = 2;
        cardFoulReadyAfter = now + (cardFoulKey == null ? 700L : 1000L);
    }

    private void glideToStop(Dot[] team) {
        for (Dot dot : team) {
            if (!dot.active) continue;
            dot.targetX = clamp(dot.currentX + dot.velocityX * .45, .03, .97);
            dot.targetY = clamp(dot.currentY + dot.velocityY * .45, .05, .95);
        }
    }

    private void beginGoalRestart(long now, int scoringSide) {
        visibleScore = score;
        if (goalEventText != null) {
            event = goalEventText;
            goalEventText = null;
        }
        beginKickoffReset(now, 1 - scoringSide);
    }

    private void beginKickoffReset(long now, int restartSide) {
        restartActive = true;
        kickoffInProgress = false;
        tackleActive = false;
        looseBall = false;
        receivingSide = -1;
        receivingPlayer = -1;
        restartStarted = now;
        restartEarliest = now + 1800L;
        restartDeadline = now + 12000L;
        restartDue = gameTick + 1;
        kickoffSide = restartSide;
        Dot[] kickoffTeam = kickoffSide == 0 ? home : away;
        kickoffPlayerA = nearestActive(kickoffTeam, .50, .46, -1, false);
        kickoffPlayerB = nearestActive(kickoffTeam, .50, .54, kickoffPlayerA, false);
        possessingSide = kickoffSide;
        possessingPlayer = kickoffPlayerA;
        possessionPasses = 0;
        plannedRoute.clear();
        plannedActionKey = null;
        plannedActor = -1;
        plannedAssist = -1;
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = .50;
        ballToY = .50;
        moveStarted = now;
        moveDuration = 900;
        ballInFlight = true;
    }

    private void updateGoalRestart(long now) {
        if (!restartActive || ballInFlight) return;
        if (now < restartEarliest) return;
        if (halfStartPending && !engineRunning()) return;
        if (halfStartPending && anyEntering() && now < restartDeadline) return;
        if (!formationReady() && now < restartDeadline) return;
        Dot[] kickoffTeam = kickoffSide == 0 ? home : away;
        Dot taker = kickoffTeam[kickoffPlayerA];
        if (distance(taker.currentX, taker.currentY, ballX, ballY) > CONTACT) {
            if (now < restartDeadline + 4000L) return;
            kickoffPlayerA = nearestActive(kickoffTeam, ballX, ballY, kickoffPlayerB, false);
            restartDeadline = now;
            return;
        }
        restartActive = false;
        halfStartPending = false;
        kickoffInProgress = true;
        kickoffDeadline = now + 5000L;
        possessingSide = kickoffSide;
        possessingPlayer = kickoffPlayerA;
        kickoffBackPass = deepestSupport(kickoffTeam, kickoffSide, kickoffPlayerA, kickoffPlayerB);
        beginPassTo(kickoffSide, kickoffPlayerB, now, 650);
    }

    private void updateKickoff(long now) {
        if (kickoffInProgress && now >= kickoffDeadline) {
            kickoffInProgress = false;
            controlUntil = now + 400L;
        }
    }

    private int deepestSupport(Dot[] team, int side, int excluded, int excluded2) {
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        double ownHalfX = side == 0 ? .32 : .68;
        for (int i = 1; i < team.length; i++) {
            if (i == excluded || i == excluded2 || !team[i].active) continue;
            if (team[i].roleLine < 2) continue;
            double score = distance(team[i].x, team[i].y, ownHalfX, .50);
            if (score < bestScore) { bestScore = score; best = i; }
        }
        return best;
    }

    private boolean formationReady() {
        int missing = 0;
        for (Dot[] team : new Dot[][] { home, away }) {
            for (Dot dot : team) {
                if (!dot.active) continue;
                double gap = distance(dot.currentX, dot.currentY, dot.targetX, dot.targetY);
                if (gap > .075) return false;
                if (gap > .04) missing++;
            }
        }
        return missing <= 1;
    }

    private double distance(double x1, double y1, double x2, double y2) {
        double dx = x2 - x1, dy = y2 - y1;
        return Math.sqrt(dx * dx + dy * dy);
    }

    private void startPlannedCirculation(long now) {
        Dot[] side = plannedSide == 0 ? home : away;
        if (plannedType == 2 || plannedType == 3 || plannedType == 4) {
            if (plannedActor == 0 && plannedCardVictim >= 0
                    && plannedMinute - engineMinute <= 1) {
                int attackingSide = 1 - plannedSide;
                if (possessingSide != attackingSide) {
                    Dot[] attackers = attackingSide == 0 ? home : away;
                    startTackle(now, attackingSide, nearestActive(attackers, ballX, ballY, -1, false));
                } else if (possessingPlayer != plannedCardVictim) {
                    beginPassTo(attackingSide, plannedCardVictim, now, 650 + random.nextInt(250));
                } else {
                    controlUntil = now + 700L;
                }
                return;
            }
            startContextPass(now);
            return;
        }
        boolean imminent = plannedMinute - engineMinute <= 1;
        if (!imminent || plannedActor < 0 || (plannedType != 1 && plannedType != 7)) {
            startContextPass(now);
            return;
        }
        if (possessingSide != plannedSide) {
            if (random.nextInt(3) == 0) {
                startTackle(now, plannedSide, nearestActive(side, ballX, ballY, plannedActor, false));
            } else {
                startContextPass(now);
            }
            return;
        }
        Dot carrier = side[Math.max(0, Math.min(side.length - 1, possessingPlayer))];
        if (attackProgress(plannedSide, carrier.currentX) >= .60) {
            int next = recyclePlayer(side, carrier, possessingPlayer);
            if (next == plannedActor) next = nearestProgressivePlayer(side, carrier, possessingPlayer);
            beginPassTo(plannedSide, next, now, 560 + random.nextInt(360));
            return;
        }
        beginPassTo(plannedSide, aheadTeammate(side, plannedSide, carrier, possessingPlayer, plannedActor),
                now, 560 + random.nextInt(360));
    }

    private void beginPassTo(int sideIndex, int next, long now, int duration) {
        Dot[] side = sideIndex == 0 ? home : away;
        next = Math.max(0, Math.min(side.length - 1, next));
        if (!side[next].active) next = nearestActive(side, side[next].currentX, side[next].currentY, -1, false);
        looseBall = false;
        receivingSide = sideIndex;
        receivingPlayer = next;
        Dot target = side[next];
        ballFromX = ballX;
        ballFromY = ballY;
        if (plannedActionKey != null && plannedActor == 0
                && plannedType >= 2 && plannedType <= 4
                && sideIndex != plannedSide && next == plannedCardVictim) {
            ballToX = plannedSpotX;
            ballToY = plannedSpotY;
            int victimTravel = (int) Math.min(2800, distance(target.currentX, target.currentY,
                    plannedSpotX, plannedSpotY) / .13 * 1000.0);
            duration = Math.max(duration, Math.max(750, victimTravel));
        } else {
            ballToX = movingX(target, next, now);
            ballToY = movingY(target, next, now);
        }
        moveStarted = now;
        moveDuration = duration;
        ballInFlight = true;
    }

    private void startContextPass(long now) {
        Dot[] side = possessingSide == 0 ? home : away;
        Dot[] rivals = possessingSide == 0 ? away : home;
        Dot current = side[Math.max(0, Math.min(side.length - 1, possessingPlayer))];
        int rivalSide = 1 - possessingSide;
        int style = tactic(possessingSide, 1, 0);
        double progress = attackProgress(possessingSide, current.currentX);
        boolean license = pendingStatShotSide == possessingSide
                || (pendingGoalStage == 1 && pendingGoalSide == possessingSide)
                || (plannedActionKey != null && plannedSide == possessingSide
                    && (plannedType == 1 || plannedType == 7) && plannedMinute - engineMinute <= 1);
        double cap = license ? .96 : style == 1 ? .71 : style == 2 ? .63 : .67;
        int nearestRival = nearestActive(rivals, current.currentX, current.currentY, -1, false);
        double pressure = distance(rivals[nearestRival].currentX, rivals[nearestRival].currentY,
                current.currentX, current.currentY);
        boolean pressed = pressure < .055;
        possessionPasses++;
        int share = possessingSide == 0 ? homePossessionTarget : 100 - homePossessionTarget;
        int basePasses = style == 1 ? 5 : style == 2 ? 3 : 6;
        int maxPasses = Math.max(2, (int) Math.round((basePasses + random.nextInt(4)) * share / 50.0));
        if (!license && possessionPasses >= maxPasses) {
            possessionPasses = 0;
            startTackle(now, rivalSide, nearestActive(rivals, ballX, ballY, -1, false));
            return;
        }
        if (!license && progress >= .76) {
            possessionPasses = 0;
            clearanceAfterTackle = true;
            startTackle(now, rivalSide, nearestActive(rivals, ballX, ballY, -1, false));
            return;
        }
        int roll = random.nextInt(100);
        if (!pressed && roll < 10 && progress < cap) {
            int far = -1;
            double bestFar = 0;
            for (int i = 1; i < side.length; i++) {
                if (i == possessingPlayer || !side[i].active) continue;
                if (attackProgress(possessingSide, side[i].currentX) > cap) continue;
                double dy = Math.abs(side[i].currentY - current.currentY);
                double d = distance(side[i].currentX, side[i].currentY, current.currentX, current.currentY);
                if (dy > .34 && d < .58 && dy > bestFar) { bestFar = dy; far = i; }
            }
            if (far >= 0) {
                double d = distance(side[far].currentX, side[far].currentY, current.currentX, current.currentY);
                beginPassTo(possessingSide, far, now, (int) (650 + d * 1300));
                return;
            }
        }
        if (!pressed && roll >= 10 && roll < 26 && progress < cap - .04) {
            controlUntil = now + 450L + random.nextInt(650);
            return;
        }
        int next = chooseReceiver(side, current, possessingPlayer, cap, pressed);
        double d = distance(side[next].currentX, side[next].currentY, current.currentX, current.currentY);
        beginPassTo(possessingSide, next, now, (int) (420 + d * 1500 + random.nextInt(160)));
    }

    private int chooseReceiver(Dot[] team, Dot current, int excluded, double cap, boolean pressed) {
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        double direction = possessingSide == 0 ? 1.0 : -1.0;
        double currentProgress = attackProgress(possessingSide, current.currentX);
        for (int i = 1; i < team.length; i++) {
            if (i == excluded || !team[i].active) continue;
            double dx = (team[i].currentX - current.currentX) * direction;
            double dy = team[i].currentY - current.currentY;
            double d = Math.sqrt(dx * dx + dy * dy);
            if (d > .36 || d < .04) continue;
            double targetProgress = attackProgress(possessingSide, team[i].currentX);
            double score = d * .7;
            if (targetProgress > cap) score += (targetProgress - cap) * 4.0;
            else if (currentProgress < cap - .05) score -= Math.max(0, dx) * .8;
            if (dx < -.04) score += pressed ? .02 : .30;
            score += tactic(possessingSide, 3, 0) == 1 ? (team[i].wideRole ? -.06 : 0) : (team[i].wideRole ? .04 : 0);
            score += random.nextDouble() * .08;
            if (score < bestScore) { bestScore = score; best = i; }
        }
        return best >= 0 ? best : nearestProgressivePlayer(team, current, excluded);
    }

    private int recyclePlayer(Dot[] team, Dot current, int excluded) {
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        double direction = possessingSide == 0 ? 1.0 : -1.0;
        for (int i = 1; i < team.length; i++) {
            if (i == excluded || !team[i].active) continue;
            double dx = team[i].currentX - current.currentX;
            double dy = team[i].currentY - current.currentY;
            double d = Math.sqrt(dx * dx + dy * dy);
            if (d > .30 || direction * dx > .04) continue;
            double score = d + random.nextDouble() * .10;
            if (score < bestScore) { bestScore = score; best = i; }
        }
        return best >= 0 ? best : nearestProgressivePlayer(team, current, excluded);
    }

    private void syncFromGame() {
        try {
            Object match = readField(host, "KS");
            Object liveRow = currentLiveRow();
            if (match == null) match = matchFromLiveRow(liveRow);
            if (match != null) {
                matchRef = match;
                int condition = integer(invoke(match, "dX"), -1);
                if (condition >= 0 && condition <= 3) pitchCondition = condition;
                Object homeTeam = invoke(match, "hc");
                Object awayTeam = invoke(match, "hd");
                homeTeamRef = homeTeam;
                awayTeamRef = awayTeam;
                homeTactics = intArray(invoke(homeTeam, "kj"));
                awayTactics = intArray(invoke(awayTeam, "kj"));
                homeName = string(invoke(homeTeam, "getNome"), homeName);
                awayName = string(invoke(awayTeam, "getNome"), awayName);
                updateLineup(home, lineupPlayers(match, "hp", "hl", homeTeam), false);
                updateLineup(away, lineupPlayers(match, "hq", "hm", awayTeam), true);
                if (homeTeam != kitHomeRef || awayTeam != kitAwayRef) {
                    kitHomeRef = homeTeam;
                    kitAwayRef = awayTeam;
                    chooseKits(homeTeam, awayTeam);
                }
                int observedMinute = integer(readField(host, "GT"), 0);
                int observedHalf = integer(readField(host, "dB"), 1);
                if (engineStateInitialized && engineHalf == 1 && observedHalf == 2) {
                    event = "Início do 2º tempo";
                    beginHalfStart(clockNow(), 1);
                }
                engineMinute = observedMinute;
                engineHalf = observedHalf;
                engineStateInitialized = true;
                syncOfficialStats(match);
                Object upcoming = findUpcomingAction(match);
                if (upcoming != null && !hasClockStoppage() && queuedEngineActions.isEmpty()) {
                    int actionMinute = integer(invoke(upcoming, "em"), -1);
                    int currentMinute = integer(readField(host, "GT"), 0);
                    String upcomingKey = engineActionKey(upcoming);
                    if (animatedKeys.contains(upcomingKey)) upcomingKey = null;
                    if (actionMinute >= currentMinute && actionMinute - currentMinute <= 8
                            && upcomingKey != null && !upcomingKey.equals(plannedActionKey)
                            && !upcomingKey.equals(previousActionKey)) {
                        planUpcomingAction(upcoming, match);
                    }
                }
            }
            String previousScore = score;
            score = labelText(host, "Hn", labelText(host, "Lm", score));
            boolean scoreChanged = !score.equals(previousScore);
            minute = labelText(host, "Ll", findMinuteText(host, minute));
            List<String> current = new ArrayList<String>();
            Object action = invoke(liveRow, "tV");
            if (match != null) scanEngineActions(match);
            String liveEvent = newestVisibleEvent(
                    labelText(host, "Hl", null), labelText(host, "Hm", null));
            if (liveEvent == null) liveEvent = string(invoke(liveRow, "ik"), null);
            if (liveEvent == null) liveEvent = string(invoke(match, "ik"), null);
            if (scoreChanged && isUsableEvent(liveEvent)
                    && !liveEvent.toLowerCase(Locale.ROOT).contains("gol")) {
                liveEvent = "Gol! " + liveEvent;
            }
            if (action == null && isUsableEvent(liveEvent)) current.add(liveEvent);
            if (liveRow == null) {
                Object log = readField(host, "xb");
                if (log instanceof Component) collectText((Component) log, current);
                Object table = readField(host, "DG");
                if (table instanceof JTable) collectTable((JTable) table, current);
            }
            current = cleanLog(current);
            if (!current.equals(previousLog)) {
                String newest = newestEntry(previousLog, current);
                previousLog = current;
                if (newest != null) applyEvent(newest);
            }
        } catch (Throwable ignored) {
        }
    }

    private void scanEngineActions(Object match) {
        Object value = invoke(match, "hE");
        if (!(value instanceof List<?>)) return;
        int minuteNow = integer(readField(host, "GT"), 0);
        int half = integer(readField(host, "dB"), 1);
        long now = clockNow();
        List<Object> fresh = new ArrayList<Object>();
        for (Object candidate : new ArrayList<Object>((List<?>) value)) {
            if (!Boolean.TRUE.equals(invoke(candidate, "isDone"))) continue;
            String key = engineActionKey(candidate);
            if (key == null || animatedKeys.contains(key)) continue;
            animatedKeys.add(key);
            if (!actionsBaselined) continue;
            if (integer(invoke(candidate, "en"), -1) != half) continue;
            if (integer(invoke(candidate, "em"), -1) < minuteNow - 1) continue;
            int type = integer(invoke(candidate, "b"), -1);
            int subtype = integer(invoke(candidate, "el"), -1);
            boolean penaltyResult = type == 7 || (type == 1 && subtype == 3);
            if (penaltyResult && (penaltyPhase != 0 || now - penaltyResolvedAt < 15000L)) continue;
            fresh.add(candidate);
        }
        actionsBaselined = true;
        for (Object action : fresh) {
            int type = integer(invoke(action, "b"), -1);
            previousActionKey = engineActionKey(action);
            if (type == 6 || type == 8) applyEngineAction(action);
            else if (hasClockStoppage() || !queuedEngineActions.isEmpty()) {
                actionDue.put(action, Integer.valueOf(gameTick));
                queuedEngineActions.add(action);
            } else {
                actionDue.put(action, Integer.valueOf(gameTick));
                applyEngineAction(action);
            }
        }
    }

    private Object currentLiveRow() {
        Object value = readField(host, "vK");
        if (!(value instanceof List<?>)) return null;
        List<?> matches = (List<?>) value;
        int index = integer(readField(host, "GW"), 0);
        if (index < 0 || index >= matches.size()) return null;
        return matches.get(index);
    }

    private void syncOfficialStats(Object match) {
        int[] possession = intArray(invoke(match, "hz"));
        int[] shots = intArray(invoke(match, "hA"));
        int[] tackles = intArray(invoke(match, "hB"));
        int[] errors = intArray(invoke(match, "hC"));
        int[] fouls = intArray(invoke(match, "hD"));
        if (possession != null && possession.length >= 2) {
            homePossessionTarget = Math.max(5, Math.min(95, possession[0]));
        }
        for (int side = 0; side < 2; side++) {
            if (shots != null && shots.length > side) {
                if (officialShots[side] >= 0 && shots[side] > officialShots[side]) pendingStatShotSide = side;
                officialShots[side] = shots[side];
            }
            if (tackles != null && tackles.length > side) {
                if (officialTackles[side] >= 0 && tackles[side] > officialTackles[side]) pendingStatTackleSide = side;
                officialTackles[side] = tackles[side];
            }
            if (errors != null && errors.length > side) {
                if (officialPassErrors[side] >= 0 && errors[side] > officialPassErrors[side]) {
                    pendingStatRecoverySide = 1 - side;
                }
                officialPassErrors[side] = errors[side];
            }
            if (fouls != null && fouls.length > side) {
                if (officialFouls[side] >= 0 && fouls[side] > officialFouls[side]) {
                    pendingStatFoulOffenderSide = side;
                }
                officialFouls[side] = fouls[side];
            }
        }
    }

    private int[] intArray(Object value) {
        return value instanceof int[] ? (int[]) value : null;
    }

    private Object matchFromLiveRow(Object selected) {
        if (selected == null) return null;
        Object match = invoke(selected, "tR");
        return match == null ? selected : match;
    }

    private boolean isUsableEvent(String value) {
        if (value == null) return false;
        String text = value.trim();
        return text.length() > 3 && !text.startsWith("components.") && !text.contains("@");
    }

    private String engineActionKey(Object action) {
        if (action == null) return null;
        return integer(invoke(action, "b"), -1) + ":"
                + integer(invoke(action, "el"), -1) + ":"
                + integer(invoke(action, "em"), -1) + ":"
                + integer(invoke(action, "en"), -1) + ":"
                + playerName(invoke(action, "eo")) + ":"
                + playerName(invoke(action, "ep"));
    }

    private Object findUpcomingAction(Object match) {
        Object value = invoke(match, "hE");
        if (!(value instanceof List<?>)) return null;
        int currentHalf = integer(readField(host, "dB"), 1);
        int currentMinute = integer(readField(host, "GT"), 0);
        Object best = null;
        int bestMinute = Integer.MAX_VALUE;
        for (Object candidate : (List<?>) value) {
            if (Boolean.TRUE.equals(invoke(candidate, "isDone"))) continue;
            int half = integer(invoke(candidate, "en"), -1);
            int actionMinute = integer(invoke(candidate, "em"), -1);
            int type = integer(invoke(candidate, "b"), -1);
            if (half != currentHalf || actionMinute < currentMinute || type == 8) continue;
            if (actionMinute < bestMinute) {
                best = candidate;
                bestMinute = actionMinute;
            }
        }
        return best;
    }

    private void planUpcomingAction(Object action, Object match) {
        plannedRoute.clear();
        plannedActionKey = engineActionKey(action);
        Object team = invoke(action, "cu");
        plannedSide = sameTeam(team, awayTeamRef) ? 1 : 0;
        Dot[] players = plannedSide == 0 ? home : away;
        int actor = findPlayer(playerName(invoke(action, "eo")), players);
        if (actor < 0) actor = 9;
        plannedActor = actor;
        plannedAssist = findAssistPlayer(match, action, players);
        plannedCardVictim = -1;
        plannedCirculationPasses = 0;
        int type = integer(invoke(action, "b"), -1);
        int subtype = integer(invoke(action, "el"), -1);
        plannedType = type;
        plannedSubtype = subtype;
        plannedMinute = integer(invoke(action, "em"), -1);
        choosePlannedSpot(type, subtype);

        if (type == 2 || type == 3 || type == 4) {
            if (actor == 0) {
                plannedSpotX = plannedSide == 0 ? .12 : .88;
                plannedSpotY = .38 + random.nextDouble() * .24;
                Dot[] attackers = plannedSide == 0 ? away : home;
                plannedCardVictim = nearestPlayer(attackers, plannedSpotX, plannedSpotY, -1, -1);
            }
            return;
        }

    }

    private void choosePlannedSpot(int type, int subtype) {
        double direction = plannedSide == 0 ? 1.0 : -1.0;
        if (type == 1 && subtype == 4) {
            plannedSpotX = plannedSide == 0 ? .73 + random.nextDouble() * .08
                    : .27 - random.nextDouble() * .08;
            plannedSpotY = .28 + random.nextDouble() * .44;
        } else if (type == 1 && subtype == 3 || type == 7) {
            plannedSpotX = plannedSide == 0 ? .885 : .115;
            plannedSpotY = .50;
        } else if (type == 1) {
            boolean inside = random.nextInt(10) < 9;
            plannedSpotX = inside ? (plannedSide == 0 ? .86 + random.nextDouble() * .075
                    : .14 - random.nextDouble() * .075)
                    : (plannedSide == 0 ? .81 + random.nextDouble() * .04
                    : .19 - random.nextDouble() * .04);
            plannedSpotY = inside ? .34 + random.nextDouble() * .32 : .30 + random.nextDouble() * .40;
        } else {
            plannedSpotX = clamp((plannedSide == 0 ? .58 : .42) + direction * random.nextDouble() * .18,
                    .12, .88);
            plannedSpotY = .18 + random.nextDouble() * .64;
        }
    }

    private boolean hasPlannedShotSpot() {
        return pendingGoalStage == 1;
    }

    private double runInX(int side) {
        return clamp(plannedSpotX - (side == 0 ? 1.0 : -1.0) * .075, .10, .90);
    }

    private int findAssistPlayer(Object match, Object target, Dot[] players) {
        Object value = invoke(match, "hE");
        if (!(value instanceof List<?>)) return -1;
        int minuteValue = integer(invoke(target, "em"), -1);
        int half = integer(invoke(target, "en"), -1);
        Object team = invoke(target, "cu");
        for (Object candidate : (List<?>) value) {
            if (integer(invoke(candidate, "b"), -1) == 8
                    && integer(invoke(candidate, "em"), -2) == minuteValue
                    && integer(invoke(candidate, "en"), -2) == half
                    && sameTeam(invoke(candidate, "cu"), team)) {
                return findPlayer(playerName(invoke(candidate, "eo")), players);
            }
        }
        return -1;
    }

    private void addRoute(int player) {
        if (player < 0) return;
        if (!plannedRoute.isEmpty()
                && plannedRoute.get(plannedRoute.size() - 1).intValue() == player) return;
        plannedRoute.add(Integer.valueOf(player));
    }

    private int nearestPlayer(Dot[] team, double x, double y, int excluded, int excluded2) {
        int best = -1;
        double bestDistance = Double.MAX_VALUE;
        for (int i = 1; i < team.length; i++) {
            if (i == excluded || i == excluded2 || !team[i].active) continue;
            double dx = team[i].currentX - x;
            double dy = team[i].currentY - y;
            double distance = dx * dx + dy * dy;
            if (distance < bestDistance) { bestDistance = distance; best = i; }
        }
        if (best >= 0) return best;
        return nearestActive(team, x, y, -1, true);
    }

    private int nearestActive(Dot[] team, double x, double y, int excluded, boolean includeKeeper) {
        int best = -1;
        double bestDistance = Double.MAX_VALUE;
        for (int i = includeKeeper ? 0 : 1; i < team.length; i++) {
            if (i == excluded || !team[i].active) continue;
            double dx = team[i].currentX - x;
            double dy = team[i].currentY - y;
            double distance = dx * dx + dy * dy;
            if (distance < bestDistance) { bestDistance = distance; best = i; }
        }
        if (best >= 0) return best;
        for (int i = 0; i < team.length; i++) if (team[i].active) return i;
        return 0;
    }

    private int nearestProgressivePlayer(Dot[] team, Dot current, int excluded) {
        int best = -1;
        double bestScore = Double.MAX_VALUE;
        double direction = possessingSide == 0 ? 1.0 : -1.0;
        for (int i = 1; i < team.length; i++) {
            if (i == excluded || !team[i].active) continue;
            double dx = team[i].currentX - current.currentX;
            double dy = team[i].currentY - current.currentY;
            double distance = Math.sqrt(dx * dx + dy * dy);
            if (distance > .34) continue;
            double backwards = direction * dx < -.10 ? .35 : 0.0;
            double focusBias = tactic(possessingSide, 3, 0) == 1 ? (team[i].wideRole ? -.07 : 0)
                    : (team[i].wideRole ? .05 : 0);
            double scoreValue = distance + backwards + focusBias + random.nextDouble() * .08;
            if (scoreValue < bestScore) { bestScore = scoreValue; best = i; }
        }
        return best >= 0 ? best : nearestPlayer(team, current.currentX, current.currentY, excluded, -1);
    }

    private void clearSetPieces() {
        penaltyPhase = 0;
        freeKickPhase = 0;
        cardFoulPhase = 0;
        ambientShotPhase = 0;
        pendingGoalStage = 0;
        simpleStoppageUntil = 0;
        kickoffInProgress = false;
        tackleActive = false;
        queuedEngineActions.clear();
        actionDue.clear();
    }

    private void applyEngineAction(Object action) {
        Integer due = actionDue.remove(action);
        activeDue = due == null ? gameTick : due.intValue();
        boolean preparedGoal = plannedActionKey != null && plannedType == 1;
        double preparedX = plannedSpotX;
        double preparedY = plannedSpotY;
        int preparedAssist = preparedGoal ? plannedAssist : -1;
        int type = integer(invoke(action, "b"), -1);
        int subtype = integer(invoke(action, "el"), -1);
        Object team = invoke(action, "cu");
        String actorName = playerName(invoke(action, "eo"));
        String secondName = playerName(invoke(action, "ep"));
        int side = sameTeam(team, awayTeamRef) ? 1 : 0;
        int homeActor = findPlayer(actorName, home);
        int awayActor = findPlayer(actorName, away);
        boolean ownGoal = false;
        int ownGoalIndex = -1;
        if (type == 1 && subtype != 3 && subtype != 4) {
            int same = side == 0 ? homeActor : awayActor;
            int other = side == 0 ? awayActor : homeActor;
            if (same < 0 && other >= 0) {
                ownGoal = true;
                ownGoalIndex = other;
                if (side == 0) homeActor = -1;
                else awayActor = -1;
            }
        } else {
            if (homeActor >= 0 && awayActor < 0) side = 0;
            else if (awayActor >= 0 && homeActor < 0) side = 1;
        }
        Dot[] players = side == 0 ? home : away;
        int actor = side == 0 ? homeActor : awayActor;
        if (actor < 0 && type != 6) actor = findPlayer(secondName, players);
        long now = clockNow();
        String description = cleanEvent(string(invoke(action, "er"), null));
        if (type == 6) {
            event = isUsableEvent(description) ? description
                    : "Substituição: sai " + actorName + " · entra " + secondName;
            return;
        }
        if (type == 8) return;
        boolean cardType = type == 2 || type == 3 || type == 4;
        boolean openPlayGoal = type == 1 && subtype != 3 && subtype != 4;
        if (openPlayGoal) goalEventText = isUsableEvent(description) ? description
                : (ownGoal ? "Gol contra de " : "Gol de ") + actorName;
        else if (isUsableEvent(description) && !cardType) event = description;
        if (type < 1 || type > 7) return;
        receivingSide = -1;
        receivingPlayer = -1;
        tackleActive = false;
        plannedRoute.clear();
        plannedActionKey = null;
        plannedAssist = -1;
        plannedCirculationPasses = 0;
        if (actor < 0) actor = nearestActive(players, ballX, ballY, -1, type == 7 || type == 1);
        if (type == 1 || type == 7) pendingStatShotSide = -1;
        if (type == 2 || type == 3 || type == 4) pendingStatFoulOffenderSide = -1;
        if (type == 1 && subtype == 3) {
            if (penaltyPhase != 0 || now - penaltyResolvedAt < 15000L) return;
            if (preEventActive) {
                plannedSide = side;
                plannedActor = actor;
                plannedType = 1;
                plannedSubtype = 0;
                plannedSpotX = side == 0 ? .87 + random.nextDouble() * .05 : .13 - random.nextDouble() * .05;
                plannedSpotY = .38 + random.nextDouble() * .24;
                pendingGoalStage = 1;
                pendingGoalSide = side;
                pendingGoalActor = actor;
                penaltyBuild = true;
                penaltyFouler = -1;
                penaltyFoulDeadline = 0;
                goalStageDeadline = now + goalBudget();
                goalBuildPasses = 0;
                goalBuildTarget = minuteDelay() <= 700 ? 0 : random.nextInt(2);
                goalVariant = 0;
                if (!ballInFlight && !looseBall) controlUntil = Math.min(controlUntil, now + 300L);
            } else {
                startPenaltySetup(now, side, actor);
            }
        } else if (type == 7) {
            return;
        } else if (type == 1 && subtype == 4) {
            plannedSide = side;
            choosePlannedSpot(1, 4);
            Dot[] defenders = side == 0 ? away : home;
            int offender = nearestActive(defenders, ballX, ballY, -1, false);
            startCardFoul(now, 1 - side, offender, null, null, false);
            cardFoulFreeKick = true;
            cardFoulSpotX = plannedSpotX;
            cardFoulSpotY = plannedSpotY;
            cardFoulKicker = actor;
            goalEventText = isUsableEvent(description) ? description : "Gol de falta: " + actorName;
        } else if (type == 1) {
            plannedSide = side;
            plannedActor = actor;
            plannedType = type;
            plannedSubtype = subtype;
            if (preparedGoal) {
                plannedSpotX = preparedX;
                plannedSpotY = preparedY;
            } else {
                choosePlannedSpot(type, subtype);
            }
            pendingGoalStage = 1;
            pendingGoalSide = side;
            pendingGoalActor = actor;
            plannedAssist = preparedAssist >= 0 ? preparedAssist
                    : matchRef == null ? -1 : findAssistPlayer(matchRef, action, players);
            if (plannedAssist == actor) plannedAssist = -1;
            goalStageDeadline = now + goalBudget();
            goalBuildPasses = 0;
            goalBuildTarget = minuteDelay() <= 700 ? 0 : random.nextInt(2);
            goalFinalPassed = false;
            goalReboundPhase = 0;
            int roll = random.nextInt(100);
            goalVariant = roll < 55 ? 0 : roll < 82 ? 1 : 2;
            if (tactic(side, 3, 0) == 1 && roll < 70) goalVariant = 1;
            ownGoalActive = ownGoal;
            ownGoalDefender = ownGoalIndex;
            ownGoalStage = 0;
            if (ownGoal) {
                pendingGoalActor = nearestActive(players, side == 0 ? .80 : .20, .50, -1, false);
                plannedActor = pendingGoalActor;
                plannedAssist = -1;
                goalVariant = random.nextBoolean() ? 1 : 0;
            }
            if (!ballInFlight && !looseBall) controlUntil = Math.min(controlUntil, now + 300L);
        } else if (type == 2) {
            startCardFoul(now, side, actor, isUsableEvent(description) ? description : "Cartão amarelo: " + actorName,
                    playerKey(side, players[actor].fullName), false);
        } else if (type == 3 || type == 4) {
            startCardFoul(now, side, actor, isUsableEvent(description) ? description : "Expulsão: " + actorName,
                    playerKey(side, players[actor].fullName), true);
        } else if (type == 5) {
            event = "Lesão: " + actorName;
            injured.add(playerKey(side, players[actor].fullName));
            onClimax();
            simpleStoppageUntil = now + 1500L;
            if (possessingSide == side && possessingPlayer == actor && !ballInFlight) {
                looseBall = true;
                looseSide = side;
                looseChaser = nearestActive(players, ballX, ballY, actor, false);
                looseSince = now;
            }
            controlUntil = Long.MAX_VALUE;
        }
    }

    private boolean isPlausibleShot(int side, int subtype, double x, double y) {
        if (y < .20 || y > .80) return false;
        if (subtype == 4) return side == 0 ? x >= .68 && x <= .84 : x <= .32 && x >= .16;
        if (subtype == 3) return side == 0 ? x >= .84 && x <= .91 : x <= .16 && x >= .09;
        return side == 0 ? x >= .84 : x <= .16;
    }

    private boolean sameTeam(Object first, Object second) {
        if (first == second && first != null) return true;
        String firstName = string(invoke(first, "getNome"), null);
        String secondName = string(invoke(second, "getNome"), null);
        return firstName != null && firstName.equals(secondName);
    }

    private String playerName(Object player) {
        return string(invoke(player, "getNome"), "");
    }

    private String newestVisibleEvent(String first, String second) {
        first = cleanEvent(first);
        second = cleanEvent(second);
        if (!isUsableEvent(first)) return isUsableEvent(second) ? second : null;
        if (!isUsableEvent(second)) return first;
        return eventOrder(second) >= eventOrder(first) ? second : first;
    }

    private String cleanEvent(String value) {
        if (value == null) return null;
        return value.replaceAll("<[^>]+>", " ").replaceAll("\\s+", " ").trim();
    }

    private int eventOrder(String value) {
        if (value == null) return -1;
        int marker = Math.max(value.lastIndexOf('\''), value.lastIndexOf('’'));
        int minuteValue = 0;
        if (marker > 0) {
            int start = marker - 1;
            while (start >= 0 && Character.isDigit(value.charAt(start))) start--;
            try { minuteValue = Integer.parseInt(value.substring(start + 1, marker)); }
            catch (Throwable ignored) { minuteValue = 0; }
        }
        String lower = value.toLowerCase(Locale.ROOT);
        if (lower.contains("2º") || lower.contains("2°") || lower.contains("2o")) minuteValue += 100;
        return minuteValue;
    }

    private String findMinuteText(Component component, String fallback) {
        if (component instanceof JLabel) {
            String text = ((JLabel) component).getText();
            if (text != null && text.matches(".*[0-9]+['’].*tempo.*")) return text.trim();
        }
        if (component instanceof Container) {
            for (Component child : ((Container) component).getComponents()) {
                String found = findMinuteText(child, null);
                if (found != null) return found;
            }
        }
        return fallback;
    }

    private int integer(Object value, int fallback) {
        return value instanceof Number ? ((Number) value).intValue() : fallback;
    }

    private List<?> lineupPlayers(Object match, String onField, String starting, Object team) {
        Object value = invoke(match, onField);
        if (!(value instanceof List<?>) || ((List<?>) value).size() < 7) value = invoke(match, starting);
        if (!(value instanceof List<?>) || ((List<?>) value).size() < 7) value = invoke(team, "kc");
        if (!(value instanceof List<?>)) return Collections.emptyList();
        List<Object> ordered = new ArrayList<Object>((List<?>) value);
        if (ordered.size() > 11) ordered = new ArrayList<Object>(ordered.subList(0, 11));
        for (int i = 0; i < ordered.size(); i++) {
            if (integer(invoke(ordered.get(i), "getPosicao"), -1) == 0) {
                if (i > 0) ordered.add(0, ordered.remove(i));
                break;
            }
        }
        return ordered;
    }

    private List<String> namesFrom(Object value) {
        if (!(value instanceof List<?>)) return Collections.emptyList();
        List<String> names = new ArrayList<String>();
        for (Object player : (List<?>) value) {
            String name = string(invoke(player, "getNome"), null);
            if (name != null && name.trim().length() > 1 && !names.contains(name)) names.add(name.trim());
            if (names.size() == 11) break;
        }
        return names;
    }

    private void setNames(Dot[] dots, List<String> names) {
        for (int i = 0; i < dots.length && i < names.size(); i++) dots[i].name = shortName(names.get(i));
    }

    private void updateLineup(Dot[] dots, List<?> players, boolean mirror) {
        if (players.isEmpty()) return;
        int count = Math.min(dots.length, players.size());
        String[] names = new String[count];
        for (int p = 0; p < count; p++) names[p] = playerName(players.get(p));
        int teamSide = mirror ? 1 : 0;
        if (holdOutgoingBall(dots, names, teamSide)) return;
        int[] slotOf = new int[count];
        boolean[] taken = new boolean[dots.length];
        boolean[] expelled = new boolean[count];
        for (int p = 0; p < count; p++) {
            slotOf[p] = -1;
            expelled[p] = p > 0 && cardFoulPhase == 0 && redCarded.contains(playerKey(teamSide, names[p]));
        }
        slotOf[0] = 0;
        taken[0] = true;
        for (int p = 1; p < count; p++) {
            if (expelled[p]) continue;
            for (int d = 1; d < dots.length; d++) {
                if (!taken[d] && dots[d].known && names[p].equals(dots[d].fullName)) {
                    slotOf[p] = d;
                    taken[d] = true;
                    break;
                }
            }
        }
        for (int p = 1; p < count; p++) {
            if (slotOf[p] >= 0 || expelled[p]) continue;
            int preferred = p < dots.length && !taken[p] ? p : -1;
            if (preferred < 0) {
                for (int d = 1; d < dots.length; d++) {
                    if (!taken[d]) { preferred = d; break; }
                }
            }
            if (preferred < 0) continue;
            slotOf[p] = preferred;
            taken[preferred] = true;
        }
        for (int d = 0; d < dots.length; d++) {
            if (!taken[d] && dots[d].active) {
                if (dots[d].known) addGhost(dots[d], teamSide);
                detachBall(teamSide, d);
                dots[d].active = false;
                if (receivingPlayer == d) receivingPlayer = -1;
            }
        }
        for (int p = 0; p < count; p++) {
            int d = slotOf[p];
            if (d < 0) continue;
            Dot dot = dots[d];
            boolean replaced = dot.known && !names[p].equals(dot.fullName);
            if (replaced && dot.active && d != 0) {
                addGhost(dot, teamSide);
                detachBall(teamSide, d);
            }
            boolean returning = !dot.active;
            dot.fullName = names[p];
            dot.name = shortName(names[p]);
            if (dot.known && (replaced || returning) && d != 0) {
                dot.entering = true;
                dot.currentX = .50 + (mirror ? .03 : -.03);
                dot.currentY = .975;
                dot.velocityX = 0;
                dot.velocityY = 0;
            }
            dot.active = true;
            dot.known = names[p].length() > 0;
        }
        if (cardFoulPhase == 0) {
            for (int d = 1; d < dots.length; d++) {
                if (dots[d].active && redCarded.contains(playerKey(teamSide, dots[d].fullName))) {
                    addGhost(dots[d], teamSide);
                    detachBall(teamSide, d);
                    dots[d].active = false;
                }
            }
        }
        dots[0].x = mirror ? .94 : .06;
        dots[0].y = .50;
        dots[0].roleLine = 0;
        dots[0].wideRole = false;
        List<Integer> fullbacks = new ArrayList<Integer>();
        List<Integer> centreBacks = new ArrayList<Integer>();
        List<Integer> midfielders = new ArrayList<Integer>();
        List<Integer> forwards = new ArrayList<Integer>();
        for (int p = 1; p < count; p++) {
            if (slotOf[p] < 0) continue;
            int position = integer(invoke(players.get(p), "getPosicao"), -1);
            Integer boxed = Integer.valueOf(p);
            if (position == 1) fullbacks.add(boxed);
            else if (position == 2) centreBacks.add(boxed);
            else if (position == 3) midfielders.add(boxed);
            else if (position == 4) forwards.add(boxed);
            else if (p <= 4) centreBacks.add(boxed);
            else if (p <= 8) midfielders.add(boxed);
            else forwards.add(boxed);
        }
        sortBySide(fullbacks, players);
        sortBySide(centreBacks, players);
        sortBySide(midfielders, players);
        sortBySide(forwards, players);
        if (fullbacks.size() > 2) {
            while (fullbacks.size() > 2) midfielders.add(fullbacks.remove(fullbacks.size() - 1));
            sortBySide(midfielders, players);
        }
        if (fullbacks.size() == 2) {
            placeDot(dots, slotOf[fullbacks.get(0).intValue()], .20, .14, 1, true, mirror);
            placeDot(dots, slotOf[fullbacks.get(1).intValue()], .20, .86, 1, true, mirror);
        } else if (fullbacks.size() == 1) {
            int index = fullbacks.get(0).intValue();
            int side = integer(invoke(players.get(index), "getLado"), 0);
            placeDot(dots, slotOf[index], .20, side == 0 ? .14 : .86, 1, true, mirror);
        }
        double backLow = fullbacks.isEmpty() ? .22 : .32;
        double backHigh = fullbacks.isEmpty() ? .78 : .68;
        spreadLine(dots, slotOf, centreBacks, .17, backLow, backHigh, 1, mirror);
        spreadLine(dots, slotOf, midfielders, .33, .16, .84, 2, mirror);
        spreadLine(dots, slotOf, forwards, .46, forwards.size() >= 3 ? .20 : .34,
                forwards.size() >= 3 ? .80 : .66, 3, mirror);
    }

    private boolean holdOutgoingBall(Dot[] dots, String[] names, int side) {
        int outgoing = -1;
        for (int d = 1; d < dots.length && outgoing < 0; d++) {
            if (!dots[d].active || !dots[d].known || !hasBallRole(side, d)) continue;
            boolean present = false;
            for (String name : names) {
                if (name.equals(dots[d].fullName)) { present = true; break; }
            }
            if (!present) outgoing = d;
        }
        if (outgoing < 0) {
            substitutionHoldSince = 0;
            return false;
        }
        long now = clockNow();
        if (substitutionHoldSince == 0) substitutionHoldSince = now;
        if (now - substitutionHoldSince > 4000L) {
            substitutionHoldSince = 0;
            return false;
        }
        releaseBallFrom(side, outgoing, now);
        return true;
    }

    private boolean hasBallRole(int side, int index) {
        if (ballInFlight && receivingSide == side && receivingPlayer == index) return true;
        if (looseBall && looseSide == side && looseChaser == index) return true;
        if (tackleActive && tackleSide == side && tackler == index) return true;
        return !looseBall && !ballInFlight && possessingSide == side && possessingPlayer == index;
    }

    private void releaseBallFrom(int side, int index, long now) {
        Dot[] team = side == 0 ? home : away;
        Dot outgoing = team[index];
        double gap = distance(outgoing.currentX, outgoing.currentY, ballX, ballY);
        if (tackleActive && tackleSide == side && tackler == index) {
            tackler = nearestActive(team, ballX, ballY, index, false);
            return;
        }
        if (looseBall && looseSide == side && looseChaser == index) {
            if (gap > .08) {
                looseChaser = nearestActive(team, ballX, ballY, index, true);
                looseSince = now;
            }
            return;
        }
        if (ballInFlight || hasAnimationStoppage() || cardFoulPhase != 0) return;
        if (gap > CONTACT * 1.5) return;
        int next = nearestProgressivePlayer(team, outgoing, index);
        if (next < 0 || next == index) return;
        double travel = distance(team[next].currentX, team[next].currentY, outgoing.currentX, outgoing.currentY);
        beginPassTo(side, next, now, (int) (420 + travel * 1500));
    }

    private void detachBall(int side, int index) {
        if (hasAnimationStoppage()) return;
        Dot[] team = side == 0 ? home : away;
        if (ballInFlight && receivingSide == side && receivingPlayer == index) {
            receivingPlayer = nearestActive(team, ballToX, ballToY, index, true);
        }
        if (tackleActive && tackleSide == side && tackler == index) {
            tackler = nearestActive(team, ballX, ballY, index, false);
        }
        if (!looseBall && !ballInFlight && possessingSide == side && possessingPlayer == index) {
            looseBall = true;
            looseSide = side;
            looseChaser = index;
            looseSince = clockNow();
        }
        if (looseBall && looseSide == side && looseChaser == index) {
            looseChaser = nearestActive(team, ballX, ballY, index, true);
            looseSince = clockNow();
        }
    }

    private void sortBySide(List<Integer> group, final List<?> players) {
        Collections.sort(group, new Comparator<Integer>() {
            @Override public int compare(Integer left, Integer right) {
                int a = integer(invoke(players.get(left.intValue()), "getLado"), 1);
                int b = integer(invoke(players.get(right.intValue()), "getLado"), 1);
                return a == b ? left.intValue() - right.intValue() : a - b;
            }
        });
    }

    private void spreadLine(Dot[] dots, int[] slotOf, List<Integer> group, double x,
                            double low, double high, int roleLine, boolean mirror) {
        int size = group.size();
        for (int order = 0; order < size; order++) {
            double y = size == 1 ? .50 : low + (high - low) * order / (double) (size - 1);
            boolean wide = roleLine == 2 && (y <= .27 || y >= .73);
            placeDot(dots, slotOf[group.get(order).intValue()], x, y, roleLine, wide, mirror);
        }
    }

    private void placeDot(Dot[] dots, int index, double x, double y, int roleLine, boolean wide, boolean mirror) {
        if (index < 0 || index >= dots.length) return;
        dots[index].x = mirror ? 1.0 - x : x;
        dots[index].y = y;
        dots[index].roleLine = roleLine;
        dots[index].wideRole = wide;
    }

    private String shortName(String name) {
        String[] words = name.trim().split("\\s+");
        if (words.length == 1) return words[0];
        String first = words[0];
        String last = words[words.length - 1];
        String full = first + " " + last;
        if (full.length() <= 16) return full;
        return first.substring(0, 1).toUpperCase(Locale.ROOT) + ". " + last;
    }

    private void applyEvent(String text) {
        event = text;
    }

    private boolean mentions(String text, Dot[] team) {
        return findPlayer(text, team) >= 0;
    }

    private int findPlayer(String text, Dot[] team) {
        String value = normalizedName(text);
        if (value.length() == 0) return -1;
        for (int i = 0; i < team.length; i++) {
            String full = normalizedName(team[i].fullName);
            if (full.length() > 2 && (value.equals(full) || value.contains(full))) return i;
        }
        int found = -1;
        for (int i = 0; i < team.length; i++) {
            String display = normalizedName(team[i].name);
            if (display.length() > 2 && value.contains(display)) {
                if (found >= 0) return -1;
                found = i;
            }
        }
        return found;
    }

    private String normalizedName(String value) {
        if (value == null) return "";
        return value.toLowerCase(Locale.ROOT).replace(".", "")
                .replaceAll("[^a-z0-9áàâãéêíóôõúüç ]", " ")
                .replaceAll("\\s+", " ").trim();
    }

    private boolean containsAny(String value, String... terms) {
        for (String term : terms) if (value.contains(term)) return true;
        return false;
    }

    private double movingX(Dot dot, int index, long now) {
        return dot.currentX;
    }

    private double movingY(Dot dot, int index, long now) {
        return dot.currentY;
    }

    private void updatePlayerTargets() {
        updateTeamTargets(home, false);
        updateTeamTargets(away, true);
        if (penaltyPhase == 0 && freeKickPhase == 0) {
            enforceTeamSpacing(home, 0);
            enforceTeamSpacing(away, 1);
        }
    }

    private void updateTeamTargets(Dot[] team, boolean awaySide) {
        boolean kickoff = !openingKickoffDone;
        boolean hasBall = possessingSide == (awaySide ? 1 : 0);
        Dot[] opponents = awaySide ? home : away;
        int sideIndex = awaySide ? 1 : 0;
        double direction = awaySide ? -1.0 : 1.0;
        int primaryPresser = nearestPlayer(team, ballX, ballY, -1, -1);
        int secondaryPresser = nearestPlayer(team, ballX, ballY, primaryPresser, -1);
        int marking = Math.max(0, Math.min(2, tactic(sideIndex, 2, 0)));
        int focus = tactic(sideIndex, 3, 0) == 1 ? 1 : 0;
        int style = tactic(sideIndex, 1, 0);
        int tertiaryPresser = marking == 2 ? nearestPlayer(team, ballX, ballY, primaryPresser, secondaryPresser) : -1;
        double secondaryPress = marking == 0 ? .10 : marking == 1 ? .25 : .40;
        double markTightness = marking == 0 ? .08 : marking == 1 ? .16 : .26;
        double lineShift = (style == 1 ? .035 : style == 2 ? -.035 : 0)
                + (marking == 0 ? -.02 : marking == 2 ? .02 : 0);
        for (int i = 0; i < team.length; i++) {
            Dot dot = team[i];
            if (penaltyPhase != 0) {
                setPenaltyTarget(dot, i, sideIndex, awaySide);
                continue;
            }
            if (freeKickPhase != 0) {
                setFreeKickTarget(dot, i, sideIndex, awaySide);
                continue;
            }
            if (cardFoulPhase == 2) {
                setCardFoulTarget(dot, i, sideIndex);
                continue;
            }
            if (restartActive) {
                dot.targetX = dot.x;
                dot.targetY = dot.y;
                if (sideIndex == kickoffSide && i == kickoffPlayerA) {
                    dot.targetX = .50;
                    dot.targetY = .50;
                } else if (sideIndex == kickoffSide && i == kickoffPlayerB) {
                    dot.targetX = awaySide ? .565 : .435;
                    dot.targetY = .54;
                } else if (sideIndex != kickoffSide) {
                    dot.targetX = awaySide ? Math.max(dot.x, .565) : Math.min(dot.x, .435);
                } else {
                    dot.targetX = awaySide ? Math.max(dot.x, .515) : Math.min(dot.x, .485);
                }
                continue;
            }
            if (kickoff) {
                dot.targetX = dot.x;
                dot.targetY = dot.y;
                continue;
            }
            if (frames >= dot.nextWanderFrame) {
                dot.wanderX = (dot.random.nextDouble() - .5) * (i == 0 ? .008 : .035);
                dot.wanderY = (dot.random.nextDouble() - .5) * (i == 0 ? .018 : .065);
                dot.nextWanderFrame = frames + 75 + dot.random.nextInt(120);
            }

            double attackProgress = awaySide ? 1.0 - ballX : ballX;
            double shift = dot.roleLine == 0 ? .012 : dot.roleLine == 1 ? .07
                    : dot.roleLine == 2 ? .13 : .19;
            shift += Math.max(-.05, Math.min(.09, (attackProgress - .5) * .18));
            if (!hasBall) shift -= dot.roleLine == 3 ? .07 : .045;
            if (dot.roleLine > 0) shift += hasBall ? lineShift * .6 : lineShift;
            if (hasBall && style == 2 && dot.roleLine == 3) shift += .03;
            if (hasBall && focus == 1 && dot.wideRole) shift += .04;
            double targetX = dot.x + direction * shift;
            double targetY;
            if (dot.wideRole) {
                targetY = dot.y + (ballY - dot.y) * (hasBall ? .10 : .06) + dot.wanderY;
            } else {
                targetY = dot.y + (ballY - dot.y) * (hasBall ? .14 : .10) + dot.wanderY;
            }
            targetX += dot.wanderX;
            if (hasBall && dot.roleLine >= 2) {
                if (focus == 1 && dot.wideRole) targetY = targetY * .85 + (dot.y < .5 ? .07 : .93) * .15;
                else if (focus == 0 && !dot.wideRole) targetY = targetY * .82 + .50 * .18;
            }
            if (i > 0 && frames >= dot.nextRunCheck) {
                dot.nextRunCheck = frames + 140 + dot.random.nextInt(220);
                if (hasBall && dot.roleLine >= 2 && dot.random.nextInt(100) < 30) {
                    dot.runUntil = frames + 70 + dot.random.nextInt(90);
                    dot.runY = clamp(dot.y + (dot.random.nextDouble() - .5) * .30, .12, .88);
                }
            }
            if (hasBall && frames < dot.runUntil && i != possessingPlayer) {
                targetX += direction * (dot.roleLine == 3 ? .09 : .06);
                targetY = targetY * .55 + dot.runY * .45;
            } else if (!hasBall) {
                dot.runUntil = 0;
            }

            if (i == 0) {
                targetX = dot.x + (ballX - dot.x) * .025;
                targetY = .50 + (ballY - .50) * .10;
                if (ambientShotPhase == 1 && sideIndex != ambientShotSide) {
                    targetX = ambientShotSide == 0 ? .955 : .045;
                    targetY = ambientShotY;
                }
            } else if (ballInFlight && sideIndex == receivingSide && i == receivingPlayer) {
                targetX = ballToX - direction * .006;
                targetY = ballToY;
            } else if (hasBall && i == possessingPlayer && !ballInFlight && !looseBall) {
                double carry = dot.roleLine == 1 ? .018 : dot.roleLine == 2 ? .028 : .038;
                targetX = dot.currentX + direction * carry;
                targetY = dot.currentY + dot.wanderY * .18;
            } else if (!hasBall && i == primaryPresser) {
                targetX = ballX - direction * .025;
                targetY = ballY;
            } else if (!hasBall && i == secondaryPresser) {
                targetX = targetX * (1 - secondaryPress) + ballX * secondaryPress;
                targetY = targetY * (1 - secondaryPress - .03) + ballY * (secondaryPress + .03);
            } else if (!hasBall && i == tertiaryPresser) {
                targetX = targetX * .78 + ballX * .22;
                targetY = targetY * .75 + ballY * .25;
            } else if (!hasBall) {
                Dot marked = opponents[Math.min(i, opponents.length - 1)];
                targetX = targetX * (1 - markTightness) + (marked.currentX - direction * .035) * markTightness;
                targetY = targetY * (1 - markTightness) + marked.currentY * markTightness;
            }

            if ((plannedActionKey != null && plannedMinute - engineMinute <= 1) || pendingGoalStage == 1) {
                if (plannedActionKey != null && plannedType >= 2 && plannedType <= 5
                        && sideIndex == plannedSide && i == plannedActor) {
                    if (plannedActor == 0 && plannedType <= 4) {
                        targetX = plannedSide == 0 ? clamp(plannedSpotX - .035, .045, .18)
                                : clamp(plannedSpotX + .035, .82, .955);
                        targetY = plannedSpotY;
                    } else {
                        targetX = ballX;
                        targetY = ballY;
                    }
                } else if (plannedActionKey != null && plannedType >= 2 && plannedType <= 4
                        && plannedActor == 0 && sideIndex != plannedSide && i == plannedCardVictim) {
                    targetX = plannedSpotX;
                    targetY = plannedSpotY;
                } else if (hasPlannedShotSpot() && sideIndex == plannedSide && i == plannedActor) {
                    targetX = targetX * .35 + runInX(plannedSide) * .65;
                    targetY = targetY * .35 + plannedSpotY * .65;
                }
            }

            boolean eventActor = hasPlannedShotSpot() && sideIndex == plannedSide && i == plannedActor;
            if (dot.wideRole && !eventActor) {
                if (dot.y < .5) targetY = clamp(targetY, .08, .38);
                else targetY = clamp(targetY, .62, .92);
            } else {
                targetY = clamp(targetY, .14, .86);
            }
            if (eventActor) {
                targetX = clamp(targetX, .055, .945);
            } else if (dot.roleLine == 0) {
                targetX = clamp(targetX, awaySide ? .90 : .035, awaySide ? .965 : .10);
            } else if (dot.roleLine == 1) {
                targetX = clamp(targetX, awaySide ? .38 : .08, awaySide ? .92 : .62);
            } else if (dot.roleLine == 2) {
                targetX = clamp(targetX, .18, .82);
            } else {
                targetX = clamp(targetX, awaySide ? .055 : .43, awaySide ? .57 : .945);
            }
            dot.targetX = targetX;
            dot.targetY = targetY;
            applyBallRoleTarget(dot, i, sideIndex);
        }
    }

    private void refreshBallRoleTargets() {
        if (penaltyPhase != 0 || freeKickPhase != 0 || cardFoulPhase == 2 || restartActive) return;
        for (int i = 0; i < home.length; i++) if (home[i].active) applyBallRoleTarget(home[i], i, 0);
        for (int i = 0; i < away.length; i++) if (away[i].active) applyBallRoleTarget(away[i], i, 1);
    }

    private void applyBallRoleTarget(Dot dot, int index, int sideIndex) {
        if (ownGoalActive && pendingGoalStage == 1 && sideIndex != pendingGoalSide && index == ownGoalDefender) {
            dot.targetX = pendingGoalSide == 0 ? .925 : .075;
            dot.targetY = clamp(ballY, .38, .62);
            return;
        }
        if (penaltyBuild && penaltyFouler >= 0 && sideIndex != pendingGoalSide && index == penaltyFouler) {
            dot.targetX = ballX;
            dot.targetY = ballY;
            return;
        }
        if (cardFoulPhase == 1) {
            if (sideIndex == cardFoulOffenderSide && index == cardFoulOffender
                    && possessingSide != cardFoulOffenderSide && cardFoulEngaged) {
                if (index == 0) {
                    dot.targetX = cardFoulOffenderSide == 0 ? clamp(ballX, .045, .17) : clamp(ballX, .83, .955);
                    dot.targetY = clamp(ballY, .30, .70);
                } else {
                    dot.targetX = ballX;
                    dot.targetY = ballY;
                }
                return;
            }
            if (cardFoulOffender == 0 && sideIndex != cardFoulOffenderSide && sideIndex == possessingSide
                    && index == possessingPlayer && !looseBall && !ballInFlight) {
                Dot[] keepers = cardFoulOffenderSide == 0 ? home : away;
                dot.targetX = keepers[0].currentX;
                dot.targetY = keepers[0].currentY;
                return;
            }
        } else if (cardFoulPhase == 3 && sideIndex == 1 - cardFoulOffenderSide && index == cardFoulTaker) {
            double direction = sideIndex == 0 ? 1.0 : -1.0;
            dot.targetX = clamp(ballX - direction * .010, .03, .97);
            dot.targetY = ballY;
            return;
        }
        if (pendingGoalStage == 1 && sideIndex == pendingGoalSide && index == pendingGoalActor) {
            boolean carrying = !looseBall && !ballInFlight && possessingSide == sideIndex
                    && possessingPlayer == index;
            if (ballInFlight && receivingSide == sideIndex && receivingPlayer == index) {
                dot.targetX = ballToX;
                dot.targetY = ballToY;
            } else if (looseBall && looseSide == sideIndex && looseChaser == index) {
                dot.targetX = ballX;
                dot.targetY = ballY;
            } else if (carrying) {
                dot.targetX = plannedSpotX;
                dot.targetY = plannedSpotY;
            } else {
                dot.targetX = runInX(sideIndex);
                dot.targetY = plannedSpotY;
            }
        } else if (looseBall && sideIndex == looseSide && index == looseChaser) {
            dot.targetX = ballX;
            dot.targetY = ballY;
        } else if (tackleActive && sideIndex == tackleSide && index == tackler) {
            dot.targetX = ballX;
            dot.targetY = ballY;
        } else if (ballInFlight && sideIndex == receivingSide && index == receivingPlayer) {
            dot.targetX = ballToX;
            dot.targetY = ballToY;
        }
    }

    private boolean isAnchored(int side, int index) {
        if (ownGoalActive && pendingGoalStage == 1 && side != pendingGoalSide && index == ownGoalDefender) return true;
        if (penaltyBuild && penaltyFouler >= 0 && side != pendingGoalSide && index == penaltyFouler) return true;
        if (looseBall && side == looseSide && index == looseChaser) return true;
        if (ballInFlight && side == receivingSide && index == receivingPlayer) return true;
        if (tackleActive && side == tackleSide && index == tackler) return true;
        if (!looseBall && side == possessingSide && index == possessingPlayer) return true;
        if (pendingGoalStage == 1 && side == pendingGoalSide && index == pendingGoalActor) return true;
        if (restartActive && side == kickoffSide && (index == kickoffPlayerA || index == kickoffPlayerB)) return true;
        if (penaltyPhase != 0 && side == penaltySide && index == penaltyActor) return true;
        if (freeKickPhase != 0 && side == freeKickSide && index == freeKickActor) return true;
        if (cardFoulPhase >= 2 && side == 1 - cardFoulOffenderSide && index == cardFoulTaker) return true;
        return cardFoulPhase != 0 && side == cardFoulOffenderSide && index == cardFoulOffender
                && (cardFoulPhase != 1 || cardFoulEngaged);
    }

    private void setPenaltyTarget(Dot dot, int index, int sideIndex, boolean awaySide) {
        double direction = penaltySide == 0 ? 1.0 : -1.0;
        double spot = spotX(penaltySide);
        if (sideIndex == penaltySide && index == penaltyActor && penaltyPhase >= 2) {
            dot.targetX = penaltyPhase <= 3 ? spot - direction * .05 : spot;
            dot.targetY = .50;
        } else if (sideIndex != penaltySide && index == 0) {
            dot.targetX = penaltySide == 0 ? .962 : .038;
            dot.targetY = .50;
        } else if (index == 0) {
            dot.targetX = dot.x;
            dot.targetY = dot.y;
        } else {
            double boxEdge = penaltySide == 0 ? .845 : .155;
            double rowX = boxEdge - direction * (.025 + (index % 3) * .022 + (sideIndex == penaltySide ? .0 : .012));
            dot.targetX = rowX;
            dot.targetY = .22 + ((index * 3 + sideIndex * 2) % 9) * .07;
        }
    }

    private void setFreeKickTarget(Dot dot, int index, int sideIndex, boolean awaySide) {
        if (sideIndex == freeKickSide && index == freeKickActor) {
            double back = freeKickPhase <= 1 ? .035 : freeKickPhase == 2 ? .055 : 0.0;
            dot.targetX = clamp(plannedSpotX - freeKickUx * back, .02, .98);
            dot.targetY = clamp(plannedSpotY - freeKickUy * back, .04, .96);
            return;
        }
        double x = kickLayoutX[sideIndex][index];
        if (x >= 0) {
            dot.targetX = x;
            dot.targetY = kickLayoutY[sideIndex][index];
        } else {
            dot.targetX = dot.x;
            dot.targetY = dot.y;
        }
    }

    private void setCardFoulTarget(Dot dot, int index, int sideIndex) {
        if (sideIndex == cardFoulOffenderSide && index == cardFoulOffender) {
            double back = cardFoulOffenderSide == 0 ? -.022 : .022;
            dot.targetX = clamp(dot.currentX + back * .4, .03, .97);
            dot.targetY = dot.currentY;
        } else if (sideIndex == 1 - cardFoulOffenderSide && index == cardFoulTaker) {
            dot.targetX = dot.currentX;
            dot.targetY = dot.currentY;
        }
    }

    private void enforceTeamSpacing(Dot[] team, int side) {
        for (int pass = 0; pass < 2; pass++) {
            for (int i = 1; i < team.length; i++) {
                if (!team[i].active) continue;
                boolean anchorI = isAnchored(side, i);
                for (int j = i + 1; j < team.length; j++) {
                    if (!team[j].active) continue;
                    boolean anchorJ = isAnchored(side, j);
                    if (anchorI && anchorJ) continue;
                    double dx = team[j].targetX - team[i].targetX;
                    double dy = team[j].targetY - team[i].targetY;
                    double distance = Math.sqrt(dx * dx + dy * dy);
                    double minimum = team[i].wideRole || team[j].wideRole ? .092 : .080;
                    if (distance >= minimum) continue;
                    if (distance < .001) { dx = 0; dy = team[i].y <= team[j].y ? .01 : -.01; distance = .01; }
                    double push = (minimum - distance) * (anchorI || anchorJ ? 1.0 : .52);
                    double nx = dx / distance, ny = dy / distance;
                    if (!anchorI) {
                        team[i].targetX = clamp(team[i].targetX - nx * push, .035, .965);
                        team[i].targetY = clamp(team[i].targetY - ny * push, .06, .94);
                    }
                    if (!anchorJ) {
                        team[j].targetX = clamp(team[j].targetX + nx * push, .035, .965);
                        team[j].targetY = clamp(team[j].targetY + ny * push, .06, .94);
                    }
                }
            }
        }
    }

    private Dot nearestOpponent(Dot[] opponents, double x, double y) {
        Dot best = opponents[1];
        double bestDistance = Double.MAX_VALUE;
        for (int i = 1; i < opponents.length; i++) {
            double dx = opponents[i].currentX - x;
            double dy = opponents[i].currentY - y;
            double distance = dx * dx + dy * dy;
            if (distance < bestDistance) { bestDistance = distance; best = opponents[i]; }
        }
        return best;
    }

    private void updateReferee(double dt) {
        double targetX, targetY;
        if (cardFoulPhase >= 2) {
            Dot[] offenders = cardFoulOffenderSide == 0 ? home : away;
            Dot offender = offenders[Math.max(0, Math.min(offenders.length - 1, cardFoulOffender))];
            targetX = offender.currentX + (offender.currentX < .5 ? .05 : -.05);
            targetY = offender.currentY + (offender.currentY < .5 ? .07 : -.07);
        } else if (penaltyPhase != 0) {
            targetX = penaltySide == 0 ? .80 : .20;
            targetY = .26;
        } else if (freeKickPhase != 0) {
            targetX = clamp(wallCenterX + (freeKickSide == 0 ? .03 : -.03), .05, .95);
            targetY = clamp(wallCenterY + (wallCenterY < .5 ? .18 : -.18), .08, .92);
        } else if (restartActive || kickoffInProgress) {
            targetX = .50 + (kickoffSide == 0 ? .08 : -.08);
            targetY = .36;
        } else {
            if (distance(refAnchorX, refAnchorY, ballX, ballY) > .08) {
                refAnchorX = ballX;
                refAnchorY = ballY;
            }
            double direction = possessingSide == 0 ? 1.0 : -1.0;
            targetX = clamp(refAnchorX - direction * .10, .08, .92);
            targetY = clamp(refAnchorY + (refAnchorY < .5 ? .13 : -.13), .08, .92);
        }
        for (Dot[] team : new Dot[][] { home, away }) {
            for (Dot dot : team) {
                if (!dot.active) continue;
                double dx = refX - dot.currentX, dy = refY - dot.currentY;
                double d = Math.sqrt(dx * dx + dy * dy);
                if (d > .0005 && d < .035) {
                    targetX += dx / d * .03;
                    targetY += dy / d * .03;
                }
            }
        }
        double dx = targetX - refX, dy = targetY - refY;
        double d = Math.sqrt(dx * dx + dy * dy);
        double speed = .085 * Math.min(1.0, d / .08);
        double wantX = d < .0005 ? 0 : dx / d * speed, wantY = d < .0005 ? 0 : dy / d * speed;
        refVX += clamp(wantX - refVX, -.22 * dt, .22 * dt);
        refVY += clamp(wantY - refVY, -.22 * dt, .22 * dt);
        refX = clamp(refX + refVX * dt, .02, .98);
        refY = clamp(refY + refVY * dt, .03, .97);
    }

    private double colorGap(Color a, Color b) {
        double dr = a.getRed() - b.getRed(), dg = a.getGreen() - b.getGreen(), db = a.getBlue() - b.getBlue();
        return Math.sqrt(dr * dr * .3 + dg * dg * .59 + db * db * .11);
    }

    private Color mostDistinct(Color[] palette, int offset) {
        Color best = palette[0];
        double bestGap = -1;
        for (int i = 0; i < palette.length; i++) {
            Color candidate = palette[(i + offset) % palette.length];
            double gap = Math.min(colorGap(candidate, homeColor), colorGap(candidate, awayColor));
            if (gap > bestGap + 8) { bestGap = gap; best = candidate; }
        }
        return best;
    }

    private void addGhost(Dot dot, int side) {
        Ghost ghost = new Ghost();
        ghost.x = dot.currentX;
        ghost.y = dot.currentY;
        ghost.side = side;
        ghost.name = dot.name;
        ghost.key = playerKey(side, dot.fullName);
        ghosts.add(ghost);
        if (ghosts.size() > 6) ghosts.remove(0);
    }

    private void updateGhosts(double dt) {
        for (int i = ghosts.size() - 1; i >= 0; i--) {
            Ghost ghost = ghosts.get(i);
            double targetY = ghost.y < .5 ? -.03 : 1.03;
            ghost.y += (targetY > ghost.y ? 1 : -1) * .075 * dt;
            if (ghost.y < -.02 || ghost.y > 1.02) ghosts.remove(i);
        }
    }

    private void updatePlayerPositions() {
        double total = frameSeconds * motion;
        int steps = Math.max(1, Math.min(60, (int) Math.ceil(total / .02)));
        double dt = total / steps;
        for (int step = 0; step < steps; step++) {
            updateGhosts(dt);
            updateReferee(dt);
            updateTeamPositions(home, away, 0, dt);
            updateTeamPositions(away, home, 1, dt);
        }
    }

    private boolean anyEntering() {
        for (Dot dot : home) if (dot.active && dot.entering) return true;
        for (Dot dot : away) if (dot.active && dot.entering) return true;
        return false;
    }

    private void updateTeamPositions(Dot[] team, Dot[] opponents, int side, double dt) {
        for (int index = 0; index < team.length; index++) {
            Dot dot = team[index];
            if (!dot.active) continue;
            if (dot.entering && distance(dot.currentX, dot.currentY, dot.targetX, dot.targetY) < .03
                    && dot.currentY < .95) {
                dot.entering = false;
            }
            boolean anchored = isAnchored(side, index);
            double dx = dot.targetX - dot.currentX;
            double dy = dot.targetY - dot.currentY;
            double distance = Math.sqrt(dx * dx + dy * dy);
            double maxSpeed = dot.roleLine == 0 ? .045 : .105;
            if (index == possessingPlayer && side == possessingSide && !looseBall) {
                maxSpeed = tackleActive ? .06 : .118;
            }
            if (pendingGoalStage == 1 && side == pendingGoalSide && index == pendingGoalActor
                    && goalFinalPassed) maxSpeed = .145;
            boolean ballRole = (looseBall && side == looseSide && index == looseChaser)
                    || (ballInFlight && side == receivingSide && index == receivingPlayer)
                    || (tackleActive && side == tackleSide && index == tackler);
            if (anchored && !(index == possessingPlayer && side == possessingSide && !looseBall)) {
                maxSpeed = Math.max(maxSpeed, ballRole ? (index == 0 ? .10 : .135) : .112);
            }
            if (penaltyBuild && penaltyFouler >= 0 && side != pendingGoalSide && index == penaltyFouler) {
                maxSpeed = .15;
            }
            if (cardFoulPhase == 1 && cardFoulEngaged) {
                if (side == cardFoulOffenderSide && index == cardFoulOffender) {
                    maxSpeed = index == 0 ? .11 : .15;
                } else if (side != cardFoulOffenderSide && side == possessingSide && index == possessingPlayer
                        && !looseBall) {
                    maxSpeed = clockNow() - cardFoulStarted > 7000L ? .02 : .065;
                }
            }
            if (dot.entering) maxSpeed = Math.max(maxSpeed, .14);
            double arrival = anchored ? .030 : .065;
            double desiredSpeed = maxSpeed * Math.min(1.0, distance / arrival);
            double desiredVX = distance < .0005 ? 0 : dx / distance * desiredSpeed;
            double desiredVY = distance < .0005 ? 0 : dy / distance * desiredSpeed;
            if (!anchored) {
                for (int j = 1; j < team.length; j++) {
                    if (j == index || !team[j].active) continue;
                    double sx = dot.currentX - team[j].currentX;
                    double sy = dot.currentY - team[j].currentY;
                    double sd = Math.sqrt(sx * sx + sy * sy);
                    if (sd > .0005 && sd < .068) {
                        double force = (.068 - sd) * 1.9;
                        desiredVX += sx / sd * force;
                        desiredVY += sy / sd * force;
                    }
                }
                for (int j = 1; j < opponents.length; j++) {
                    if (!opponents[j].active) continue;
                    double sx = dot.currentX - opponents[j].currentX;
                    double sy = dot.currentY - opponents[j].currentY;
                    double sd = Math.sqrt(sx * sx + sy * sy);
                    if (sd > .0005 && sd < .025) {
                        desiredVX += sx / sd * (.025 - sd);
                        desiredVY += sy / sd * (.025 - sd);
                    }
                }
            }
            double acceleration = anchored ? .42 : .34;
            double changeX = desiredVX - dot.velocityX;
            double changeY = desiredVY - dot.velocityY;
            double change = Math.sqrt(changeX * changeX + changeY * changeY);
            double maximumChange = acceleration * dt;
            if (change > maximumChange && change > 0) {
                changeX = changeX / change * maximumChange;
                changeY = changeY / change * maximumChange;
            }
            dot.velocityX += changeX;
            dot.velocityY += changeY;
            dot.currentX = clamp(dot.currentX + dot.velocityX * dt, .015, .985);
            dot.currentY = clamp(dot.currentY + dot.velocityY * dt, .03, .985);
        }
    }

    private double clamp(double value, double low, double high) {
        return Math.max(low, Math.min(high, value));
    }

    @Override protected void paintComponent(Graphics graphics) {
        super.paintComponent(graphics);
        Graphics2D g = (Graphics2D) graphics.create();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        int w = getWidth(), h = getHeight();
        int top = 4;
        int bottom = h - 4, left = 4, right = w - 4;
        int fieldW = right - left, fieldH = bottom - top;
        g.drawImage(pitch(fieldW, fieldH), left, top, null);
        g.setColor(LINE);
        g.setStroke(STROKE_2);
        g.drawRect(left + 2, top + 2, fieldW - 4, fieldH - 4);
        int mid = left + fieldW / 2;
        g.drawLine(mid, top + 2, mid, bottom - 2);
        int circle = Math.min(96, fieldH / 3);
        g.drawOval(mid - circle / 2, top + fieldH / 2 - circle / 2, circle, circle);
        g.fillOval(mid - 3, top + fieldH / 2 - 3, 6, 6);
        drawPenaltyArea(g, left, top, fieldW, fieldH, false);
        drawPenaltyArea(g, left, top, fieldW, fieldH, true);
        long now = clockNow();
        drawTeam(g, home, homeColor, homeAccent, homeStripe, homeKeeper, left, top, fieldW, fieldH, now);
        drawTeam(g, away, awayColor, awayAccent, awayStripe, awayKeeper, left, top, fieldW, fieldH, now);
        if (homeTeamRef != null) {
            if (refereeKit == null) refereeKit = mostDistinct(REFEREE_KITS, 0);
            if (ballAccent == null) ballAccent = mostDistinct(BALL_ACCENTS, ballStyle);
        }
        Color kit = refereeKit == null ? REFEREE_KITS[0] : refereeKit;
        int rx = left + (int) (viewX(refX) * fieldW), ry = top + (int) (refY * fieldH);
        g.setColor(SHADOW);
        g.fillOval(rx - 7, ry - 5, 16, 16);
        g.setColor(kit);
        g.fillOval(rx - 8, ry - 8, 16, 16);
        g.setColor(kit.getRed() + kit.getGreen() + kit.getBlue() < 200 ? Color.WHITE : new Color(20, 20, 20));
        g.setStroke(STROKE_2);
        g.drawOval(rx - 8, ry - 8, 16, 16);
        g.setFont(NAME_FONT);
        String refLabel = shortName(refereeName);
        int refW = g.getFontMetrics().stringWidth(refLabel);
        g.setFont(NAME_FONT_LIGHT);
        refW = g.getFontMetrics().stringWidth(refLabel);
        g.setColor(new Color(0, 0, 0, 80));
        g.drawString(refLabel, rx - refW / 2 + 1, ry - 11);
        g.setColor(new Color(255, 236, 140, 170));
        g.drawString(refLabel, rx - refW / 2, ry - 12);
        for (Ghost ghost : ghosts) {
            int gx = left + (int) (viewX(ghost.x) * fieldW);
            int gy = top + (int) (clamp(ghost.y, 0, 1) * fieldH);
            Color fill = ghost.side == 0 ? homeColor : awayColor;
            g.setColor(new Color(fill.getRed(), fill.getGreen(), fill.getBlue(), 150));
            g.fillOval(gx - 10, gy - 10, 20, 20);
            if (redCarded.contains(ghost.key)) {
                g.setColor(CARD_RED);
                g.fillRoundRect(gx + 8, gy - 13, 6, 10, 2, 2);
            }
            g.setFont(NAME_FONT);
            g.setColor(new Color(255, 255, 255, 170));
            g.drawString(ghost.name, gx - g.getFontMetrics().stringWidth(ghost.name) / 2, gy - 14);
        }
        int bx = left + (int) (viewX(ballX) * fieldW);
        int by = top + (int) (ballY * fieldH);
        int radius = 7 + (int) Math.round(ballLift * 3);
        int shadowOffset = 2 + (int) Math.round(ballLift * 7);
        g.setColor(SHADOW);
        g.fillOval(bx - 5 + shadowOffset / 2, by - 3 + shadowOffset, 11, 11);
        drawBall(g, bx, by - (int) Math.round(ballLift * 5), radius);


        if (DEBUG_TOOLS) drawDebugButtons(g, w);
        g.dispose();
        Toolkit.getDefaultToolkit().sync();
    }

    private void drawDebugButtons(Graphics2D g, int width) {
        g.setFont(NAME_FONT);
        FontMetrics metrics = g.getFontMetrics();
        int bw = 118, bh = 16, top = 26;
        for (int team = 0; team < 2; team++) {
            int x = width - (2 - team) * (bw + 6) - 10;
            String title = team == 0 ? homeName : awayName;
            g.setColor(new Color(0, 0, 0, 200));
            g.fillRoundRect(x, 10, bw, 14, 6, 6);
            g.setColor(team == 0 ? homeColor : awayColor);
            g.drawString(title.length() > 18 ? title.substring(0, 18) : title, x + 4, 21);
            for (int i = 0; i < DEBUG_LABELS.length; i++) {
                Rectangle area = new Rectangle(x, top + i * (bh + 2), bw, bh);
                debugButtons[team * DEBUG_LABELS.length + i] = area;
                g.setColor(new Color(20, 20, 20, 190));
                g.fillRoundRect(area.x, area.y, area.width, area.height, 6, 6);
                g.setColor(CARD_YELLOW);
                g.drawRoundRect(area.x, area.y, area.width, area.height, 6, 6);
                g.setColor(Color.WHITE);
                g.drawString(DEBUG_LABELS[i], area.x + (bw - metrics.stringWidth(DEBUG_LABELS[i])) / 2,
                        area.y + 12);
            }
        }
    }

    private boolean handleDebugClick(MouseEvent event) {
        if (!DEBUG_TOOLS) return false;
        for (int i = 0; i < debugButtons.length; i++) {
            if (debugButtons[i] != null && debugButtons[i].contains(event.getPoint())) {
                runDebug(i % DEBUG_LABELS.length, i / DEBUG_LABELS.length);
                return true;
            }
        }
        return false;
    }

    private void runDebug(int option, int team) {
        if (hasAnimationStoppage() || penaltyPhase != 0 || ballInFlight) return;
        long now = clockNow();
        Dot[] own = team == 0 ? home : away;
        double direction = team == 0 ? 1.0 : -1.0;
        if (option <= 3) {
            double[] distances = {.17, .23, .29, .36};
            double goalX = team == 0 ? 1.0 : 0.0;
            double y = .32 + random.nextDouble() * .36;
            double x = goalX - direction * distances[option];
            int taker = nearestActive(own, x, y, -1, false);
            int roll = random.nextInt(100);
            startFreeKick(now, team, taker, x, y, 4 - option, roll < 50 ? 0 : roll < 80 ? 1 : 2);
            event = "Debug: falta com " + freeKickWall + " na barreira";
            goalEventText = "Debug: gol de falta · " + own[freeKickActor].name;
        } else if (option == 4) {
            startPenaltySetup(now, team, -1);
            penaltyDebug = true;
        } else if (option == 5 || option == 6 || option == 7) {
            int offender = nearestActive(own, ballX, ballY, -1, false);
            String key = option == 5 ? null : playerKey(team, own[offender].fullName);
            String text = option == 5 ? "Debug: falta" : option == 6 ? "Debug: amarelo" : "Debug: vermelho";
            startCardFoul(now, team, offender, text + " · " + own[offender].name, key, option == 7);
        } else if (option == 8) {
            int victim = nearestActive(own, ballX, ballY, -1, false);
            injured.add(playerKey(team, own[victim].fullName));
            event = "Debug: lesão · " + own[victim].name;
            simpleStoppageUntil = now + 1500L;
            controlUntil = Long.MAX_VALUE;
            if (possessingSide == team && possessingPlayer == victim) {
                looseBall = true;
                looseSide = team;
                looseChaser = nearestActive(own, ballX, ballY, victim, false);
                looseSince = now;
            }
        } else if (option == 9 || option == 10) {
            boolean ownGoalDebug = option == 10;
            int scoringSide = ownGoalDebug ? 1 - team : team;
            Dot[] scorers = scoringSide == 0 ? home : away;
            int scorer = nearestActive(scorers, scoringSide == 0 ? .80 : .20, .50, -1, false);
            plannedSide = scoringSide;
            plannedActor = scorer;
            plannedType = 1;
            plannedSubtype = 0;
            choosePlannedSpot(1, 0);
            pendingGoalStage = 1;
            pendingGoalSide = scoringSide;
            pendingGoalActor = scorer;
            plannedAssist = -1;
            goalStageDeadline = now + goalBudget();
            goalBuildPasses = 0;
            goalBuildTarget = minuteDelay() <= 700 ? 0 : random.nextInt(2);
            goalFinalPassed = false;
            goalReboundPhase = 0;
            goalVariant = ownGoalDebug ? 1 : random.nextInt(3);
            ownGoalActive = ownGoalDebug;
            ownGoalStage = 0;
            ownGoalDefender = ownGoalDebug ? nearestActive(own, scoringSide == 0 ? .92 : .08, .50, -1, false) : -1;
            goalEventText = ownGoalDebug ? "Debug: gol contra · " + own[ownGoalDefender].name
                    : "Debug: gol · " + scorers[scorer].name;
            controlUntil = Math.min(controlUntil, now + 300L);
        } else if (option == 11) {
            int leaving = 1 + random.nextInt(own.length - 1);
            Dot dot = own[leaving];
            event = "Debug: sai " + dot.name + " · entra Reserva";
            dot.fullName = "Reserva Debug " + team + leaving;
            dot.name = shortName(dot.fullName);
            dot.currentX = .50 + (team == 1 ? .03 : -.03);
            dot.currentY = .975;
            dot.velocityX = 0;
            dot.velocityY = 0;
        }
    }

    private BufferedImage pitch(int width, int height) {
        int condition = pitchCondition < 0 ? 0 : pitchCondition;
        String key = width + "x" + height + ":" + condition;
        if (pitchImage != null && key.equals(pitchKey)) return pitchImage;
        width = Math.max(1, width);
        height = Math.max(1, height);
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        int[][] lightGreen = { {38, 146, 64}, {44, 134, 60}, {72, 124, 56}, {90, 116, 58} };
        int[][] darkGreen = { {30, 126, 55}, {37, 118, 53}, {63, 112, 51}, {80, 105, 53} };
        int[] dry = {150, 146, 82};
        int[] dirt = {124, 96, 64};
        double[] wearAmount = {0, .30, .70, 1.15};
        double[] dryAmount = {0, .05, .35, .55};
        double[] grain = {5, 6, 9, 12};
        long seed = System.identityHashCode(matchRef) * 31L + condition;
        double[] coarse = noiseGrid(seed, 13, 9);
        double[] fine = noiseGrid(seed + 7, 41, 25);
        Random speck = new Random(seed + 11);
        int bands = condition == 0 ? 14 : 12;
        int[] pixels = new int[width * height];
        for (int y = 0; y < height; y++) {
            double ny = y / (double) height;
            for (int x = 0; x < width; x++) {
                double nx = x / (double) width;
                int band = (int) (nx * bands);
                int[] base = (band & 1) == 0 ? lightGreen[condition] : darkGreen[condition];
                double smooth = sample(coarse, 13, 9, nx, ny);
                double detail = sample(fine, 41, 25, nx, ny);
                double zone = wearZone(nx, ny);
                double wear = clamp(zone * wearAmount[condition] * (.55 + smooth * .9) - (1 - detail) * .25, 0, 1);
                double dryness = clamp(dryAmount[condition] * (smooth * 1.2 - .2), 0, 1);
                double jitter = (speck.nextDouble() - .5) * grain[condition] + (detail - .5) * grain[condition];
                double r = base[0] + (dry[0] - base[0]) * dryness;
                double gr = base[1] + (dry[1] - base[1]) * dryness;
                double b = base[2] + (dry[2] - base[2]) * dryness;
                r += (dirt[0] - r) * wear;
                gr += (dirt[1] - gr) * wear;
                b += (dirt[2] - b) * wear;
                int ri = (int) clamp(r + jitter, 0, 255), gi = (int) clamp(gr + jitter, 0, 255),
                        bi = (int) clamp(b + jitter * .6, 0, 255);
                pixels[y * width + x] = (ri << 16) | (gi << 8) | bi;
            }
        }
        image.setRGB(0, 0, width, height, pixels, 0, width);
        pitchImage = image;
        pitchKey = key;
        return image;
    }

    private double wearZone(double x, double y) {
        double zone = 0;
        for (double goal : new double[] { .045, .955 }) {
            double dx = (x - goal) / .07, dy = (y - .5) / .16;
            zone = Math.max(zone, Math.exp(-(dx * dx + dy * dy)));
            double sx = (x - (goal < .5 ? .11 : .89)) / .03, sy = (y - .5) / .05;
            zone = Math.max(zone, .8 * Math.exp(-(sx * sx + sy * sy)));
        }
        double cx = (x - .5) / .07, cy = (y - .5) / .18;
        zone = Math.max(zone, .7 * Math.exp(-(cx * cx + cy * cy)));
        double lane = Math.exp(-Math.pow((y - .5) / .22, 2)) * .35;
        return Math.max(zone, lane);
    }

    private double[] noiseGrid(long seed, int columns, int rows) {
        Random grid = new Random(seed);
        double[] values = new double[columns * rows];
        for (int i = 0; i < values.length; i++) values[i] = grid.nextDouble();
        return values;
    }

    private double sample(double[] grid, int columns, int rows, double x, double y) {
        double gx = x * (columns - 1), gy = y * (rows - 1);
        int x0 = (int) Math.floor(gx), y0 = (int) Math.floor(gy);
        int x1 = Math.min(columns - 1, x0 + 1), y1 = Math.min(rows - 1, y0 + 1);
        double tx = gx - x0, ty = gy - y0;
        tx = tx * tx * (3 - 2 * tx);
        ty = ty * ty * (3 - 2 * ty);
        double a = grid[y0 * columns + x0], b = grid[y0 * columns + x1];
        double c = grid[y1 * columns + x0], d = grid[y1 * columns + x1];
        return (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty;
    }

    private boolean inFocus(int side, int index, Dot dot) {
        if (!looseBall && side == possessingSide && index == possessingPlayer) return true;
        if (ballInFlight && side == receivingSide && index == receivingPlayer) return true;
        if (looseBall && side == looseSide && index == looseChaser) return true;
        if (pendingGoalStage != 0 && side == pendingGoalSide && index == pendingGoalActor) return true;
        if (cardFoulPhase != 0 && side == cardFoulOffenderSide && index == cardFoulOffender) return true;
        if (penaltyPhase >= 2 && side == penaltySide && index == penaltyActor) return true;
        if (freeKickPhase != 0 && side == freeKickSide && index == freeKickActor) return true;
        return distance(dot.currentX, dot.currentY, ballX, ballY) < .10;
    }

    private void drawBall(Graphics2D g, int cx, int cy, int radius) {
        Color mark = ballAccent == null ? BALL_ACCENTS[0] : ballAccent;
        g.setColor(Color.WHITE);
        g.fillOval(cx - radius, cy - radius, radius * 2, radius * 2);
        Graphics2D ball = (Graphics2D) g.create();
        ball.clip(new java.awt.geom.Ellipse2D.Double(cx - radius, cy - radius, radius * 2, radius * 2));
        ball.translate(cx, cy);
        ball.rotate(ballSpin);
        ball.setColor(mark);
        int r = radius;
        switch (ballStyle) {
            case 0:
                ball.fillPolygon(pentagon(0, 0, r * .40));
                for (int k = 0; k < 5; k++) {
                    double a = k * Math.PI * 2 / 5;
                    ball.fillPolygon(pentagon(Math.cos(a) * r * 1.05, Math.sin(a) * r * 1.05, r * .36));
                }
                break;
            case 1:
            case 2:
                for (int k = 0; k < 3; k++) {
                    double a = k * Math.PI * 2 / 3;
                    Graphics2D arm = (Graphics2D) ball.create();
                    arm.rotate(a);
                    arm.fillArc(r / 6, -r / 2, r, r, 90, 180);
                    if (ballStyle == 2) arm.fillRect(r / 2, -1, r / 2, 2);
                    arm.dispose();
                }
                break;
            case 3:
                for (int k = 0; k < 4; k++) {
                    double a = k * Math.PI / 2;
                    java.awt.Polygon tri = new java.awt.Polygon();
                    tri.addPoint((int) (Math.cos(a) * r * .25), (int) (Math.sin(a) * r * .25));
                    tri.addPoint((int) (Math.cos(a + .35) * r * .95), (int) (Math.sin(a + .35) * r * .95));
                    tri.addPoint((int) (Math.cos(a - .35) * r * .95), (int) (Math.sin(a - .35) * r * .95));
                    ball.fillPolygon(tri);
                }
                break;
            case 4:
                ball.setStroke(new BasicStroke(Math.max(1f, r * .18f)));
                ball.drawOval(-r / 2, -r / 2, r, r);
                ball.drawLine(-r, 0, -r / 2, 0);
                ball.drawLine(r / 2, 0, r, 0);
                break;
            case 5:
                ball.setStroke(new BasicStroke(Math.max(1f, r * .20f)));
                ball.drawArc(-r, -r, r * 2, r * 2, 30, 70);
                ball.drawArc(-r, -r, r * 2, r * 2, 210, 70);
                ball.drawArc(-r / 2, -r / 2, r, r, 120, 60);
                break;
            case 6:
                ball.setStroke(new BasicStroke(Math.max(1.2f, r * .26f)));
                ball.drawArc(-r, -r / 3, r * 2, r * 2, 30, 120);
                ball.drawArc(-r, -r * 5 / 3, r * 2, r * 2, 210, 120);
                break;
            case 7:
                for (int k = 0; k < 4; k++) {
                    double a = k * Math.PI / 2 + .4;
                    ball.fillRect((int) (Math.cos(a) * r * .55) - r / 5, (int) (Math.sin(a) * r * .55) - 1, r * 2 / 5, 3);
                }
                break;
            case 8:
                for (int k = 0; k < 6; k++) {
                    double a = k * Math.PI / 3;
                    ball.fillOval((int) (Math.cos(a) * r * .62) - 1, (int) (Math.sin(a) * r * .62) - 1, 3, 3);
                }
                ball.fillOval(-2, -2, 4, 4);
                break;
            case 9:
                for (int k = 0; k < 3; k++) {
                    double a = k * Math.PI * 2 / 3;
                    ball.fillPolygon(star(Math.cos(a) * r * .55, Math.sin(a) * r * .55, r * .35));
                }
                break;
            case 10:
                ball.setStroke(new BasicStroke(Math.max(1f, r * .18f)));
                ball.drawLine(-r, -r / 3, r, -r / 3);
                ball.drawLine(-r, r / 3, r, r / 3);
                break;
            default:
                ball.fillArc(-r, -r, r * 2, r * 2, 20, 50);
                ball.fillArc(-r, -r, r * 2, r * 2, 200, 50);
                break;
        }
        ball.dispose();
        g.setColor(new Color(0, 0, 0, 170));
        g.drawOval(cx - radius, cy - radius, radius * 2, radius * 2);
        g.setColor(new Color(255, 255, 255, 140));
        g.fillOval(cx - radius / 2, cy - radius * 3 / 4, Math.max(2, radius / 2), Math.max(2, radius / 3));
    }

    private java.awt.Polygon star(double cx, double cy, double size) {
        java.awt.Polygon polygon = new java.awt.Polygon();
        for (int k = 0; k < 10; k++) {
            double a = -Math.PI / 2 + k * Math.PI / 5;
            double rr = k % 2 == 0 ? size : size * .45;
            polygon.addPoint((int) Math.round(cx + Math.cos(a) * rr), (int) Math.round(cy + Math.sin(a) * rr));
        }
        return polygon;
    }

    private java.awt.Polygon pentagon(double cx, double cy, double size) {
        java.awt.Polygon polygon = new java.awt.Polygon();
        for (int k = 0; k < 5; k++) {
            double a = -Math.PI / 2 + k * Math.PI * 2 / 5;
            polygon.addPoint((int) Math.round(cx + Math.cos(a) * size), (int) Math.round(cy + Math.sin(a) * size));
        }
        return polygon;
    }

    private void drawPenaltyArea(Graphics2D g, int left, int top, int width, int height, boolean rightSide) {
        int largeW = Math.max(80, width / 7), largeH = height / 2;
        int smallW = Math.max(32, width / 22), smallH = height / 4;
        int y1 = top + (height - largeH) / 2;
        int y2 = top + (height - smallH) / 2;
        int x1 = rightSide ? left + width - largeW : left;
        int x2 = rightSide ? left + width - smallW : left;
        g.drawRect(x1, y1, largeW, largeH);
        g.drawRect(x2, y2, smallW, smallH);
        int goalX = rightSide ? left + width : left - 8;
        g.drawRect(goalX, top + height / 2 - height / 10, 8, height / 5);
    }

    private void drawTeam(Graphics2D g, Dot[] team, Color kitFill, Color kitAccent, Color stripe, Color keeper,
                          int left, int top, int width, int height, long now) {
        g.setFont(NAME_FONT);
        FontMetrics metrics = g.getFontMetrics();
        int side = team == away ? 1 : 0;
        for (int i = 0; i < team.length; i++) {
            Dot dot = team[i];
            if (!dot.active) continue;
            int x = left + (int) (viewX(dot.currentX) * width);
            int y = top + (int) (dot.currentY * height);
            int fade = dot.entering ? 110 : 255;
            if (dot.fadeStart > 0) {
                long age = System.currentTimeMillis() - dot.fadeStart;
                if (age < 450) fade = (int) Math.max(20, 255 * age / 450);
                else dot.fadeStart = 0;
            }
            Color fill = i == 0 ? keeper : kitFill;
            Color accent = i == 0 ? contrastRing(keeper) : kitAccent;
            g.setColor(SHADOW);
            if (!dot.entering && fade == 255) g.fillOval(x - 9, y - 7, 20, 20);
            g.setColor(new Color(fill.getRed(), fill.getGreen(), fill.getBlue(), fade));
            g.fillOval(x - 10, y - 10, 20, 20);
            if (i != 0 && stripe != null) {
                java.awt.Shape clip = g.getClip();
                g.clip(new java.awt.geom.Ellipse2D.Double(x - 10, y - 10, 20, 20));
                g.setColor(new Color(stripe.getRed(), stripe.getGreen(), stripe.getBlue(), fade));
                for (int sx = x - 9; sx < x + 10; sx += 6) g.fillRect(sx, y - 10, 3, 20);
                g.setClip(clip);
            }
            g.setColor(new Color(255, 255, 255, dot.entering ? 35 : 70));
            g.fillOval(x - 7, y - 8, 9, 6);
            g.setColor(new Color(accent.getRed(), accent.getGreen(), accent.getBlue(), fade));
            g.setStroke(STROKE_2);
            g.drawOval(x - 10, y - 10, 20, 20);
            String key = playerKey(side, dot.fullName);
            if (injured.contains(key)) {
                g.setColor(Color.WHITE);
                g.fillOval(x + 4, y + 3, 11, 11);
                g.setColor(CARD_EDGE);
                g.drawOval(x + 4, y + 3, 11, 11);
                g.setColor(CARD_RED);
                g.fillRect(x + 8, y + 5, 3, 7);
                g.fillRect(x + 6, y + 7, 7, 3);
            }
            if (yellowCarded.contains(key) || redCarded.contains(key)) {
                g.setColor(redCarded.contains(key) ? CARD_RED : CARD_YELLOW);
                g.fillRoundRect(x + 8, y - 13, 6, 10, 2, 2);
                g.setColor(CARD_EDGE);
                g.drawRoundRect(x + 8, y - 13, 6, 10, 2, 2);
            }
            boolean focus = inFocus(side, i, dot);
            g.setFont(focus ? NAME_FONT : NAME_FONT_LIGHT);
            FontMetrics fm = g.getFontMetrics();
            int textW = fm.stringWidth(dot.name);
            int tx = x - textW / 2;
            int ty = y - 13;
            if (focus) {
                g.setColor(new Color(0, 0, 0, 90));
                g.fillRoundRect(tx - 4, ty - fm.getAscent(), textW + 8, fm.getHeight(), 10, 10);
                g.setColor(Color.WHITE);
            } else {
                g.setColor(new Color(0, 0, 0, 120));
                g.drawString(dot.name, tx + 1, ty + 1);
                g.setColor(new Color(255, 255, 255, dot.entering ? 110 : 190));
            }
            g.drawString(dot.name, tx, ty);
        }
    }

    private String playerKey(int side, String name) {
        return side + ":" + normalizedName(name);
    }

    private void drawEventBar(Graphics2D g, int width, int y) {
        g.setColor(EVENT_BACK);
        g.fillRoundRect(10, y, width - 20, 29, 10, 10);
        g.setFont(EVENT_FONT);
        g.setColor(EVENT_TITLE);
        String title = homeName + "  " + visibleScore + "  " + awayName;
        g.drawString(title, 22, y + 20);
        String info = (minute.length() == 0 ? "" : minute + "  •  ") + event;
        FontMetrics fm = g.getFontMetrics();
        int max = width - fm.stringWidth(title) - 62;
        while (fm.stringWidth(info) > max && info.length() > 8) info = info.substring(0, info.length() - 2);
        if (!info.equals(event) && info.length() > 3) info += "…";
        g.setColor(Color.WHITE);
        g.drawString(info, width - 22 - fm.stringWidth(info), y + 20);
    }

    private void drawOtherMatches(Graphics2D g, int width, int height, int y) {
        BufferedImage matches = otherMatchesImage;
        if (matches == null) return;
        int sourceWidth = matches.getWidth();
        int sourceHeight = matches.getHeight();
        int availableWidth = width - 20;
        int availableHeight = height - y - 8;
        if (sourceWidth <= 0 || sourceHeight <= 0 || availableHeight <= 0) return;
        double scale = availableWidth / (double) sourceWidth;
        otherMatchesScale = scale;
        otherMatchesArea = new Rectangle(10, y, availableWidth,
                Math.min(availableHeight, (int) Math.ceil(sourceHeight * scale)));
        Graphics2D copy = (Graphics2D) g.create(10, y, availableWidth, availableHeight);
        copy.scale(scale, scale);
        copy.drawImage(matches, 0, 0, null);
        copy.dispose();
    }

    private void captureOtherMatches() {
        try {
            Object value = readField(host, "ut");
            if (!(value instanceof Component)) value = readField(host, "Hs");
            if (!(value instanceof Component)) value = readField(host, "Hq");
            if (!(value instanceof Component)) return;
            Component matches = (Component) value;
            int width = matches.getWidth();
            int height = Math.min(420, matches.getHeight());
            if (width <= 0 || height <= 0) return;
            BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
            Graphics2D graphics = image.createGraphics();
            graphics.setClip(0, 0, width, height);
            matches.printAll(graphics);
            graphics.dispose();
            otherMatchesImage = image;
            otherMatchesSource = matches;
        } catch (Throwable ignored) {
        }
    }

    private static final Color PITCH_GREEN = new Color(46, 125, 50);
    private static final Color KIT_DARK = new Color(18, 24, 31);
    private static final Color[] KEEPER_PALETTE = {
        new Color(57, 255, 20), new Color(255, 140, 0), new Color(214, 38, 160), new Color(0, 200, 230),
        new Color(250, 225, 0), new Color(28, 28, 28), new Color(124, 64, 214), new Color(255, 92, 92)
    };
    private static final double KIT_CLASH = 42;

    private void chooseKits(Object homeTeam, Object awayTeam) {
        Color[] homeKit = kitOptions(homeTeam).get(0);
        Color[] awayKit = null;
        double bestGap = -1;
        for (Color[] option : kitOptions(awayTeam)) {
            double gap = kitGap(homeKit, option);
            if (gap >= KIT_CLASH) {
                awayKit = option;
                break;
            }
            if (gap > bestGap) {
                bestGap = gap;
                awayKit = option;
            }
        }
        homeColor = homeKit[0];
        homeStripe = homeKit[2];
        homeAccent = kitRing(homeKit);
        awayColor = awayKit[0];
        awayStripe = awayKit[2];
        awayAccent = kitRing(awayKit);
        homeKeeper = keeperColor(homeKit, awayKit, null);
        awayKeeper = keeperColor(homeKit, awayKit, homeKeeper);
    }

    private List<Color[]> kitOptions(Object team) {
        List<Color[]> options = new ArrayList<Color[]>();
        Color primary = parseColor(readField(team, "cor1"), null);
        Color secondary = parseColor(readField(team, "cor2"), null);
        for (int kit = 1; kit <= 3; kit++) {
            Object value = invokeInt(team, "bU", kit);
            Color[] sampled = value instanceof ImageIcon ? sampleKit((ImageIcon) value) : null;
            if (sampled != null) options.add(anchorKit(sampled, primary, secondary));
        }
        if (primary != null) options.add(new Color[] { polish(primary), secondary == null ? null : polish(secondary), null });
        if (secondary != null) options.add(new Color[] { polish(secondary), primary == null ? null : polish(primary), null });
        if (options.isEmpty()) options.add(new Color[] { new Color(43, 137, 214), Color.WHITE, null });
        return options;
    }

    private Color[] sampleKit(ImageIcon icon) {
        int width = icon.getIconWidth(), height = icon.getIconHeight();
        if (width <= 0 || height <= 0) return null;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = image.createGraphics();
        graphics.drawImage(icon.getImage(), 0, 0, null);
        graphics.dispose();
        int[] counts = new int[512];
        long[] sums = new long[512 * 3];
        int total = 0;
        for (int y = (int) (height * .30); y < (int) (height * .88); y++) {
            for (int x = (int) (width * .28); x < (int) (width * .72); x++) {
                int pixel = image.getRGB(x, y);
                if ((pixel >>> 24) < 200) continue;
                int r = (pixel >> 16) & 255, gr = (pixel >> 8) & 255, b = pixel & 255;
                int bucket = (r >> 5) << 6 | (gr >> 5) << 3 | (b >> 5);
                counts[bucket]++;
                sums[bucket * 3] += r;
                sums[bucket * 3 + 1] += gr;
                sums[bucket * 3 + 2] += b;
                total++;
            }
        }
        if (total < 20) return null;
        Integer[] order = new Integer[512];
        for (int i = 0; i < 512; i++) order[i] = Integer.valueOf(i);
        final int[] weights = counts;
        java.util.Arrays.sort(order, new Comparator<Integer>() {
            @Override public int compare(Integer a, Integer b) { return weights[b.intValue()] - weights[a.intValue()]; }
        });
        int first = order[0].intValue();
        Color primary = bucketColor(sums, counts, first);
        int primaryCount = counts[first];
        Color second = null;
        int secondCount = 0;
        for (int i = 1; i < 512 && counts[order[i].intValue()] > 0; i++) {
            int bucket = order[i].intValue();
            Color candidate = bucketColor(sums, counts, bucket);
            if (colorGap(candidate, primary) < 70) {
                primaryCount += counts[bucket];
                continue;
            }
            if (second == null) {
                second = candidate;
                secondCount = counts[bucket];
            } else if (colorGap(candidate, second) < 70) {
                secondCount += counts[bucket];
            }
        }
        boolean striped = second != null && secondCount >= total * .25 && primaryCount >= total * .25;
        boolean detail = second != null && secondCount >= total * .06;
        return new Color[] { polish(primary), detail ? polish(second) : null, striped ? polish(second) : null };
    }

    private Color[] anchorKit(Color[] kit, Color official, Color officialSecond) {
        Color[] result = kit.clone();
        Color[] palette = { official, officialSecond };
        for (int i = 0; i < 3; i += 2) {
            if (result[i] == null) continue;
            for (Color candidate : palette) {
                if (candidate != null && labGap(polish(candidate), result[i]) < 28) {
                    result[i] = polish(candidate);
                    break;
                }
            }
        }
        if (result[2] == null) {
            Color ring = null;
            double best = 30;
            for (Color candidate : palette) {
                if (candidate == null) continue;
                double gap = labGap(polish(candidate), result[0]);
                if (gap > best) {
                    best = gap;
                    ring = polish(candidate);
                }
            }
            if (ring != null) result[1] = ring;
        }
        return result;
    }

    private Color bucketColor(long[] sums, int[] counts, int bucket) {
        return new Color((int) (sums[bucket * 3] / counts[bucket]), (int) (sums[bucket * 3 + 1] / counts[bucket]),
                (int) (sums[bucket * 3 + 2] / counts[bucket]));
    }

    private Color polish(Color color) {
        float[] hsb = Color.RGBtoHSB(color.getRed(), color.getGreen(), color.getBlue(), null);
        float saturation = hsb[1], brightness = hsb[2];
        if (saturation > .25f) {
            saturation = Math.min(1f, saturation * 1.12f);
            brightness = Math.max(.50f, brightness);
        } else if (brightness >= .45f) {
            brightness = Math.max(.95f, brightness);
            saturation = Math.min(saturation, .06f);
        } else {
            brightness = Math.min(.16f, brightness);
        }
        return Color.getHSBColor(hsb[0], saturation, brightness);
    }

    private double kitGap(Color[] a, Color[] b) {
        double gap = labGap(a[0], b[0]);
        if (a[2] != null) gap = Math.min(gap, (labGap(a[0], b[0]) + labGap(a[2], b[0])) / 2);
        if (b[2] != null) gap = Math.min(gap, (labGap(a[0], b[0]) + labGap(a[0], b[2])) / 2);
        return gap;
    }

    private double[] lab(Color color) {
        double[] rgb = { color.getRed() / 255.0, color.getGreen() / 255.0, color.getBlue() / 255.0 };
        for (int i = 0; i < 3; i++) rgb[i] = rgb[i] > .04045 ? Math.pow((rgb[i] + .055) / 1.055, 2.4) : rgb[i] / 12.92;
        double x = (rgb[0] * .4124 + rgb[1] * .3576 + rgb[2] * .1805) / .95047;
        double y = rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
        double z = (rgb[0] * .0193 + rgb[1] * .1192 + rgb[2] * .9505) / 1.08883;
        double fx = x > .008856 ? Math.cbrt(x) : 7.787 * x + 16 / 116.0;
        double fy = y > .008856 ? Math.cbrt(y) : 7.787 * y + 16 / 116.0;
        double fz = z > .008856 ? Math.cbrt(z) : 7.787 * z + 16 / 116.0;
        return new double[] { 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz) };
    }

    private double labGap(Color a, Color b) {
        double[] p = lab(a), q = lab(b);
        double dl = p[0] - q[0], da = p[1] - q[1], db = p[2] - q[2];
        return Math.sqrt(dl * dl + da * da + db * db);
    }

    private double luminance(Color color) {
        return color.getRed() * .2126 + color.getGreen() * .7152 + color.getBlue() * .0722;
    }

    private Color contrastRing(Color fill) {
        return luminance(fill) < 140 ? Color.WHITE : KIT_DARK;
    }

    private Color kitRing(Color[] kit) {
        if (kit[2] != null) return luminance(kit[0]) + luminance(kit[2]) < 200 ? Color.WHITE : KIT_DARK;
        Color ring = kit[1];
        if (ring == null || labGap(ring, kit[0]) < 30 || labGap(ring, PITCH_GREEN) < 30) ring = contrastRing(kit[0]);
        return ring;
    }

    private Color keeperColor(Color[] homeKit, Color[] awayKit, Color other) {
        Color best = KEEPER_PALETTE[0];
        double bestScore = -1;
        for (Color candidate : KEEPER_PALETTE) {
            double score = Math.min(kitGap(homeKit, new Color[] { candidate, null, null }),
                    kitGap(awayKit, new Color[] { candidate, null, null }));
            score = Math.min(score, labGap(candidate, PITCH_GREEN) * 1.4);
            if (other != null) score = Math.min(score, labGap(candidate, other));
            if (score > bestScore) {
                bestScore = score;
                best = candidate;
            }
        }
        return best;
    }

    private Color parseColor(Object value, Color fallback) {
        try {
            String text = String.valueOf(value);
            return Color.decode(text.startsWith("#") ? text : "#" + text);
        } catch (Throwable ignored) { return fallback; }
    }

    private String labelText(Object owner, String field, String fallback) {
        Object value = readField(owner, field);
        return value instanceof JLabel ? string(((JLabel) value).getText(), fallback) : fallback;
    }

    private void collectText(Component component, List<String> output) {
        if (component instanceof JLabel) {
            String text = ((JLabel) component).getText();
            if (text != null) output.add(text);
        } else if (component instanceof JTable) collectTable((JTable) component, output);
        if (component instanceof JScrollPane) {
            Component view = ((JScrollPane) component).getViewport().getView();
            if (view != null) collectText(view, output);
        } else if (component instanceof Container) {
            for (Component child : ((Container) component).getComponents()) collectText(child, output);
        }
    }

    private void collectTable(JTable table, List<String> output) {
        TableModel model = table.getModel();
        int first = Math.max(0, model.getRowCount() - 8);
        for (int row = first; row < model.getRowCount(); row++) {
            StringBuilder text = new StringBuilder();
            for (int col = 0; col < model.getColumnCount(); col++) {
                Object value = model.getValueAt(row, col);
                if (value != null && String.valueOf(value).trim().length() > 0) {
                    if (text.length() > 0) text.append(' ');
                    text.append(value);
                }
            }
            if (text.length() > 0) output.add(text.toString());
        }
    }

    private List<String> cleanLog(List<String> raw) {
        List<String> result = new ArrayList<String>();
        for (String item : raw) {
            String text = item.replaceAll("<[^>]+>", " ").replaceAll("\\s+", " ").trim();
            if (text.length() >= 4 && !result.contains(text)) result.add(text);
        }
        return result;
    }

    private String newestEntry(List<String> oldItems, List<String> newItems) {
        for (int i = newItems.size() - 1; i >= 0; i--) {
            String item = newItems.get(i);
            if (!oldItems.contains(item)) return item;
        }
        return newItems.isEmpty() ? null : newItems.get(newItems.size() - 1);
    }

    private static Object readField(Object owner, String name) {
        if (owner == null) return null;
        Class<?> type = owner.getClass();
        while (type != null) {
            try {
                Field field = type.getDeclaredField(name);
                field.setAccessible(true);
                return field.get(owner);
            } catch (Throwable ignored) { type = type.getSuperclass(); }
        }
        return null;
    }

    private static Object invoke(Object owner, String name) {
        if (owner == null) return null;
        try {
            Method method = owner.getClass().getMethod(name);
            method.setAccessible(true);
            return method.invoke(owner);
        } catch (Throwable ignored) { return null; }
    }

    private static Object invokeInt(Object owner, String name, int value) {
        if (owner == null) return null;
        try {
            Method method = owner.getClass().getMethod(name, int.class);
            method.setAccessible(true);
            return method.invoke(owner, Integer.valueOf(value));
        } catch (Throwable ignored) { return null; }
    }

    private static String string(Object value, String fallback) {
        if (value == null) return fallback;
        String text = String.valueOf(value).trim();
        return text.length() == 0 ? fallback : text;
    }

    private final List<Ghost> ghosts = new ArrayList<Ghost>();

    private static final class Ghost {
        double x;
        double y;
        int side;
        String name;
        String key;
    }

    private static final class Dot {
        double x;
        double y;
        double currentX;
        double currentY;
        double targetX;
        double targetY;
        double velocityX;
        double velocityY;
        double wanderX;
        double wanderY;
        int nextWanderFrame;
        int nextRunCheck;
        int runUntil;
        double runY = .5;
        int roleLine;
        boolean wideRole;
        boolean active = true;
        boolean known;
        boolean entering;
        long fadeStart;
        String name;
        String fullName;
        final boolean away;
        final Random random;
        Dot(double x, double y, String name, boolean away) {
            this.x = x; this.y = y;
            this.currentX = this.targetX = x;
            this.currentY = this.targetY = y;
            this.name = name; this.away = away;
            this.fullName = name;
            this.random = new Random(name.hashCode() * 31L + (away ? 1L : 0L));
            this.roleLine = x < .12 || x > .88 ? 0 : x < .27 || x > .73 ? 1
                    : x < .41 || x > .59 ? 2 : 3;
            this.wideRole = y <= .27 || y >= .73;
        }
    }
}
