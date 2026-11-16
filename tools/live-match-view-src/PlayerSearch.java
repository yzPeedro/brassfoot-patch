package mega;

import java.util.Locale;

public final class PlayerSearch {
    private PlayerSearch() {
    }

    private static String normalize(String value) {
        if (value == null) return "";
        String text = value.toLowerCase(Locale.ROOT);
        text = text.replace("\u00e1", "a").replace("\u00e9", "e").replace("\u00ed", "i")
                .replace("\u00f3", "o").replace("\u00fa", "u").replace("\u00e7", "c")
                .replace("\u00e2", "a").replace("\u00ea", "e").replace("\u00ee", "i")
                .replace("\u00f4", "o").replace("\u00fb", "u").replace("\u00e0", "a")
                .replace("\u00e8", "e").replace("\u00ec", "i").replace("\u00f2", "o")
                .replace("\u00f9", "u").replace("\u00c3", "a").replace("\u00d5", "o");
        return text;
    }

    public static String normalizedName(String name) {
        return normalize(name);
    }

    public static String keepFullName(String name, int start, int end) {
        return name;
    }

    public static boolean termMatch(String query, String playerName) {
        if (query == null || query.length() == 0) return true;
        String text = normalize(playerName);
        String[] terms = normalize(query).split("\\s+");
        for (int i = 0; i < terms.length; i++) {
            if (terms[i].length() == 0) continue;
            if (!text.contains(terms[i])) return false;
        }
        return true;
    }
}
