package mega;

import java.awt.BasicStroke;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Locale;
import javax.swing.BorderFactory;
import javax.swing.Icon;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.JToolBar;
import javax.swing.JTree;
import javax.swing.border.LineBorder;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import javax.swing.tree.TreeModel;

final class PlaceholderField extends JTextField {
    private final String placeholder;

    PlaceholderField(String placeholder) {
        this.placeholder = placeholder;
    }

    @Override protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        if (getText().length() == 0 && !hasFocus()) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(java.awt.RenderingHints.KEY_TEXT_ANTIALIASING,
                    java.awt.RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
            g2.setColor(new Color(130, 140, 160));
            g2.setFont(getFont().deriveFont(Font.ITALIC));
            Insets insets = getInsets();
            FontMetrics fm = g2.getFontMetrics();
            int y = (getHeight() - fm.getHeight()) / 2 + fm.getAscent();
            g2.drawString(placeholder, insets.left + 2, y);
            g2.dispose();
        }
    }
}

public final class TeamTools {
    private TeamTools() {
    }

    private static Object field(Object target, String name) {
        Class<?> type = target.getClass();
        while (type != null) {
            try {
                Field f = type.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(target);
            } catch (Throwable ignored) {
                type = type.getSuperclass();
            }
        }
        return null;
    }

