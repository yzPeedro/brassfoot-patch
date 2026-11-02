package mega.lab;

import best.O;
import best.Z;
import best.ah;
import f.B;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintStream;
import java.io.Writer;
import java.util.ArrayList;
import java.util.List;

public final class CareerHarness {
    private CareerHarness() {
    }

    public static void main(String[] args) throws Exception {
        String output = args[0];
        String countries = args.length > 1 ? args[1] : "all";
        boolean intClubs = args.length > 2 && Boolean.parseBoolean(args[2]);
        PrintStream console = quiet(output);
        Runtime runtime = Runtime.getRuntime();
        long started = System.nanoTime();
        prepare();
        long prepared = System.nanoTime();
        StringBuilder playable = new StringBuilder();
        List<Integer> selected = select(countries, intClubs, playable);
        long heapBefore = heap();
        best.p.dg();
        long created = System.nanoTime();
        long heapAfter = heap();
        String save = args.length > 3 ? args[3] : null;
        long saveMillis = -1L;
        long loadMillis = -1L;
        long saveBytes = -1L;
        boolean loaded = false;
        if (save != null) {
            long saveStart = System.nanoTime();
            c.a.ae(save);
            saveMillis = (System.nanoTime() - saveStart) / 1000000L;
            saveBytes = new java.io.File(System.getProperty("user.dir"), "sav/" + save + ".s22").length();
            int teams = c.a.SR.P().size();
            long loadStart = System.nanoTime();
            loaded = c.a.c(save, false) && c.a.SR.P().size() == teams;
            loadMillis = (System.nanoTime() - loadStart) / 1000000L;
        }
        Writer writer = new OutputStreamWriter(new FileOutputStream(output), "UTF-8");
        writer.write("{\n  \"saveMillis\": " + saveMillis
                + ",\n  \"saveBytes\": " + saveBytes
                + ",\n  \"loadMillis\": " + loadMillis
                + ",\n  \"reloadedSameWorld\": " + loaded
                + ",\n  \"teamsInWorld\": " + c.a.SR.P().size()
                + ",\n  \"playersInWorld\": " + players()
                + ",\n  \"playableCountries\": [" + playable + "]"
                + ",\n  \"selectedCountries\": " + selected
                + ",\n  \"internationalClubs\": " + intClubs
                + ",\n  \"prepareMillis\": " + (prepared - started) / 1000000L
                + ",\n  \"createMillis\": " + (created - prepared) / 1000000L
                + ",\n  \"heapBeforeCreateBytes\": " + heapBefore
                + ",\n  \"heapAfterCreateBytes\": " + heapAfter
                + ",\n  \"maxHeapBytes\": " + runtime.maxMemory()
                + ",\n  \"leagues\": [\n    " + leagues() + "\n  ]\n}\n");
        writer.close();
        console.println("ok " + output);
        System.exit(0);
    }

    static PrintStream quiet(String output) throws Exception {
        PrintStream console = System.out;
        System.setOut(new PrintStream(new FileOutputStream(output + ".stdout.log"), true, "UTF-8"));
        return console;
    }

    static void prepare() {
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
    }

    static List<Integer> select(String countries, boolean intClubs, StringBuilder playable) {
        List<Integer> selected = new ArrayList<Integer>();
        for (Object item : c.a.SR.bF) {
            O option = (O) item;
            boolean pick = "all".equals(countries) || ("," + countries + ",").contains("," + option.getPais() + ",");
            option.v(pick);
            if (pick) {
                selected.add(option.getPais());
            }
            if (playable.length() > 0) {
                playable.append(',');
            }
            playable.append('[').append(option.getPais()).append(',').append(option.iB()).append(']');
        }
        c.a.SR.setJogaIntClubes(intClubs);
        c.a.SR.setJogaSelecoesAll(false);
        c.a.SR.setJogaEstadual(false);
        c.a.SR.I(2023);
        return selected;
    }

    static long heap() {
        Runtime runtime = Runtime.getRuntime();
        System.gc();
        return runtime.totalMemory() - runtime.freeMemory();
    }

    static int players() {
        int players = 0;
        for (Object item : c.a.SR.P()) {
            players += ((ah) item).kc().size();
        }
        return players;
    }

    static String leagues() {
        StringBuilder leagues = new StringBuilder();
        for (Object item : c.a.SR.N()) {
            Z country = (Z) item;
            if (leagues.length() > 0) {
                leagues.append(",\n    ");
            }
            leagues.append("{\"country\":").append(country.jc()).append(",\"divisions\":[");
            ArrayList divisions = country.eb();
            for (int i = 0; i < divisions.size(); i++) {
                if (i > 0) {
                    leagues.append(',');
                }
                leagues.append(((B) divisions.get(i)).yi().yK().size());
            }
            leagues.append("],\"withoutDivision\":").append(country.ek().size()).append('}');
        }
        return leagues.toString();
    }
}
