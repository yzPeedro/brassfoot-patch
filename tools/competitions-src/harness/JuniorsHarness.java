import best.F;
import best.O;
import best.ah;
import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class JuniorsHarness {
    private static PrintStream out;
    private static int failures;

    private static void check(boolean condition, String label) {
        out.println((condition ? "OK   " : "FALHA ") + label);
        if (!condition) failures++;
    }

    private static ah team(String file) {
        for (Object item : c.a.SR.P()) if (file.equals(((ah) item).jY())) return (ah) item;
        return null;
    }

    private static Map<String, Integer> expected(File list) throws Exception {
        Map<String, Integer> result = new HashMap<String, Integer>();
        for (String line : Files.readAllLines(list.toPath(), StandardCharsets.UTF_8)) {
            String[] cols = line.split("\t");
            if (cols.length == 2) result.put(cols[0], Integer.valueOf(cols[1]));
        }
        return result;
    }

    private static Set<String> names(List players) {
        Set<String> result = new HashSet<String>();
        for (Object item : players) result.add(((F) item).getNome() + "|" + ((F) item).hashCode());
        return result;
    }

    private static Set<Object> identities(List players) {
        return new HashSet<Object>(players);
    }

    private static void season() {
        int steps = 0;
        c.a.SR.V();
        while (!c.a.SR.bk && steps < 6000) {
            c.a.SR.V();
            steps++;
        }
        check(c.a.SR.bk, "temporada " + (c.a.SR.op() + c.a.SR.H() - 1) + " terminou em " + steps + " passos");
    }

    private static boolean load(String name) {
        try {
            com.esotericsoftware.kryo.Kryo kryo = new com.esotericsoftware.kryo.Kryo();
            kryo.setRegistrationRequired(false);
            com.esotericsoftware.kryo.io.Input input = new com.esotericsoftware.kryo.io.Input(
                    new java.io.FileInputStream(System.getProperty("user.dir") + "/sav/" + name + ".s22"));
            c.a.SR = (best.f) kryo.readClassAndObject(input);
            c.a.afQ = (best.ay) kryo.readClassAndObject(input);
            input.close();
            c.a.SR.bs = false;
            c.a.SR.G();
            return true;
        } catch (Exception error) {
            error.printStackTrace(out);
            return false;
        }
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", CompHarness.MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        Map<String, Integer> expected = expected(new File(args[1]));
        int seasons = Integer.parseInt(args[2]);
        boolean real = new File(game, "juniores-reais.json").isFile();
        System.setProperty("user.dir", game.getPath());
        out = System.out;
        System.setOut(new PrintStream(new FileOutputStream(new File(game, "harness-game-stdout.log")), true, "UTF-8"));
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
        for (Object item : c.a.SR.bF) {
            O option = (O) item;
            option.v(option.getPais() == 29);
        }
        c.a.SR.I(2026);
        c.a.SR.setJogaEstadual(true);
        c.a.SR.setJogaIntClubes(false);
        c.a.SR.setJogaSelecoesAll(false);
        best.p.dg();
        best.p.dh();
        c.a.SR.az();
        out.println("modo " + (real ? "juniores reais" : "original") + "; juniores na carreira: " + c.a.SR.Q().size());
        int largest = 0;
        String largestFile = "";
        for (Map.Entry<String, Integer> entry : expected.entrySet()) {
            ah club = team(entry.getKey());
            int have = club == null ? -1 : club.ky().size();
            if (real) check(have == entry.getValue(), entry.getKey() + ": " + have + " juniores (arquivo " + entry.getValue() + ")");
            if (have > largest) {
                largest = have;
                largestFile = entry.getKey();
            }
        }
        out.println("maior base: " + largestFile + " com " + largest);
        Set<Object> initial = identities(c.a.SR.Q());
        int bad = 0;
        for (Object item : c.a.SR.Q()) {
            int age = ((F) item).getIdade();
            if (real && (age < 18 || age > 20)) bad++;
        }
        if (real) check(bad == 0, "nenhum junior fora de 18 a 20 anos na criacao (" + bad + ")");
        Map<Object, Integer> ages = new HashMap<Object, Integer>();
        Map<Object, ah> clubs = new HashMap<Object, ah>();
        for (Object item : c.a.SR.Q()) {
            ages.put(item, ((F) item).getIdade());
            clubs.put(item, ((F) item).fg());
        }
        for (int s = 0; s < seasons; s++) {
            season();
            if (s == 0) {
                c.a.ae("juniors-harness");
                int before = c.a.SR.Q().size();
                boolean loaded = load("juniors-harness");
                check(loaded && c.a.SR.Q().size() == before, "save e recarga com " + c.a.SR.Q().size() + " juniores (antes " + before + ")");
                initial = remap(initial);
                Map<Object, Integer> mapped = new HashMap<Object, Integer>();
                for (Map.Entry<Object, Integer> e : ages.entrySet()) {
                    Object again = find((F) e.getKey());
                    if (again != null) mapped.put(again, e.getValue());
                }
                ages = mapped;
            }
            int created = 0;
            int aged = 0;
            for (Object item : c.a.SR.Q()) {
                if (!initial.contains(item)) created++;
                int age = ((F) item).getIdade();
                if (real && age > 20) aged++;
            }
            if (real) {
                check(created == 0, "temporada " + (s + 1) + ": nenhum junior criado (" + created + " novos)");
                check(aged == 0, "temporada " + (s + 1) + ": nenhum junior com 21 anos ou mais na base (" + aged + ")");
            } else {
                out.println("temporada " + (s + 1) + ": modo original gerou " + created + " juniores");
            }
            int promoted = 0;
            int released = 0;
            int lost = 0;
            for (Map.Entry<Object, Integer> e : ages.entrySet()) {
                F player = (F) e.getKey();
                if (c.a.SR.Q().contains(player)) continue;
                if (c.a.SR.O().contains(player)) {
                    if (player.fg() != null) promoted++;
                    else released++;
                } else {
                    lost++;
                }
            }
            out.println("temporada " + (s + 1) + ": saidas da base: " + promoted + " promovidos, " + released + " sem clube, " + lost + " fora das listas");
        }
        out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }

    private static Set<Object> remap(Set<Object> previous) {
        Set<Object> result = new HashSet<Object>();
        for (Object item : previous) {
            Object again = find((F) item);
            if (again != null) result.add(again);
        }
        return result;
    }

    private static Object find(F player) {
        for (Object item : c.a.SR.Q()) {
            F other = (F) item;
            if (other.getNome().equals(player.getNome()) && other.getIdade() == player.getIdade() && other.getPosicao() == player.getPosicao()) return other;
        }
        for (Object item : c.a.SR.O()) {
            F other = (F) item;
            if (other.getNome().equals(player.getNome()) && other.getPosicao() == player.getPosicao()) return other;
        }
        return null;
    }
}
