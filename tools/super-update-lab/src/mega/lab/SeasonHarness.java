package mega.lab;

import best.Z;
import f.B;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

public final class SeasonHarness {
    private SeasonHarness() {
    }

    public static void main(String[] args) throws Exception {
        String output = args[0];
        String countries = args[1];
        boolean intClubs = Boolean.parseBoolean(args[2]);
        int seasons = Integer.parseInt(args[3]);
        int maxSteps = Integer.parseInt(args[4]);
        String save = args.length > 5 ? args[5] : null;
        PrintStream console = CareerHarness.quiet(output);
        CareerHarness.prepare();
        StringBuilder playable = new StringBuilder();
        List<Integer> selected = CareerHarness.select(countries, intClubs, playable);
        long createStart = System.nanoTime();
        best.p.dg();
        long createMillis = (System.nanoTime() - createStart) / 1000000L;
        long heapCreated = CareerHarness.heap();
        String leaguesBefore = CareerHarness.leagues();
        StringBuilder seasonsJson = new StringBuilder();
        String failure = null;
        int steps = 0;
        long peakHeap = heapCreated;
        try {
            for (int season = 0; season < seasons; season++) {
                Map<Object, Integer> before = membership();
                int start = c.a.SR.H();
                long seasonStart = System.nanoTime();
                int seasonSteps = 0;
                while (c.a.SR.H() == start && seasonSteps < maxSteps) {
                    c.a.SR.V();
                    seasonSteps++;
                    steps++;
                    if (seasonSteps % 50 == 0) {
                        Runtime runtime = Runtime.getRuntime();
                        peakHeap = Math.max(peakHeap, runtime.totalMemory() - runtime.freeMemory());
                    }
                }
                long seasonMillis = (System.nanoTime() - seasonStart) / 1000000L;
                Map<Object, Integer> after = membership();
                if (seasonsJson.length() > 0) {
                    seasonsJson.append(",\n    ");
                }
                seasonsJson.append("{\"seasonBefore\":").append(start)
                        .append(",\"seasonAfter\":").append(c.a.SR.H())
                        .append(",\"steps\":").append(seasonSteps)
                        .append(",\"millis\":").append(seasonMillis)
                        .append(",\"heapBytes\":").append(CareerHarness.heap())
                        .append(",\"movements\":").append(movements(before, after))
                        .append(",\"leagues\":[").append(CareerHarness.leagues().replace("\n    ", "")).append("]}");
                if (c.a.SR.H() == start) {
                    break;
                }
            }
        } catch (Throwable error) {
            StringWriter trace = new StringWriter();
            error.printStackTrace(new PrintWriter(trace));
            failure = trace.toString();
        }
        long saveBytes = -1L;
        boolean reloaded = false;
        if (save != null && failure == null) {
            c.a.ae(save);
            saveBytes = new java.io.File(System.getProperty("user.dir"), "sav/" + save + ".s22").length();
            int teams = c.a.SR.P().size();
            reloaded = c.a.c(save, false) && c.a.SR.P().size() == teams;
        }
        Writer writer = new OutputStreamWriter(new FileOutputStream(output), "UTF-8");
        writer.write("{\n  \"selectedCountries\": " + selected
                + ",\n  \"internationalClubs\": " + intClubs
                + ",\n  \"teamsInWorld\": " + c.a.SR.P().size()
                + ",\n  \"playersInWorld\": " + CareerHarness.players()
                + ",\n  \"createMillis\": " + createMillis
                + ",\n  \"heapAfterCreateBytes\": " + heapCreated
                + ",\n  \"peakHeapBytes\": " + peakHeap
                + ",\n  \"steps\": " + steps
                + ",\n  \"saveBytes\": " + saveBytes
                + ",\n  \"reloadedSameWorld\": " + reloaded
                + ",\n  \"failure\": " + (failure == null ? "null" : quote(failure))
                + ",\n  \"leaguesAtCreation\": [\n    " + leaguesBefore + "\n  ]"
                + ",\n  \"seasons\": [\n    " + seasonsJson + "\n  ]\n}\n");
        writer.close();
        console.println((failure == null ? "ok " : "falhou ") + output);
        System.exit(0);
    }

    private static Map<Object, Integer> membership() {
        Map<Object, Integer> result = new IdentityHashMap<Object, Integer>();
        for (Object item : c.a.SR.N()) {
            ArrayList divisions = ((Z) item).eb();
            for (int i = 0; i < divisions.size(); i++) {
                for (Object team : ((B) divisions.get(i)).yi().yK()) {
                    result.put(team, i + 1);
                }
            }
        }
        return result;
    }

    private static String movements(Map<Object, Integer> before, Map<Object, Integer> after) {
        Map<String, Integer> counts = new HashMap<String, Integer>();
        for (Map.Entry<Object, Integer> entry : before.entrySet()) {
            Integer next = after.get(entry.getKey());
            String key = entry.getValue() + ">" + (next == null ? 0 : next);
            if (next == null || !next.equals(entry.getValue())) {
                Integer current = counts.get(key);
                counts.put(key, current == null ? 1 : current + 1);
            }
        }
        for (Map.Entry<Object, Integer> entry : after.entrySet()) {
            if (!before.containsKey(entry.getKey())) {
                String key = "0>" + entry.getValue();
                Integer current = counts.get(key);
                counts.put(key, current == null ? 1 : current + 1);
            }
        }
        StringBuilder json = new StringBuilder("{");
        for (Map.Entry<String, Integer> entry : new java.util.TreeMap<String, Integer>(counts).entrySet()) {
            if (json.length() > 1) {
                json.append(',');
            }
            json.append('"').append(entry.getKey()).append("\":").append(entry.getValue());
        }
        return json.append('}').toString();
    }

    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "").replace("\n", "\\n").replace("\t", " ") + "\"";
    }
}
