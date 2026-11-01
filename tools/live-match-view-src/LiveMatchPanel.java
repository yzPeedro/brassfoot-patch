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
import java.util.List;
import java.util.Locale;
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
    private boolean decisionPause;
    private long decisionPauseStarted;
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
    private int frames;
    private boolean everShown;

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
        MouseAdapter forwarder = new MouseAdapter() {
            @Override public void mousePressed(MouseEvent event) { forwardMouse(event); }
            @Override public void mouseReleased(MouseEvent event) { forwardMouse(event); }
            @Override public void mouseClicked(MouseEvent event) { forwardMouse(event); }
        };
        addMouseListener(forwarder);
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
        if (matchEnded()) return;
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
        }
        if (preEventMinute == next && preEventHalf == half) return;
        Object value = invoke(match, "hE");
        if (!(value instanceof List<?>)) return;
        List<Object> visual = new ArrayList<Object>();
        for (Object candidate : (List<?>) value) {
            if (Boolean.TRUE.equals(invoke(candidate, "isDone"))) continue;
            if (integer(invoke(candidate, "em"), -1) != next || integer(invoke(candidate, "en"), -1) != half) continue;
            int type = integer(invoke(candidate, "b"), -1);
            if (type != 1 && type != 2 && type != 3 && type != 4 && type != 5 && type != 7) continue;
            String key = engineActionKey(candidate);
            if (key == null || animatedKeys.contains(key)) continue;
            visual.add(candidate);
        }
        preEventMinute = next;
        preEventHalf = half;
        if (visual.isEmpty()) return;
        preEventActive = true;
        preEventRemaining = visual.size();
        preEventDeadline = Long.MAX_VALUE;
        preEventStarted = now;
        for (Object action : visual) {
            animatedKeys.add(engineActionKey(action));
            queuedEngineActions.add(action);
        }
        holdGameClock();
    }

    private void onClimax() {
        if (!preEventActive) return;
        preEventRemaining--;
        if (preEventRemaining <= 0) fireEngineMinute();
    }

    private void fireEngineMinute() {
        preEventActive = false;
        preEventRemaining = 0;
        if (matchEnded() || Boolean.FALSE.equals(readField(host, "GZ"))) return;
        Object clock = readField(host, "GO");
        if (clock instanceof Timer) ((Timer) clock).stop();
        clockHeld = false;
        try {
            Method step = host.getClass().getMethod("qa");
            step.invoke(host);
        } catch (Throwable error) {
            diagnostic("fire_minute_failed", error);
            if (clock instanceof Timer) ((Timer) clock).restart();
        }
        score = labelText(host, "Hn", labelText(host, "Lm", score));
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
                LiveMatchPanel panel = new LiveMatchPanel(host);
                Class<?> constraintType = Class.forName("components.a");
                Constructor<?> constructor = constraintType.getDeclaredConstructor(
                        int.class, int.class, int.class, int.class);
                constructor.setAccessible(true);
                Object constraint = constructor.newInstance(15, 165, 994, 480);
                host.add(panel, constraint);
                host.setComponentZOrder(panel, 0);
                host.revalidate();
                host.repaint();
                diagnostic("panel_added parent=" + panel.getParent().getClass().getName()
                        + " bounds=" + panel.getBounds(), null);
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
        ensureVisibleLayer();
        long nanos = System.nanoTime();
        if (lastTickNanos != 0) frameSeconds = clamp((nanos - lastTickNanos) / 1e9, .004, .05);
        lastTickNanos = nanos;
        frames++;
        if (frames % 8 == 0) syncFromGame();
        if (isDecisionDialogOpen()) {
            if (!decisionPause) {
                decisionPause = true;
                decisionPauseStarted = System.currentTimeMillis();
            }
            repaint();
            return;
        } else if (decisionPause) {
            decisionPause = false;
            shiftAnimationDeadlines(System.currentTimeMillis() - decisionPauseStarted);
        }
        long now = System.currentTimeMillis();
        updatePreSimulation(now);
        if (preEventActive && (now >= preEventDeadline || now - preEventStarted > 40000L)) fireEngineMinute();
        if (hasClockStoppage()) {
            if (pauseRequested() && !preEventActive) releaseGameClock();
            else holdGameClock();
        } else {
            releaseGameClock();
        }
        if (frames % 30 == 0) captureOtherMatches();
        if (frames % 12 == 0) updatePlayerTargets();
        else refreshBallRoleTargets();
        updatePlayerPositions();
        if (!hasAnimationStoppage() && !queuedEngineActions.isEmpty()) {
            if (preEventActive && preEventDeadline == Long.MAX_VALUE) preEventDeadline = now + 16000L;
            applyEngineAction(queuedEngineActions.remove(0));
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
        if (ballInFlight) {
            double t = Math.min(1.0, (now - moveStarted) / (double) moveDuration);
            double eased = t * t * (3.0 - 2.0 * t);
            ballX = ballFromX + (ballToX - ballFromX) * eased;
            ballY = ballFromY + (ballToY - ballFromY) * eased;
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
        if (pendingGoalStage == 2) {
            looseBall = false;
            pendingGoalStage = 0;
            onClimax();
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
            int control = 360 + random.nextInt(520);
            if (random.nextInt(5) == 0) control += 700 + random.nextInt(650);
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
            looseSince = System.currentTimeMillis();
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
            possessingSide = tackleSide;
            possessingPlayer = tackler;
            possessionPasses = 0;
            controlUntil = now + 420L + random.nextInt(260);
            return;
        }
        if (now >= tackleDeadline) {
            tackleActive = false;
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
        if (engineMinute > 2 || engineHalf != 1) {
            openingKickoffDone = true;
            return;
        }
        if (!engineRunning()) return;
        openingKickoffDone = true;
        event = "Saída de bola";
        beginKickoffReset(now, 0);
        restartEarliest = now + 900L;
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

    private void shiftAnimationDeadlines(long delta) {
        if (delta <= 0) return;
        moveStarted += delta;
        if (controlUntil > 0 && controlUntil < Long.MAX_VALUE) controlUntil += delta;
        if (simpleStoppageUntil > 0) simpleStoppageUntil += delta;
        if (restartEarliest > 0) restartEarliest += delta;
        if (restartDeadline > 0) restartDeadline += delta;
        if (penaltyReadyAfter > 0) penaltyReadyAfter += delta;
        if (penaltyDeadline > 0) penaltyDeadline += delta;
        if (freeKickReadyAfter > 0) freeKickReadyAfter += delta;
        if (freeKickDeadline > 0) freeKickDeadline += delta;
        if (cardFoulReadyAfter > 0) cardFoulReadyAfter += delta;
        if (cardFoulDeadline > 0) cardFoulDeadline += delta;
        if (tackleDeadline > 0) tackleDeadline += delta;
        if (kickoffDeadline > 0) kickoffDeadline += delta;
        if (goalStageDeadline > 0) goalStageDeadline += delta;
        if (looseSince > 0) looseSince += delta;
    }

    private void followBallCarrier() {
        if (restartActive || looseBall || ballInFlight) return;
        Dot[] side = possessingSide == 0 ? home : away;
        int player = Math.max(0, Math.min(side.length - 1, possessingPlayer));
        Dot carrier = side[player];
        if (!carrier.active) return;
        double speed = Math.sqrt(carrier.velocityX * carrier.velocityX + carrier.velocityY * carrier.velocityY);
        double dirX;
        double dirY;
        if (speed > .004) {
            dirX = carrier.velocityX / speed;
            dirY = carrier.velocityY / speed;
        } else {
            dirX = possessingSide == 0 ? 1.0 : -1.0;
            dirY = 0;
        }
        double footX = carrier.currentX + dirX * BALL_FOOT;
        double footY = carrier.currentY + dirY * BALL_FOOT;
        if (distance(carrier.currentX, carrier.currentY, ballX, ballY) > CONTACT * 1.5) {
            looseBall = true;
            looseSide = possessingSide;
            looseChaser = player;
            looseSince = System.currentTimeMillis();
            return;
        }
        ballX += (footX - ballX) * .45;
        ballY += (footY - ballY) * .45;
        ballFromX = ballToX = ballX;
        ballFromY = ballToY = ballY;
    }

    private void ensureVisibleLayer() {
        if (!firstLayerCheck) {
            firstLayerCheck = true;
            diagnostic("layer_check showing=" + host.isShowing()
                    + " root=" + (host.getRootPane() == null ? "null" : "present")
                    + " hostBounds=" + host.getBounds(), null);
        }
        if (!host.isShowing() || host.getRootPane() == null) {
            setVisible(false);
            if (everShown) {
                timer.stop();
                if (getParent() != null) getParent().remove(this);
                diagnostic("panel_stopped host_no_longer_showing", null);
            }
            return;
        }
        everShown = true;
        JLayeredPane layer = host.getRootPane().getLayeredPane();
        int panelY = 165;
        int panelHeight = Math.max(520, host.getHeight() - panelY - 10);
        Point origin = SwingUtilities.convertPoint(host, 15, panelY, layer);
        if (getParent() != layer) {
            if (getParent() != null) getParent().remove(this);
            layer.add(this, JLayeredPane.PALETTE_LAYER);
        }
        setBounds(origin.x, origin.y, 994, panelHeight);
        layer.setLayer(this, JLayeredPane.PALETTE_LAYER.intValue());
        layer.moveToFront(this);
        setVisible(true);
        if (!attachedLogged) {
            attachedLogged = true;
            diagnostic("layer_visible bounds=" + getBounds() + " layerSize="
                    + layer.getWidth() + "x" + layer.getHeight(), null);
        }
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
        boolean timeUp = now >= goalStageDeadline;
        boolean assistReady = plannedAssist >= 0 && possessingPlayer == plannedAssist;
        boolean finalPass = timeUp || goalBuildPasses >= goalBuildTarget && (progress >= .45 || assistReady)
                || progress >= .66;
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

    private void holdGameClock() {
        Object value = readField(host, "GO");
        if (value instanceof Timer && ((Timer) value).isRunning()) {
            ((Timer) value).stop();
            clockHeld = true;
        }
    }

    private void releaseGameClock() {
        if (!clockHeld) return;
        clockHeld = false;
        Object value = readField(host, "GO");
        if (!(value instanceof Timer) || matchEnded()) return;
        if (Boolean.FALSE.equals(readField(host, "GZ"))) return;
        ((Timer) value).restart();
    }

    private void startPenalty(long now, int side, int actor, boolean goal) {
        holdGameClock();
        resetBallControl();
        plannedRoute.clear();
        plannedActionKey = null;
        penaltyPhase = 1;
        penaltySide = side;
        penaltyActor = actor;
        penaltyOutcome = goal ? 0 : 1 + random.nextInt(3);
        penaltyShotY = penaltyOutcome == 2 ? (random.nextBoolean() ? .385 : .615)
                : penaltyOutcome == 3 ? (random.nextBoolean() ? .27 : .73)
                : .42 + random.nextDouble() * .16;
        penaltyReadyAfter = now + 1100L;
        penaltyDeadline = now + 5200L;
        possessingSide = side;
        possessingPlayer = actor;
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = side == 0 ? .885 : .115;
        ballToY = .50;
        moveStarted = now;
        moveDuration = 650;
        ballInFlight = true;
    }

    private void updatePenalty(long now) {
        if (penaltyPhase == 1 && !ballInFlight && now >= penaltyReadyAfter
                && (formationReady() || now >= penaltyDeadline)) {
            penaltyPhase = 2;
            controlUntil = Long.MAX_VALUE;
        } else if (penaltyPhase == 2 && !ballInFlight) {
            Dot[] shooting = penaltySide == 0 ? home : away;
            Dot actor = shooting[Math.min(shooting.length - 1, penaltyActor)];
            if (distance(actor.currentX, actor.currentY, ballX, ballY) > .022) return;
            penaltyPhase = 3;
            possessingSide = penaltySide;
            possessingPlayer = penaltyActor;
            ballFromX = ballX;
            ballFromY = ballY;
            ballToX = penaltySide == 0 ? (penaltyOutcome == 3 ? 1.018
                    : penaltyOutcome == 1 ? .955 : .985)
                    : (penaltyOutcome == 3 ? -.018 : penaltyOutcome == 1 ? .045 : .015);
            ballToY = penaltyShotY;
            moveStarted = now;
            moveDuration = penaltyOutcome == 1 ? 650 : 760;
            ballInFlight = true;
            if (penaltyOutcome == 1) {
                Dot keeper = penaltySide == 0 ? away[0] : home[0];
                event = "Defesa do goleiro: " + keeper.name;
            } else if (penaltyOutcome == 2) {
                event = "Pênalti na trave!";
            } else if (penaltyOutcome == 3) {
                event = "Pênalti para fora!";
            }
        } else if (penaltyPhase == 4 && now >= controlUntil) {
            int defendingSide = 1 - penaltySide;
            penaltyPhase = 0;
            recoverToKeeper(now, defendingSide);
        }
    }

    private void handlePenaltyArrival(long now) {
        if (penaltyPhase == 1) {
            ballFromX = ballToX = ballX = penaltySide == 0 ? .885 : .115;
            ballFromY = ballToY = ballY = .50;
            controlUntil = Long.MAX_VALUE;
        } else if (penaltyPhase == 3) {
            onClimax();
            if (penaltyOutcome == 0) {
                penaltyPhase = 0;
                beginGoalRestart(now, penaltySide);
            } else {
                penaltyPhase = 4;
                controlUntil = now + 600L;
            }
        }
    }

    private void startFreeKick(long now, int side, int actor) {
        holdGameClock();
        resetBallControl();
        plannedRoute.clear();
        plannedActionKey = null;
        plannedSide = side;
        plannedActor = actor;
        plannedType = 1;
        plannedSubtype = 4;
        choosePlannedSpot(1, 4);
        freeKickPhase = 1;
        freeKickSide = side;
        freeKickActor = actor;
        double goalX = side == 0 ? 1.0 : 0.0;
        double distanceToGoal = Math.abs(goalX - plannedSpotX);
        freeKickWall = distanceToGoal < .20 ? 4 : distanceToGoal < .27 ? 3
                : distanceToGoal < .34 ? 2 : 1;
        freeKickReadyAfter = now + 1000L;
        freeKickDeadline = now + 4800L;
        possessingSide = side;
        possessingPlayer = actor;
        ballFromX = ballX;
        ballFromY = ballY;
        ballToX = plannedSpotX;
        ballToY = plannedSpotY;
        moveStarted = now;
        moveDuration = 700;
        ballInFlight = true;
    }

    private void updateFreeKick(long now) {
        if (freeKickPhase == 1 && !ballInFlight && now >= freeKickReadyAfter
                && (formationReady() || now >= freeKickDeadline)) {
            freeKickPhase = 2;
            controlUntil = Long.MAX_VALUE;
        } else if (freeKickPhase == 2 && !ballInFlight) {
            Dot[] shooting = freeKickSide == 0 ? home : away;
            Dot actor = shooting[Math.min(shooting.length - 1, freeKickActor)];
            if (distance(actor.currentX, actor.currentY, ballX, ballY) > .022) return;
            freeKickPhase = 3;
            possessingSide = freeKickSide;
            possessingPlayer = freeKickActor;
            ballFromX = ballX;
            ballFromY = ballY;
            ballToX = freeKickSide == 0 ? .985 : .015;
            ballToY = .41 + random.nextDouble() * .18;
            moveStarted = now;
            moveDuration = 780;
            ballInFlight = true;
        }
    }

    private void handleFreeKickArrival(long now) {
        if (freeKickPhase == 1) {
            ballFromX = ballToX = ballX = plannedSpotX;
            ballFromY = ballToY = ballY = plannedSpotY;
            controlUntil = Long.MAX_VALUE;
        } else if (freeKickPhase == 3) {
            freeKickPhase = 0;
            onClimax();
            beginGoalRestart(now, freeKickSide);
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
        holdGameClock();
        plannedRoute.clear();
        plannedActionKey = null;
        cardFoulPhase = 1;
        cardFoulOffenderSide = offenderSide;
        cardFoulOffender = offender;
        cardFoulEvent = foulEvent;
        cardFoulKey = cardKey;
        cardFoulRed = red;
        cardFoulTaker = -1;
        cardFoulReadyAfter = 0;
        cardFoulDeadline = now + 6000L;
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
            Dot offender = offenders[cardFoulOffender];
            boolean contact = !ballInFlight && possessingSide == takerSide && !looseBall
                    && distance(offender.currentX, offender.currentY, ballX, ballY) <= CONTACT * 1.6;
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
        cardFoulReadyAfter = now + (cardFoulKey == null ? 900L : 1600L);
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
        holdGameClock();
        restartActive = true;
        kickoffInProgress = false;
        tackleActive = false;
        looseBall = false;
        receivingSide = -1;
        receivingPlayer = -1;
        restartStarted = now;
        restartEarliest = now + 3200L;
        restartDeadline = now + 12000L;
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
        for (Dot dot : home) {
            if (dot.active && distance(dot.currentX, dot.currentY, dot.targetX, dot.targetY) > .040) return false;
        }
        for (Dot dot : away) {
            if (dot.active && distance(dot.currentX, dot.currentY, dot.targetX, dot.targetY) > .040) return false;
        }
        return true;
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
        if (possessionPasses > 0 && random.nextInt(18) == 0) {
            queueAmbientPattern(side);
            if (!plannedRoute.isEmpty()) {
                int next = plannedRoute.remove(0).intValue();
                if (next != possessingPlayer) {
                    beginPassTo(possessingSide, next, now, 650 + random.nextInt(420));
                    return;
                }
            }
        }
        Dot current = side[Math.max(0, Math.min(side.length - 1, possessingPlayer))];
        possessionPasses++;
        if (possessionPasses >= 8 + random.nextInt(7)) {
            int desiredSide = random.nextInt(100) < homePossessionTarget ? 0 : 1;
            possessionPasses = 0;
            if (desiredSide != possessingSide) {
                Dot[] other = desiredSide == 0 ? home : away;
                startTackle(now, desiredSide, nearestActive(other, ballX, ballY, -1, false));
                return;
            }
        }
        boolean attackingThird = possessingSide == 0 ? current.currentX >= .74 : current.currentX <= .26;
        int next = attackingThird ? recyclePlayer(side, current, possessingPlayer)
                : nearestProgressivePlayer(side, current, possessingPlayer);
        beginPassTo(possessingSide, next, now, 620 + random.nextInt(480));
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

    private void queueAmbientPattern(Dot[] side) {
        plannedSide = possessingSide;
        plannedRoute.clear();
        int pattern = random.nextInt(3);
        if (pattern == 0) {
            double touchline = random.nextBoolean() ? .04 : .96;
            int thrower = nearestPlayer(side, ballX, touchline, possessingPlayer, -1);
            int receiver = nearestPlayer(side,
                    side[thrower].currentX + (possessingSide == 0 ? .10 : -.10),
                    touchline < .5 ? .24 : .76, thrower, -1);
            addRoute(thrower);
            addRoute(receiver);
        } else if (pattern == 1) {
            addRoute(0);
            int defender = nearestPlayer(side, possessingSide == 0 ? .20 : .80,
                    .35 + random.nextDouble() * .30, 0, -1);
            addRoute(defender);
        } else {
            double cornerX = possessingSide == 0 ? .94 : .06;
            double cornerY = random.nextBoolean() ? .05 : .95;
            int taker = nearestPlayer(side, cornerX, cornerY, possessingPlayer, -1);
            int target = nearestPlayer(side, possessingSide == 0 ? .83 : .17,
                    .38 + random.nextDouble() * .24, taker, -1);
            addRoute(taker);
            addRoute(target);
        }
        possessionPasses = 0;
    }

    private void syncFromGame() {
        try {
            Object match = readField(host, "KS");
            Object liveRow = currentLiveRow();
            if (match == null) match = matchFromLiveRow(liveRow);
            if (match != null) {
                matchRef = match;
                Object homeTeam = invoke(match, "hc");
                Object awayTeam = invoke(match, "hd");
                homeTeamRef = homeTeam;
                awayTeamRef = awayTeam;
                homeTactics = intArray(invoke(homeTeam, "kj"));
                awayTactics = intArray(invoke(awayTeam, "kj"));
                homeName = string(invoke(homeTeam, "getNome"), homeName);
                awayName = string(invoke(awayTeam, "getNome"), awayName);
                updateLineup(home, lineupPlayers(match, "hl", homeTeam), false);
                updateLineup(away, lineupPlayers(match, "hm", awayTeam), true);
                Color[] hc = kitColors(homeTeam, 1, homeColor, homeAccent);
                Color[] ac = kitColors(awayTeam, 2, awayColor, awayAccent);
                homeColor = hc[0]; homeAccent = hc[1];
                awayColor = ac[0]; awayAccent = ac[1];
                int observedMinute = integer(readField(host, "GT"), 0);
                int observedHalf = integer(readField(host, "dB"), 1);
                if (engineStateInitialized && engineHalf == 1 && observedHalf == 2) {
                    event = "Início do 2º tempo";
                    clearSetPieces();
                    beginKickoffReset(System.currentTimeMillis(), 1);
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
            String actionKey = engineActionKey(action);
            if (actionKey != null && !actionKey.equals(previousActionKey) && animatedKeys.contains(actionKey)) {
                previousActionKey = actionKey;
            }
            if (actionKey != null && !actionKey.equals(previousActionKey)) {
                previousActionKey = actionKey;
                int actionType = integer(invoke(action, "b"), -1);
                if (actionType == 6 || actionType == 8) {
                    applyEngineAction(action);
                } else if (hasClockStoppage() || !queuedEngineActions.isEmpty()) {
                    queuedEngineActions.add(action);
                } else {
                    applyEngineAction(action);
                }
            }
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
        return (plannedActionKey != null && (plannedType == 1 || plannedType == 7)
                && plannedMinute - engineMinute <= 1) || pendingGoalStage == 1;
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
    }

    private void applyEngineAction(Object action) {
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
        if (homeActor >= 0 && awayActor < 0) side = 0;
        else if (awayActor >= 0 && homeActor < 0) side = 1;
        Dot[] players = side == 0 ? home : away;
        int actor = side == 0 ? homeActor : awayActor;
        if (actor < 0 && type != 6) actor = findPlayer(secondName, players);
        long now = System.currentTimeMillis();
        String description = cleanEvent(string(invoke(action, "er"), null));
        if (type == 6) {
            event = isUsableEvent(description) ? description
                    : "Substituição: sai " + actorName + " · entra " + secondName;
            return;
        }
        if (type == 8) return;
        boolean cardType = type == 2 || type == 3 || type == 4;
        boolean openPlayGoal = type == 1 && subtype != 3 && subtype != 4;
        if (openPlayGoal) goalEventText = isUsableEvent(description) ? description : "Gol de " + actorName;
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
            if (!event.toLowerCase(Locale.ROOT).contains("pen")) event = "Pênalti: " + event;
            startPenalty(now, side, actor, true);
        } else if (type == 7) {
            event = "Pênalti desperdiçado: " + actorName;
            startPenalty(now, side, actor, false);
        } else if (type == 1 && subtype == 4) {
            if (!event.toLowerCase(Locale.ROOT).contains("falta")) event = "Gol de falta: " + event;
            startFreeKick(now, side, actor);
        } else if (type == 1) {
            holdGameClock();
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
            goalStageDeadline = now + 7000L;
            goalBuildPasses = 0;
            goalBuildTarget = random.nextInt(2);
            goalFinalPassed = false;
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
            holdGameClock();
            simpleStoppageUntil = now + 2200L;
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

    private List<?> lineupPlayers(Object match, String lineupMethod, Object team) {
        Object value = invoke(match, lineupMethod);
        if (value instanceof List<?> && ((List<?>) value).size() >= 7) return (List<?>) value;
        value = invoke(team, "kc");
        return value instanceof List<?> ? (List<?>) value : Collections.emptyList();
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
        int[] slotOf = new int[count];
        boolean[] taken = new boolean[dots.length];
        for (int p = 0; p < count; p++) slotOf[p] = -1;
        slotOf[0] = 0;
        taken[0] = true;
        for (int p = 1; p < count; p++) {
            for (int d = 1; d < dots.length; d++) {
                if (!taken[d] && dots[d].known && names[p].equals(dots[d].fullName)) {
                    slotOf[p] = d;
                    taken[d] = true;
                    break;
                }
            }
        }
        for (int p = 1; p < count; p++) {
            if (slotOf[p] >= 0) continue;
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
                dots[d].active = false;
                if (receivingPlayer == d) receivingPlayer = -1;
            }
        }
        for (int p = 0; p < count; p++) {
            int d = slotOf[p];
            if (d < 0) continue;
            Dot dot = dots[d];
            boolean replaced = dot.known && !names[p].equals(dot.fullName);
            boolean returning = !dot.active;
            dot.fullName = names[p];
            dot.name = shortName(names[p]);
            if (dot.known && (replaced || returning) && d != 0) {
                dot.currentX = .50 + (mirror ? .03 : -.03);
                dot.currentY = .975;
                dot.velocityX = 0;
                dot.velocityY = 0;
            }
            dot.active = true;
            dot.known = names[p].length() > 0;
        }
        int teamSide = mirror ? 1 : 0;
        if (cardFoulPhase == 0) {
            for (int d = 1; d < dots.length; d++) {
                if (dots[d].active && redCarded.contains(playerKey(teamSide, dots[d].fullName))) {
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
        boolean kickoff = engineMinute <= 0;
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
                } else if (sideIndex == plannedSide && i == plannedAssist) {
                    targetX = plannedSpotX - direction * .075;
                    targetY = clamp(plannedSpotY + (plannedSpotY < .5 ? .12 : -.12), .14, .86);
                } else if (sideIndex == plannedSide && plannedType == 1 && dot.roleLine >= 2) {
                    double supportX = plannedSpotX - direction * (.11 + (i % 3) * .045);
                    double supportY = .15 + ((i * 2) % 5) * .175;
                    targetX = targetX * .68 + supportX * .32;
                    targetY = targetY * .72 + supportY * .28;
                } else if (sideIndex != plannedSide && plannedType == 1 && dot.roleLine <= 1 && i > 0) {
                    double boxLine = plannedSide == 0 ? .84 : .16;
                    targetX = targetX * .35 + boxLine * .65;
                    targetY = .16 + (i - 1) % 5 * .17;
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
        if (cardFoulPhase == 1) {
            if (sideIndex == cardFoulOffenderSide && index == cardFoulOffender
                    && possessingSide != cardFoulOffenderSide) {
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
        if (looseBall && side == looseSide && index == looseChaser) return true;
        if (ballInFlight && side == receivingSide && index == receivingPlayer) return true;
        if (tackleActive && side == tackleSide && index == tackler) return true;
        if (!looseBall && side == possessingSide && index == possessingPlayer) return true;
        if (pendingGoalStage == 1 && side == pendingGoalSide && index == pendingGoalActor) return true;
        if (restartActive && side == kickoffSide && (index == kickoffPlayerA || index == kickoffPlayerB)) return true;
        if (penaltyPhase != 0 && side == penaltySide && index == penaltyActor) return true;
        if (freeKickPhase != 0 && side == freeKickSide && index == freeKickActor) return true;
        if (cardFoulPhase >= 2 && side == 1 - cardFoulOffenderSide && index == cardFoulTaker) return true;
        return cardFoulPhase != 0 && side == cardFoulOffenderSide && index == cardFoulOffender;
    }

    private void setPenaltyTarget(Dot dot, int index, int sideIndex, boolean awaySide) {
        double direction = penaltySide == 0 ? 1.0 : -1.0;
        if (sideIndex == penaltySide && index == penaltyActor) {
            dot.targetX = (penaltySide == 0 ? .885 : .115)
                    - direction * (penaltyPhase == 1 ? .035 : 0.0);
            dot.targetY = .50;
        } else if (sideIndex != penaltySide && index == 0) {
            dot.targetX = penaltySide == 0 ? .955 : .045;
            dot.targetY = penaltyPhase == 3 && penaltyOutcome == 1 ? penaltyShotY : .50;
        } else if (index == 0) {
            dot.targetX = dot.x;
            dot.targetY = dot.y;
        } else {
            double rowX = (penaltySide == 0 ? .885 : .115) - direction
                    * (sideIndex == penaltySide ? .105 + (index % 2) * .025
                    : .075 + (index % 2) * .025);
            dot.targetX = rowX;
            dot.targetY = .16 + ((index * 2 + sideIndex) % 5) * .17;
        }
    }

    private void setFreeKickTarget(Dot dot, int index, int sideIndex, boolean awaySide) {
        double direction = freeKickSide == 0 ? 1.0 : -1.0;
        if (sideIndex == freeKickSide && index == freeKickActor) {
            dot.targetX = plannedSpotX - direction * (freeKickPhase == 1 ? .035 : 0.0);
            dot.targetY = plannedSpotY;
        } else if (sideIndex != freeKickSide && index == 0) {
            dot.targetX = freeKickSide == 0 ? .955 : .045;
            dot.targetY = .50;
        } else if (sideIndex != freeKickSide && index > 0 && index <= freeKickWall) {
            double offset = (index - (freeKickWall + 1) / 2.0) * .043;
            dot.targetX = plannedSpotX + direction * .060;
            dot.targetY = clamp(plannedSpotY + offset, .16, .84);
        } else if (index == 0) {
            dot.targetX = dot.x;
            dot.targetY = dot.y;
        } else if (sideIndex == freeKickSide) {
            dot.targetX = clamp(plannedSpotX + direction * (.07 + (index % 3) * .045), .08, .92);
            dot.targetY = .14 + ((index * 2) % 6) * .14;
        } else {
            dot.targetX = clamp(plannedSpotX + direction * (.11 + (index % 2) * .035), .08, .92);
            dot.targetY = .15 + ((index * 3) % 6) * .14;
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

    private void updatePlayerPositions() {
        double dt = frameSeconds;
        updateTeamPositions(home, away, 0, dt);
        updateTeamPositions(away, home, 1, dt);
    }

    private void updateTeamPositions(Dot[] team, Dot[] opponents, int side, double dt) {
        for (int index = 0; index < team.length; index++) {
            Dot dot = team[index];
            if (!dot.active) continue;
            boolean anchored = isAnchored(side, index);
            double dx = dot.targetX - dot.currentX;
            double dy = dot.targetY - dot.currentY;
            double distance = Math.sqrt(dx * dx + dy * dy);
            double maxSpeed = dot.roleLine == 0 ? .045 : .105;
            if (index == possessingPlayer && side == possessingSide && !looseBall) {
                maxSpeed = tackleActive ? .06 : .118;
            }
            if ((plannedActionKey != null || pendingGoalStage == 1) && side == plannedSide
                    && (index == plannedActor || index == plannedAssist)) maxSpeed = .145;
            if (anchored && !(index == possessingPlayer && side == possessingSide && !looseBall)) {
                maxSpeed = Math.max(maxSpeed, index == 0 ? .10 : .135);
            }
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
        int top = 8;
        int fieldHeight = Math.min(410, Math.max(330, h - 240));
        int bottom = top + fieldHeight, left = 10, right = w - 10;
        int fieldW = right - left, fieldH = bottom - top;
        for (int i = 0; i < 10; i++) {
            g.setColor((i & 1) == 0 ? GRASS : GRASS_ALT);
            g.fillRect(left + i * fieldW / 10, top, fieldW / 10 + 1, fieldH);
        }
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
        long now = System.currentTimeMillis();
        drawTeam(g, home, homeColor, homeAccent, left, top, fieldW, fieldH, now);
        drawTeam(g, away, awayColor, awayAccent, left, top, fieldW, fieldH, now);
        int bx = left + (int) (ballX * fieldW);
        int by = top + (int) (ballY * fieldH);
        g.setColor(SHADOW);
        g.fillOval(bx - 5, by - 3, 12, 12);
        g.setColor(Color.WHITE);
        g.fillOval(bx - 6, by - 6, 12, 12);
        g.setColor(Color.BLACK);
        g.drawOval(bx - 6, by - 6, 12, 12);
        int eventBarY = bottom + 7;
        drawEventBar(g, w, eventBarY);
        drawOtherMatches(g, w, h, eventBarY + 37);
        g.dispose();
        Toolkit.getDefaultToolkit().sync();
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

    private void drawTeam(Graphics2D g, Dot[] team, Color fill, Color accent,
                          int left, int top, int width, int height, long now) {
        g.setFont(NAME_FONT);
        FontMetrics metrics = g.getFontMetrics();
        int side = team == away ? 1 : 0;
        for (int i = 0; i < team.length; i++) {
            Dot dot = team[i];
            if (!dot.active) continue;
            int x = left + (int) (dot.currentX * width);
            int y = top + (int) (dot.currentY * height);
            g.setColor(SHADOW);
            g.fillOval(x - 9, y - 7, 20, 20);
            g.setColor(fill);
            g.fillOval(x - 10, y - 10, 20, 20);
            g.setColor(accent);
            g.setStroke(STROKE_2);
            g.drawOval(x - 10, y - 10, 20, 20);
            String key = playerKey(side, dot.fullName);
            if (injured.contains(key)) {
                g.setColor(Color.WHITE);
                g.fillOval(x - 17, y - 15, 9, 9);
                g.setColor(CARD_RED);
                g.fillRect(x - 13, y - 13, 2, 6);
                g.fillRect(x - 15, y - 11, 6, 2);
            }
            if (yellowCarded.contains(key) || redCarded.contains(key)) {
                g.setColor(redCarded.contains(key) ? CARD_RED : CARD_YELLOW);
                g.fillRoundRect(x + 8, y - 13, 6, 10, 2, 2);
                g.setColor(CARD_EDGE);
                g.drawRoundRect(x + 8, y - 13, 6, 10, 2, 2);
            }
            int textW = metrics.stringWidth(dot.name);
            int tx = x - textW / 2;
            int ty = y - 14;
            g.setColor(NAME_BACK);
            g.fillRoundRect(tx - 3, ty - metrics.getAscent(), textW + 6, metrics.getHeight(), 6, 6);
            g.setColor(Color.WHITE);
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

    private Color[] teamColors(Object team, Color fallback, Color fallbackAccent) {
        Color primary = parseColor(readField(team, "cor1"), fallback);
        Color accent = parseColor(readField(team, "cor2"), fallbackAccent);
        return new Color[] { primary, accent };
    }

    private Color[] kitColors(Object team, int kit, Color fallback, Color fallbackAccent) {
        Object value = invokeInt(team, "bU", kit);
        if (!(value instanceof ImageIcon)) return teamColors(team, fallback, fallbackAccent);
        ImageIcon icon = (ImageIcon) value;
        if (icon.getIconWidth() <= 0 || icon.getIconHeight() <= 0) {
            return teamColors(team, fallback, fallbackAccent);
        }
        BufferedImage sample = new BufferedImage(32, 32, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = sample.createGraphics();
        graphics.drawImage(icon.getImage(), 0, 0, 32, 32, null);
        graphics.dispose();
        long red = 0, green = 0, blue = 0, weight = 0;
        for (int y = 0; y < 32; y++) {
            for (int x = 0; x < 32; x++) {
                int pixel = sample.getRGB(x, y);
                int alpha = pixel >>> 24;
                if (alpha < 70) continue;
                red += ((pixel >> 16) & 255) * alpha;
                green += ((pixel >> 8) & 255) * alpha;
                blue += (pixel & 255) * alpha;
                weight += alpha;
            }
        }
        if (weight == 0) return teamColors(team, fallback, fallbackAccent);
        Color primary = new Color((int) (red / weight), (int) (green / weight), (int) (blue / weight));
        double luminance = primary.getRed() * .2126 + primary.getGreen() * .7152 + primary.getBlue() * .0722;
        Color accent = luminance < 145 ? Color.WHITE : new Color(18, 24, 31);
        return new Color[] { primary, accent };
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
        int roleLine;
        boolean wideRole;
        boolean active = true;
        boolean known;
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