    private static Object staticField(String className, String name) {
        try {
            Field f = Class.forName(className).getDeclaredField(name);
            f.setAccessible(true);
            return f.get(null);
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static Object invoke(Object target, String name) {
        if (target == null) return null;
        try {
            Method m = target.getClass().getMethod(name);
            m.setAccessible(true);
            return m.invoke(target);
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static String normalize(String value) {
        if (value == null) return "";
        String text = value.toLowerCase(Locale.ROOT);
        text = text.replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i")
                .replace("\u00f3", "o").replace("\u00fa", "u").replace("\u00e7", "c")
                .replace("\u00e2", "a").replace("\u00ea", "e").replace("\u00ee", "i")
                .replace("\u00f4", "o").replace("\u00fb", "u").replace("\u00e0", "a")
                .replace("\u00e8", "e").replace("\u00ec", "i").replace("\u00f2", "o")
                .replace("\u00f9", "u");
        return text.trim();
    }

    private static boolean matches(String nodeText, String query) {
        if (query.length() == 0) return true;
        String text = normalize(nodeText);
        String[] terms = query.split("\\s+");
        for (int i = 0; i < terms.length; i++) {
            if (terms[i].length() == 0) continue;
            if (!text.contains(terms[i])) return false;
        }
        return true;
    }

    private static String nodeText(Object node) {
        Object user = ((DefaultMutableTreeNode) node).getUserObject();
        if (user == null) return "";
        String direct = user.toString();
        return direct == null ? "" : direct;
    }

    private static DefaultMutableTreeNode filterNode(DefaultMutableTreeNode original, String query) {
        Object user = original.getUserObject();
        boolean leafTeam = original.isLeaf() && user != null
                && "best.ah".equals(user.getClass().getName());
        if (leafTeam) {
            return matches(nodeText(original), query) ? new DefaultMutableTreeNode(user) : null;
        }
        DefaultMutableTreeNode copy = new DefaultMutableTreeNode(user);
        int children = original.getChildCount();
        for (int i = 0; i < children; i++) {
            DefaultMutableTreeNode child = (DefaultMutableTreeNode) original.getChildAt(i);
            DefaultMutableTreeNode filtered = filterNode(child, query);
            if (filtered != null) copy.add(filtered);
        }
        if (query.length() > 0 && copy.getChildCount() == 0) return null;
        return copy;
    }

    private static void expandAll(JTree tree) {
        for (int i = 0; i < tree.getRowCount(); i++) tree.expandRow(i);
    }

    private static void log(String message) {
        java.io.PrintWriter out = null;
        try {
            String base = System.getenv("LOCALAPPDATA");
            if (base == null || base.trim().length() == 0) base = System.getProperty("user.home");
            java.io.File folder = new java.io.File(base, "BrassfootPatch2026");
            if (!folder.isDirectory()) folder.mkdirs();
            out = new java.io.PrintWriter(new java.io.FileWriter(
                    new java.io.File(folder, "team-tools.log"), true));
            out.println(new java.util.Date() + " | " + message);
        } catch (Throwable ignored) {
        } finally {
            if (out != null) out.close();
        }
    }

    public static void install(final Object screen) {
        try {
            installInner(screen);
        } catch (Throwable error) {
            log("install FAILED: " + error.getClass().getName() + ": " + error.getMessage());
            java.io.StringWriter trace = new java.io.StringWriter();
            error.printStackTrace(new java.io.PrintWriter(trace));
            log(trace.toString());
        }
    }

    private static void installInner(final Object screen) {
        log("install start screen=" + screen.getClass().getName());
        JTree tree = (JTree) field(screen, "uw");
        JScrollPane scroller = (JScrollPane) field(screen, "wi");
        JToolBar toolbar = (JToolBar) field(screen, "ve");
        JButton transfers = (JButton) field(screen, "Ic");
        log("fields tree=" + (tree != null) + " scroller=" + (scroller != null)
                + " toolbar=" + (toolbar != null) + " transfers=" + (transfers != null));
        if (tree == null || scroller == null) return;

        final JTree finalTree = tree;
        final TreeModel originalModel = tree.getModel();
        final DefaultMutableTreeNode originalRoot = originalModel instanceof DefaultTreeModel
                ? (DefaultMutableTreeNode) ((DefaultTreeModel) originalModel).getRoot() : null;
        if (originalRoot == null) return;

        final PlaceholderField search = new PlaceholderField("Buscar time por nome...");
        search.setFont(new Font("Tahoma", Font.PLAIN, 12));
        search.setBorder(BorderFactory.createEmptyBorder(3, 4, 3, 4));
        search.setOpaque(false);
        search.setToolTipText("Buscar time por nome (qualquer parte, incluindo o segundo nome)");

        JPanel searchBox = new JPanel(new BorderLayout(4, 0));
        searchBox.setBorder(new LineBorder(new Color(150, 170, 205), 1, true));
        searchBox.setBackground(Color.WHITE);
        JLabel magnifier = new JLabel(searchIcon());
        magnifier.setBorder(BorderFactory.createEmptyBorder(0, 5, 0, 2));
        searchBox.add(magnifier, BorderLayout.WEST);
        searchBox.add(search, BorderLayout.CENTER);

        final Runnable[] applier = new Runnable[1];
        search.getDocument().addDocumentListener(new DocumentListener() {
            public void insertUpdate(DocumentEvent e) { applier[0].run(); }
            public void removeUpdate(DocumentEvent e) { applier[0].run(); }
            public void changedUpdate(DocumentEvent e) { applier[0].run(); }
        });

        JPanel holder = new JPanel(new BorderLayout(0, 4));
        holder.setOpaque(false);
        holder.add(searchBox, BorderLayout.NORTH);
        holder.add(tree, BorderLayout.CENTER);
        scroller.setViewportView(holder);

        applier[0] = new Runnable() {
            public void run() {
                String query = normalize(search.getText());
                try {
                    if (query.length() == 0) {
                        finalTree.setModel(originalModel);
                        expandAll(finalTree);
                        return;
                    }
                    DefaultMutableTreeNode filtered = filterNode(originalRoot, query);
                    if (filtered == null) filtered = new DefaultMutableTreeNode("Times");
                    finalTree.setModel(new DefaultTreeModel(filtered));
                    expandAll(finalTree);
                } catch (Throwable ignored) {
                    finalTree.setModel(originalModel);
                }
            }
        };

        if (toolbar != null) {
            JButton stadium = new JButton();
            stadium.setToolTipText("Forma\u00e7\u00e3o t\u00e1tica mais usada nos \u00faltimos jogos");
            Icon icon = loadStadiumIcon();
            if (icon != null) stadium.setIcon(icon);
            else stadium.setText("\u26ab");
            stadium.setOpaque(false);
            stadium.setFocusable(false);
            stadium.setBorderPainted(false);
            stadium.setPreferredSize(new java.awt.Dimension(35, 35));
            stadium.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) { showFormation(screen); }
            });
            int index = -1;
            if (transfers != null) {
                for (int i = 0; i < toolbar.getComponentCount(); i++) {
                    if (toolbar.getComponent(i) == transfers) { index = i; break; }
                }
            }
            toolbar.add(stadium, index >= 0 ? index + 1 : toolbar.getComponentCount());
        }
    }

    private static Icon searchIcon() {
        int size = 16;
        java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(
                size, size, java.awt.image.BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(110, 125, 150));
        g.setStroke(new BasicStroke(1.7f));
        g.drawOval(2, 2, 9, 9);
        g.drawLine(10, 10, 14, 14);
        g.dispose();
        return new ImageIcon(image);
    }

    private static Icon loadStadiumIcon() {
        int size = 35;
        java.awt.image.BufferedImage image = new java.awt.image.BufferedImage(
                size, size, java.awt.image.BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
        int midX = size / 2;
        int midY = size / 2;
        int left = 4, right = size - 5;
        int top = 5, bottom = size - 6;
        g.setColor(new Color(46, 140, 74));
        g.fillRect(left, top, right - left, bottom - top);
        g.setColor(new Color(255, 255, 255, 225));
        g.setStroke(new BasicStroke(1.3f));
        g.drawRect(left, top, right - left, bottom - top);
        g.drawLine(left, midY, right, midY);
        g.drawOval(midX - 5, midY - 5, 10, 10);
        int boxDepth = 5, boxHalf = 6;
        g.drawRect(midX - boxHalf, top, boxHalf * 2, boxDepth);
        g.drawRect(midX - boxHalf, bottom - boxDepth, boxHalf * 2, boxDepth);
        g.dispose();
        return new ImageIcon(image);
    }

    private static int[] mostUsedFormation(Object team) {
        Object root = staticField("c.a", "SR");
        if (root == null) return null;
        Object daysValue = invoke(root, "R");
        if (!(daysValue instanceof ArrayList)) return null;
        ArrayList days = (ArrayList) daysValue;
        Object todayValue = invoke(root, "J");
        int today = todayValue instanceof Integer ? ((Integer) todayValue).intValue() : days.size() - 1;
        int[] bestSlots = null;
        int bestCount = 0;
        for (int d = days.size() - 1; d >= 0; d--) {
            Object day = days.get(d);
            Object matchesValue = invoke(day, "h");
            if (!(matchesValue instanceof ArrayList)) continue;
            ArrayList matches = (ArrayList) matchesValue;
            for (int j = 0; j < matches.size(); j++) {
                Object match = matches.get(j);
                Boolean played = (Boolean) invoke(match, "e");
                if (played == null || !played.booleanValue()) continue;
                Object home = invoke(match, "hc");
                Object away = invoke(match, "hd");
                int side = -1;
                if (team == home) side = 0;
                else if (team == away) side = 1;
                if (side < 0) continue;
                Object grid = invoke(match, "id");
                if (!(grid instanceof int[][])) continue;
                int[][] slots = (int[][]) grid;
                if (side >= slots.length || slots[side] == null) continue;
                int[] formation = slots[side];
                int count = formationCount(days, team, formation);
                if (count > bestCount) {
                    bestCount = count;
                    bestSlots = formation;
                }
            }
        }
        return bestSlots;
    }

    private static int formationCount(ArrayList days, Object team, int[] slots) {
        int count = 0;
        for (int d = 0; d < days.size(); d++) {
            Object day = days.get(d);
            Object matchesValue = invoke(day, "h");
            if (!(matchesValue instanceof ArrayList)) continue;
            ArrayList matches = (ArrayList) matchesValue;
            for (int j = 0; j < matches.size(); j++) {
                Object match = matches.get(j);
                Boolean played = (Boolean) invoke(match, "e");
                if (played == null || !played.booleanValue()) continue;
                Object home = invoke(match, "hc");
                Object away = invoke(match, "hd");
                int side = -1;
                if (team == home) side = 0;
                else if (team == away) side = 1;
                if (side < 0) continue;
                Object grid = invoke(match, "id");
                if (!(grid instanceof int[][])) continue;
                int[][] all = (int[][]) grid;
                if (side >= all.length || all[side] == null) continue;
                if (Arrays.equals(all[side], slots)) count++;
            }
        }
        return count;
    }

    private static String formationName(int[] slots) {
        if (slots == null) return "Indispon\u00edvel";
        Object formations = staticField("best.aq", "sJ");
        Object names = staticField("best.aq", "rB");
        if (!(formations instanceof int[][]) || !(names instanceof String[])) return "Personalizada";
        int[][] table = (int[][]) formations;
        String[] labels = (String[]) names;
        for (int i = 1; i < table.length && i + 1 < labels.length; i++) {
            if (Arrays.equals(table[i], slots)) return labels[i + 1];
        }
        return "Personalizada";
    }

    private static int[][] pitchCells() {
        Object raw = staticField("components.ao", "RJ");
        if (!(raw instanceof int[][])) return null;
        return (int[][]) raw;
    }

    private static void showFormation(Object screen) {
        log("showFormation click");
        try {
            showFormationInner(screen);
        } catch (Throwable error) {
            log("showFormation FAILED: " + error.getClass().getName() + ": " + error.getMessage());
            java.io.StringWriter trace = new java.io.StringWriter();
            error.printStackTrace(new java.io.PrintWriter(trace));
            log(trace.toString());
        }
    }

    private static Object newSlot() {
        try {
            return Class.forName("components.ao").newInstance();
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static void slotSetPlayer(Object slot, Object player) {
        call(slot, "a", new Class<?>[] { Object.class }, new Object[] { player }, "best.F");
    }

    private static void slotSetShirt(Object slot, Object shirt) {
        call(slot, "h", new Class<?>[] { Object.class }, new Object[] { shirt }, "javax.swing.ImageIcon");
    }

    private static Object call(Object target, String name, Class<?>[] types, Object[] args, String actual) {
        try {
            Class<?>[] real = new Class<?>[types.length];
            for (int i = 0; i < types.length; i++) real[i] = Class.forName(actual);
            Method m = target.getClass().getMethod(name, real);
            m.setAccessible(true);
            return m.invoke(target, args);
        } catch (Throwable error) {
            log("call " + name + " FAILED: " + error);
            return null;
        }
    }

    private static Object callNoArgs(Object target, String name) {
        try {
            Method m = target.getClass().getMethod(name);
            m.setAccessible(true);
            return m.invoke(target);
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static int intCall(Object target, String name) {
        Object value = callNoArgs(target, name);
        return value instanceof Integer ? ((Integer) value).intValue() : -1;
    }

    private static Object renderPitch(ArrayList slots, int skip, Object shirt, boolean compact,
                                      int mode, Object team, boolean withMarkers) {
        try {
            Class<?> aoClass = Class.forName("components.ao");
            Object receiver = slots.get(0);
            Method m = null;
            Method[] methods = aoClass.getMethods();
            for (int i = 0; i < methods.length; i++) {
                if (!"a".equals(methods[i].getName())) continue;
                if (methods[i].getReturnType() != javax.swing.ImageIcon.class) continue;
                Class<?>[] params = methods[i].getParameterTypes();
                if (params.length < 1 || params[0] != java.util.ArrayList.class) continue;
                if (withMarkers && params.length == 7 && params[6] == int.class) m = methods[i];
                else if (!withMarkers && params.length == 6) m = methods[i];
            }
            if (m == null) {
                log("renderPitch no method found withMarkers=" + withMarkers);
                return null;
            }
            m.setAccessible(true);
            StringBuilder sig = new StringBuilder("renderPitch method=" + m.toString());
            for (Class<?> pt : m.getParameterTypes()) sig.append(" [").append(pt.getName()).append("]");
            sig.append(" | shirt=").append(shirt == null ? "null" : shirt.getClass().getName())
               .append(" team=").append(team == null ? "null" : team.getClass().getName());
            log(sig.toString());
            if (withMarkers) {
                return m.invoke(receiver, slots, Integer.valueOf(skip), shirt,
                        Boolean.valueOf(compact), Integer.valueOf(1), team, Integer.valueOf(mode));
            } else {
                return m.invoke(receiver, slots, Integer.valueOf(skip), shirt,
                        Boolean.valueOf(compact), Integer.valueOf(1), null);
            }
        } catch (Throwable error) {
            log("renderPitch FAILED: " + error);
            return null;
        }
    }

    private static Object renderAvailable(ArrayList slots, Object shirt) {
        try {
            Class<?> aoClass = Class.forName("components.ao");
            Method m = null;
            Method[] methods = aoClass.getMethods();
            for (int i = 0; i < methods.length; i++) {
                if (!"a".equals(methods[i].getName())) continue;
                if (methods[i].getParameterTypes().length == 3) { m = methods[i]; break; }
            }
            if (m == null) return null;
            m.setAccessible(true);
            return m.invoke(slots.get(0), slots, Integer.valueOf(-1), shirt);
        } catch (Throwable error) {
            log("renderAvailable FAILED: " + error);
            return null;
        }
    }

    private static javax.swing.Icon resourceIcon(String path) {
        try {
            java.net.URL url = TeamTools.class.getResource(path);
            if (url != null) return new javax.swing.ImageIcon(url);
        } catch (Throwable ignored) {
        }
        return null;
    }

    private static void showFormationInner(Object screen) {
        JDialog owner = (JDialog) field(screen, "ub");
        Object team = field(screen, "uk");
        log("showFormationInner team=" + (team == null ? "null" : team.getClass().getName()));

        final Object shirt = callNoArgs(team, "kS");
        final ArrayList slots = new ArrayList();
        for (int i = 0; i <= 91; i++) slots.add(newSlot());

        java.util.HashSet placed = new java.util.HashSet();

        Object tactic = callNoArgs(team, "kX");
        ArrayList tacticPlayers = tactic == null ? null : (ArrayList) callNoArgs(tactic, "uH");
        ArrayList tacticSlots = tactic == null ? null : (ArrayList) callNoArgs(tactic, "uI");
        if (tacticPlayers != null && tacticSlots != null) {
            for (int i = 0; i < tacticPlayers.size() && i < tacticSlots.size(); i++) {
                Object player = tacticPlayers.get(i);
                Object slotValue = tacticSlots.get(i);
                if (player == null || slotValue == null || !(slotValue instanceof Integer)) continue;
                int slotIndex = ((Integer) slotValue).intValue();
                if (slotIndex >= 1 && slotIndex < slots.size()) {
                    Object slot = slots.get(slotIndex);
                    slotSetPlayer(slot, player);
                    slotSetShirt(slot, shirt);
                    placed.add(player);
                }
            }
        }

        if (placed.isEmpty()) {
            Object sJRaw = staticField("best.aq", "sJ");
            int[][] formationTable = sJRaw instanceof int[][] ? (int[][]) sJRaw : null;
            int[] tactics = (int[]) callNoArgs(team, "kj");
            int formationIndex = (tactics != null && tactics.length > 0) ? tactics[0] : 4;
            if (formationIndex < 1 || formationIndex >= (formationTable == null ? 1 : formationTable.length)) {
                formationIndex = 4;
            }
            ArrayList starters = (ArrayList) callNoArgs(team, "kY");
            if (starters != null && formationTable != null) {
                int[] houses = formationTable[formationIndex];
                for (int i = 0; i < starters.size() && i < houses.length; i++) {
                    Object player = starters.get(i);
                    int slotIndex = houses[i];
                    if (player != null && slotIndex >= 1 && slotIndex < slots.size()) {
                        Object slot = slots.get(slotIndex);
                        slotSetPlayer(slot, player);
                        slotSetShirt(slot, shirt);
                        placed.add(player);
                    }
                }
            }
            ArrayList bench = (ArrayList) callNoArgs(team, "kZ");
            if (bench != null) {
                int benchSlot = 26;
                for (int i = 0; i < bench.size() && benchSlot <= 36 && benchSlot < slots.size(); i++) {
                    Object player = bench.get(i);
                    if (player != null && !placed.contains(player)) {
                        Object slot = slots.get(benchSlot);
                        slotSetPlayer(slot, player);
                        slotSetShirt(slot, shirt);
                        placed.add(player);
                        benchSlot++;
                    }
                }
            }
        }

        ArrayList available = (ArrayList) callNoArgs(team, "ky");
        int extraSlot = 37;
        if (available != null) {
            for (int i = 0; i < available.size() && extraSlot < slots.size(); i++) {
                Object player = available.get(i);
                if (player == null || placed.contains(player)) continue;
                Object slot = slots.get(extraSlot);
                slotSetPlayer(slot, player);
                slotSetShirt(slot, shirt);
                extraSlot++;
            }
        }

        final Object fieldImage = renderPitch(slots, -1, shirt, false, 0, team, true);
        final Object benchImage = renderPitch(slots, -1, shirt, false, 1, team, true);
        final Object availableImage = renderAvailable(slots, shirt);
        log("rendered field=" + (fieldImage != null) + " bench=" + (benchImage != null)
                + " available=" + (availableImage != null));

        javax.swing.JLayeredPane layered = new javax.swing.JLayeredPane();
        layered.setPreferredSize(new java.awt.Dimension(1024, 650));
        layered.setBackground(new Color(128, 141, 128));
        layered.setOpaque(true);

        javax.swing.Icon pitchIcon = resourceIcon("/aicons/campo.png");
        javax.swing.JLabel pitchBg = new javax.swing.JLabel(pitchIcon);
        pitchBg.setBounds(0, 0, 434, 650);
        layered.add(pitchBg, javax.swing.JLayeredPane.DEFAULT_LAYER);

        if (fieldImage instanceof javax.swing.Icon) {
            javax.swing.JLabel fieldLabel = new javax.swing.JLabel((javax.swing.Icon) fieldImage);
            fieldLabel.setBounds(0, 0, 480, 679);
            layered.add(fieldLabel, javax.swing.JLayeredPane.POPUP_LAYER);
        }

        JLabel benchTitle = new JLabel("  Banco de reservas");
        benchTitle.setOpaque(true);
        benchTitle.setBackground(new Color(51, 51, 51));
        benchTitle.setForeground(Color.WHITE);
        benchTitle.setFont(new Font("Arial", Font.PLAIN, 12));
        benchTitle.setBounds(435, 0, 590, 20);
        layered.add(benchTitle, javax.swing.JLayeredPane.POPUP_LAYER);

        JLabel availTitle = new JLabel("  Jogadores dispon\u00edveis");
        availTitle.setOpaque(true);
        availTitle.setBackground(new Color(51, 51, 51));
        availTitle.setForeground(Color.WHITE);
        availTitle.setFont(new Font("Arial", Font.PLAIN, 12));
        availTitle.setBounds(435, 185, 590, 20);
        layered.add(availTitle, javax.swing.JLayeredPane.POPUP_LAYER);

        if (benchImage instanceof javax.swing.Icon) {
            javax.swing.JLabel benchLabel = new javax.swing.JLabel((javax.swing.Icon) benchImage);
            benchLabel.setBounds(440, 30, 580, 160);
            layered.add(benchLabel, javax.swing.JLayeredPane.POPUP_LAYER);
        }

        if (availableImage instanceof javax.swing.Icon) {
            javax.swing.JLabel availLabel = new javax.swing.JLabel((javax.swing.Icon) availableImage);
            availLabel.setBounds(435, 210, 580, 410);
            layered.add(availLabel, javax.swing.JLayeredPane.POPUP_LAYER);
        }

        final JDialog dialog = new JDialog(owner, "Forma\u00e7\u00e3o t\u00e1tica", true);
        dialog.setUndecorated(true);
        dialog.setSize(1024, 650);
        dialog.setPreferredSize(new java.awt.Dimension(1024, 650));
        dialog.setMinimumSize(new java.awt.Dimension(1024, 650));
        dialog.setResizable(false);
        dialog.setLocationRelativeTo(owner);

        JButton back = new JButton("<< Voltar");
        back.setIcon(resourceIcon("/aicons/home.png"));
        back.setFont(new Font("Tahoma", Font.PLAIN, 12));
        back.setFocusPainted(false);
        back.setBounds(1024 - 172, 610, 160, 31);
        back.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) { dialog.dispose(); }
        });
        layered.add(back, javax.swing.JLayeredPane.POPUP_LAYER);

        javax.swing.KeyStroke escape = javax.swing.KeyStroke.getKeyStroke(
                java.awt.event.KeyEvent.VK_ESCAPE, 0);
        dialog.getRootPane().getInputMap(javax.swing.JComponent.WHEN_IN_FOCUSED_WINDOW)
                .put(escape, "closeTactic");
        dialog.getRootPane().getActionMap().put("closeTactic", new javax.swing.AbstractAction() {
            public void actionPerformed(ActionEvent e) { dialog.dispose(); }
        });

        dialog.setContentPane(layered);
        dialog.setVisible(true);
    }

}
