import best.I;
import best.ah;
import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class HumanCalendarHarness {
    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", CompHarness.MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        String wanted = args[1];
        int startYear = Integer.parseInt(args[2]);
        int days = args.length > 3 ? Integer.parseInt(args[3]) : 0;
        System.setProperty("user.dir", game.getPath());
        PrintStream out = System.out;
        System.setOut(new PrintStream(new FileOutputStream(new File(game, "harness-game-stdout.log")), true, "UTF-8"));
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
        for (Object item : c.a.SR.bF) {
            best.O option = (best.O) item;
            option.v(option.getPais() == 29);
        }
        c.a.SR.I(startYear);
        c.a.SR.setJogaEstadual(true);
        c.a.SR.setJogaIntClubes(true);
        c.a.SR.setJogaSelecoesAll(false);
        best.p.dg();
        ah human = null;
        for (Object item : c.a.SR.o(29).eb()) {
            for (Object team : ((f.B) item).yi().yK()) {
                if (((ah) team).jY().contains(wanted)) human = (ah) team;
            }
        }
        out.println("humano: " + (human == null ? "NAO ENCONTRADO" : human.getNome() + " " + human.jY()));
        if (human == null) System.exit(2);
        human.b("Teste", best.n.H(0));
        if (c.a.SR.isJogaRegionais()) best.p.dh();
        c.a.SR.az();
        dump(out, human, "criacao");
        c.a.SR.setIgnoraLigas(true);
        c.a.SR.setIgnoraEstadual(true);
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd EEE");
        int skipped = 0, shown = 0;
        for (int step = 0; step < days && !c.a.SR.bk; step++) {
            try {
                human.I(true);
                best.a today = (best.a) c.a.SR.R().get(c.a.SR.J());
                I humanMatch = null;
                for (Object item : today.h()) {
                    I match = (I) item;
                    if (match.hc() == human || match.hd() == human) humanMatch = match;
                }
                if (humanMatch != null) {
                    int first = c.a.SR.ao();
                    boolean league = c.a.SR.isIgnoraLigas() && first == 1 && !best.s.dG();
                    boolean regional = first == 10 && !best.s.dH();
                    String competition = humanMatch.ht() == null ? "?" : humanMatch.ht().getNome();
                    String firstName = today.t().isEmpty() ? "-" : ((best.at) today.t().get(0)).getNome();
                    boolean skip = league || regional;
                    if (skip) skipped++; else shown++;
                    out.println((skip ? "PULADO " : "exibido ") + format.format(today.a().getTime()) + " | jogo humano: " + competition
                            + " | 1o campeonato do dia: " + firstName + " (tipo " + first + ")");
                }
                c.a.SR.V();
            } catch (Throwable error) {
                out.println("V() falhou no passo " + step + ": " + error);
                break;
            }
        }
        if (days > 0) {
            out.println("dias com jogo humano: exibidos " + shown + ", pulados " + skipped);
            dump(out, human, "apos " + days + " passos");
        }
        System.exit(0);
    }

    private static void dump(PrintStream out, ah human, String label) {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd EEE");
        Map<String, List<String>> byDate = new HashMap<String, List<String>>();
        out.println("== calendario de " + human.getNome() + " (" + label + ")");
        int total = 0;
        for (Object day : c.a.SR.R()) {
            best.a date = (best.a) day;
            String when = format.format(date.a().getTime());
            for (Object item : date.h()) {
                I match = (I) item;
                if (match.hc() != human && match.hd() != human) continue;
                ah rival = match.hc() == human ? match.hd() : match.hc();
                String competition = match.ht() == null ? "?" : match.ht().getClass().getName() + " " + match.ht().getNome();
                String line = when + " | " + competition + " | " + (match.hc() == human ? "casa" : "fora") + " x "
                        + (rival == null ? "null" : rival.getNome() + " [" + rival.jY() + "] elenco " + rival.kc().size())
                        + " | humano elenco " + human.kc().size() + " | rival humano " + (rival != null && rival.jZ())
                        + " | humano jZ " + human.jZ();
                out.println(line);
                if (!byDate.containsKey(when)) byDate.put(when, new ArrayList<String>());
                byDate.get(when).add(competition);
                total++;
            }
        }
        out.println("total " + total);
        for (Map.Entry<String, List<String>> entry : byDate.entrySet()) {
            if (entry.getValue().size() > 1) out.println("CONFLITO " + entry.getKey() + " " + entry.getValue());
        }
    }
}
