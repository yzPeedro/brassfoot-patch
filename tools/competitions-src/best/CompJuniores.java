package best;

import c.a;
import java.io.File;
import java.util.ArrayList;

public final class CompJuniores {
    static final String MARKER = "juniores-reais.json";
    static final int MAX_AGE = 20;
    static final int MAX_PROFESSIONALS = 35;
    private static Boolean real;

    private CompJuniores() {
    }

    private static void log(String message, Throwable error) {
        System.err.println("[CompJuniores] " + message + (error == null ? "" : ": " + error));
    }

    public static boolean realMode() {
        if (real == null) {
            String dir = System.getProperty("user.dir");
            real = Boolean.valueOf(dir != null && new File(dir, MARKER).isFile());
        }
        return real.booleanValue();
    }

    private static java.util.Set researched() {
        java.util.Set clubs = new java.util.HashSet();
        try {
            String text = new String(java.nio.file.Files.readAllBytes(new File(System.getProperty("user.dir"), MARKER).toPath()), "UTF-8");
            int start = text.indexOf("\"clubs\"");
            int open = text.indexOf('[', start);
            int close = text.indexOf(']', open);
            if (start < 0 || open < 0 || close < 0) return clubs;
            java.util.regex.Matcher m = java.util.regex.Pattern.compile("\"([^\"]+)\"").matcher(text.substring(open, close));
            while (m.find()) clubs.add(m.group(1).toLowerCase());
        } catch (Exception error) {
            log("marcador de juniores ilegivel", error);
        }
        return clubs;
    }

    public static boolean skipGeneration(f state, boolean season) {
        if (!realMode()) return false;
        if (!season) {
            java.util.Set clubs = researched();
            ArrayList teams = a.SR.P();
            int cleared = 0;
            for (int i = 0; i < teams.size(); i++) {
                ah club = (ah) teams.get(i);
                if (clubs.contains(club.jY().toLowerCase())) continue;
                ArrayList juniors = club.ky();
                for (int j = 0; j < juniors.size(); j++) {
                    ((F) juniors.get(j)).n(null);
                    a.SR.Q().remove(juniors.get(j));
                    cleared++;
                }
                juniors.clear();
            }
            log(clubs.size() + " clubes com Sub-20 real; " + cleared + " juniores de clubes sem pesquisa retirados", null);
        }
        return true;
    }

    public static boolean seasonTurn(F player) {
        try {
            if (!realMode()) return false;
            int age = player.getIdade() + 1;
            ah club = player.fg();
            if (age > MAX_AGE) {
                if (club != null) {
                    K.a(true, player, club);
                    if (club.kc().size() > MAX_PROFESSIONALS) {
                        club.kc().remove(player);
                        player.n(null);
                    }
                } else {
                    player.h(false);
                    a.SR.Q().remove(player);
                    if (!a.SR.O().contains(player)) a.SR.O().add(player);
                }
            }
            player.setIdade(age);
            return true;
        } catch (Throwable error) {
            log("falha na virada do junior", error);
            return false;
        }
    }

    public static F replacement(ah club, int position, F reuse, int value, String name, Boolean season) {
        if (!realMode()) return F.a(club, position, reuse, value, name, season);
        if (club == null) return null;
        int[] minimum = {2, 3, 3, 6, 4};
        int[] counts = club.J(true);
        boolean short_ = club.kc().size() < 16 || position >= 0 && position < counts.length && counts[position] < minimum[position];
        return short_ ? F.a(club, position, reuse, value, name, season) : null;
    }

    public static boolean academyLabel(javax.swing.JLabel label, ah club) {
        if (!realMode() || label == null || club == null) return false;
        label.setText(club.ky().size() + " jogadores");
        return true;
    }

    public static int academyLimit() {
        return realMode() ? Integer.MAX_VALUE : 20;
    }

    public static ArrayList juniors(ah club) {
        return club == null ? new ArrayList() : club.ky();
    }
}
