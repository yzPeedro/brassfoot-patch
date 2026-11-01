import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class SaveExport {
    private final StringBuilder out = new StringBuilder();
    private final Map<Object, Integer> teamIndex = new IdentityHashMap<Object, Integer>();

    public static void main(String[] args) throws Throwable {
        if (args.length != 2) {
            System.err.println("uso: SaveExport <nome-do-save> <saida.json>");
            System.exit(2);
        }
        new best.M(true);
        if (!c.a.c(args[0], false)) throw new IllegalStateException("save não carregado: " + args[0]);
        new SaveExport().export(c.a.SR, args[0], new File(args[1]));
        System.exit(0);
    }

    private static Object field(Object owner, String name) throws Exception {
        for (Class<?> type = owner.getClass(); type != null; type = type.getSuperclass()) {
            try {
                Field field = type.getDeclaredField(name);
                field.setAccessible(true);
                return field.get(owner);
            } catch (NoSuchFieldException ignored) {
            }
        }
        return null;
    }

    private static List<?> list(Object owner, String name) throws Exception {
        Object value = field(owner, name);
        return value instanceof List ? (List<?>) value : new ArrayList<Object>();
    }

    private static int number(Object owner, String name) throws Exception {
        Object value = field(owner, name);
        return value instanceof Number ? ((Number) value).intValue() : -1;
    }

    private void export(Object world, String save, File target) throws Exception {
        List<?> teams = list(world, "aj");
        for (int i = 0; i < teams.size(); i++) teamIndex.put(teams.get(i), Integer.valueOf(i));
        out.append("{\"schemaVersion\":1,\"save\":").append(quote(save));
        out.append(",\"season\":").append(number(world, "rM"));
        out.append(",\"humanTeams\":[");
        List<?> human = list(world, "ak");
        for (int i = 0; i < human.size(); i++) {
            if (i > 0) out.append(',');
            Integer index = teamIndex.get(human.get(i));
            out.append(index == null ? -1 : index.intValue());
        }
        out.append("],\"teams\":[");
        for (int i = 0; i < teams.size(); i++) {
            if (i > 0) out.append(',');
            writeTeam(i, teams.get(i));
        }
        out.append("],\"freeAgents\":[");
        List<?> free = list(world, "ah");
        for (int i = 0; i < free.size(); i++) {
            if (i > 0) out.append(',');
            writePlayer(free.get(i));
        }
        out.append(']');
        out.append(",\"competitions\":[");
        boolean first = true;
        for (Competition competition : competitions(world)) {
            if (!first) out.append(',');
            first = false;
            out.append("{\"path\":").append(quote(competition.path)).append(",\"type\":").append(quote(competition.type))
                    .append(",\"label\":").append(quote(competition.label)).append(",\"teams\":[");
            boolean firstTeam = true;
            for (Integer index : competition.teams) {
                if (!firstTeam) out.append(',');
                firstTeam = false;
                out.append(index.intValue());
            }
            out.append("]}");
        }
        out.append("]}");
        Writer writer = new OutputStreamWriter(new FileOutputStream(target), "UTF-8");
        try {
            writer.write(out.toString());
        } finally {
            writer.close();
        }
    }

    private void writeTeam(int index, Object team) throws Exception {
        out.append("{\"index\":").append(index)
                .append(",\"id\":").append(number(team, "mU"))
                .append(",\"file\":").append(quote(String.valueOf(field(team, "mV"))))
                .append(",\"name\":").append(quote(String.valueOf(field(team, "dm"))))
                .append(",\"country\":").append(number(team, "pais"))
                .append(",\"state\":").append(number(team, "dr"))
                .append(",\"division\":").append(number(team, "divisao"))
                .append(",\"players\":[");
        List<?> players = list(team, "nd");
        for (int i = 0; i < players.size(); i++) {
            if (i > 0) out.append(',');
            writePlayer(players.get(i));
        }
        out.append("]}");
    }

    private void writePlayer(Object player) throws Exception {
        out.append("{\"id\":").append(number(player, "ei"))
                .append(",\"name\":").append(quote(String.valueOf(field(player, "dm"))))
                .append(",\"age\":").append(number(player, "em"))
                .append(",\"country\":").append(number(player, "pais"))
                .append(",\"position\":").append(number(player, "er"))
                .append('}');
    }

    private static final class Competition {
        String path;
        String type;
        String label;
        Set<Integer> teams = new LinkedHashSet<Integer>();
    }

    private List<Competition> competitions(Object world) throws Exception {
        List<Competition> result = new ArrayList<Competition>();
        for (Field field : world.getClass().getDeclaredFields()) {
            if (Modifier.isStatic(field.getModifiers())) continue;
            if (!field.getType().getName().startsWith("f.")) continue;
            field.setAccessible(true);
            Object value = field.get(world);
            if (value != null) addCompetition(result, "mundo." + field.getName(), value);
        }
        List<?> cups = list(world, "aq");
        for (int i = 0; i < cups.size(); i++) addCompetition(result, "copas[" + i + "]", cups.get(i));
        for (String countries : new String[] {"ao", "ap"}) {
            List<?> list = list(world, countries);
            for (int i = 0; i < list.size(); i++) {
                Object country = list.get(i);
                String name = String.valueOf(field(country, "hB"));
                List<?> divisions = list(country, "ds");
                for (int d = 0; d < divisions.size(); d++) {
                    addCompetition(result, countries + "[" + i + "]." + name + ".divisao[" + (d + 1) + "]", divisions.get(d));
                }
            }
        }
        return result;
    }

    private void addCompetition(List<Competition> result, String path, Object root) throws Exception {
        Competition competition = new Competition();
        competition.path = path;
        competition.type = root.getClass().getName();
        competition.label = label(root);
        collectTeams(root, competition.teams, new IdentityHashMap<Object, Boolean>(), 0);
        if (!competition.teams.isEmpty()) result.add(competition);
        for (Field field : allFields(root.getClass())) {
            Object value = field.get(root);
            List<Object> children = new ArrayList<Object>();
            if (value instanceof Collection) children.addAll((Collection<?>) value);
            else if (value != null && value.getClass().isArray() && !value.getClass().getComponentType().isPrimitive()) {
                for (int i = 0; i < Array.getLength(value); i++) children.add(Array.get(value, i));
            }
            for (int i = 0; i < children.size(); i++) {
                Object child = children.get(i);
                if (child == null || !isCompetition(child)) continue;
                Competition sub = new Competition();
                sub.path = path + "." + field.getName() + "[" + i + "]";
                sub.type = child.getClass().getName();
                sub.label = label(child);
                collectTeams(child, sub.teams, new IdentityHashMap<Object, Boolean>(), 0);
                if (!sub.teams.isEmpty() && sub.teams.size() < competition.teams.size()) result.add(sub);
            }
        }
    }

    private static boolean isCompetition(Object value) {
        String name = value.getClass().getName();
        return name.startsWith("f.") || name.equals("best.w");
    }

    private static boolean stop(Object value) {
        String name = value.getClass().getName();
        return name.equals("best.F") || name.equals("best.al") || name.equals("best.f") || name.equals("best.Z")
                || name.startsWith("java.awt") || name.startsWith("javax.") || name.startsWith("components.")
                || value instanceof String || value instanceof Number || value instanceof Boolean
                || value instanceof Character || value instanceof Enum || value instanceof java.util.Calendar;
    }

    private void collectTeams(Object value, Set<Integer> teams, Map<Object, Boolean> seen, int depth) throws Exception {
        if (value == null || depth > 12 || seen.containsKey(value)) return;
        seen.put(value, Boolean.TRUE);
        Integer index = teamIndex.get(value);
        if (index != null) {
            teams.add(index);
            return;
        }
        if (stop(value)) return;
        if (value instanceof Collection) {
            for (Object item : (Collection<?>) value) collectTeams(item, teams, seen, depth + 1);
            return;
        }
        if (value instanceof Map) {
            for (Object item : ((Map<?, ?>) value).values()) collectTeams(item, teams, seen, depth + 1);
            return;
        }
        if (value.getClass().isArray()) {
            if (value.getClass().getComponentType().isPrimitive()) return;
            for (int i = 0; i < Array.getLength(value); i++) collectTeams(Array.get(value, i), teams, seen, depth + 1);
            return;
        }
        String name = value.getClass().getName();
        if (!(name.startsWith("best.") || name.startsWith("f.") || name.startsWith("est."))) return;
        for (Field field : allFields(value.getClass())) collectTeams(field.get(value), teams, seen, depth + 1);
    }

    private static List<Field> allFields(Class<?> type) {
        List<Field> fields = new ArrayList<Field>();
        for (Class<?> current = type; current != null && current != Object.class; current = current.getSuperclass()) {
            for (Field field : current.getDeclaredFields()) {
                if (Modifier.isStatic(field.getModifiers()) || field.getType().isPrimitive()) continue;
                field.setAccessible(true);
                fields.add(field);
            }
        }
        return fields;
    }

    private static String label(Object value) {
        for (Field field : allFields(value.getClass())) {
            try {
                Object text = field.get(value);
                if (text instanceof String && ((String) text).trim().length() > 1) return (String) text;
            } catch (IllegalAccessException ignored) {
            }
        }
        return value.getClass().getName();
    }

    private static String quote(String value) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < 0x20) b.append(String.format("\\u%04x", (int) ch));
            else b.append(ch);
        }
        return b.append('"').toString();
    }
}
