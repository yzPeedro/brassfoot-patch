package mega.lab;

import best.O;
import best.Z;
import best.ah;
import f.B;
import f.s;
import java.io.PrintStream;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
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
        PrintStream console = System.out;
        System.setOut(new PrintStream(new FileOutputStream(output + ".stdout.log"), true, "UTF-8"));
        Runtime runtime = Runtime.getRuntime();
        long started = System.nanoTime();
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.vH();
        best.p.dd();
        long prepared = System.nanoTime();
        List<Integer> selected = new ArrayList<Integer>();
        StringBuilder playable = new StringBuilder();
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
        System.gc();
        long heapBefore = runtime.totalMemory() - runtime.freeMemory();
        best.p.dg();
        long created = System.nanoTime();
        System.gc();
        long heapAfter = runtime.totalMemory() - runtime.freeMemory();
        StringBuilder leagues = new StringBuilder();
        for (Object item : c.a.SR.N()) {
            Z country = (Z) item;
            if (leagues.length() > 0) {
                leagues.append(",\n    ");
            }
            leagues.append("{\"country\":").append(country.jc()).append(",\"divisions\":[");
            ArrayList divisions = country.eb();
            for (int i = 0; i < divisions.size(); i++) {
                s table = ((B) divisions.get(i)).yi();
                if (i > 0) {
                    leagues.append(',');
                }
                leagues.append(table.yK().size());
            }
            leagues.append("],\"withoutDivision\":").append(country.ek().size()).append('}');
        }
        int players = 0;
        for (Object item : c.a.SR.P()) {
            players += ((ah) item).kc().size();
        }
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
                + ",\n  \"playersInWorld\": " + players
                + ",\n  \"playableCountries\": [" + playable + "]"
                + ",\n  \"selectedCountries\": " + selected
                + ",\n  \"internationalClubs\": " + intClubs
                + ",\n  \"prepareMillis\": " + (prepared - started) / 1000000L
                + ",\n  \"createMillis\": " + (created - prepared) / 1000000L
                + ",\n  \"heapBeforeCreateBytes\": " + heapBefore
                + ",\n  \"heapAfterCreateBytes\": " + heapAfter
                + ",\n  \"maxHeapBytes\": " + runtime.maxMemory()
                + ",\n  \"leagues\": [\n    " + leagues + "\n  ]\n}\n");
        writer.close();
        console.println("ok " + output);
        System.exit(0);
    }
}
