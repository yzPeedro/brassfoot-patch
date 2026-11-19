package app;
import est.ArrayLigaEType;
import est.ArrayLigaType;
import est.ConfigEstadualType;
import est.ConfigLigaType;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputFilter;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;

/** Validated read-only analysis and isolated experiments for Brasfoot 22-23 league configurations. */
public final class CompetitionCodec {
    private static final int MAX_INPUT_BYTES = 1024 * 1024;
    private CompetitionCodec() {}

    static Object decode(byte[] data) throws Exception {
        if (data.length < 8 || data.length > MAX_INPUT_BYTES) {
            throw new IOException("Invalid serialized file size: " + data.length);
        }
        try (ObjectInputStream input = new ObjectInputStream(new ByteArrayInputStream(data))) {
            input.setObjectInputFilter(info -> {
                if (info.depth() > 32 || info.references() > 1024
                        || info.arrayLength() > 128 || info.streamBytes() > MAX_INPUT_BYTES) {
                    return ObjectInputFilter.Status.REJECTED;
                }
                Class<?> type = info.serialClass();
                if (type == null) return ObjectInputFilter.Status.UNDECIDED;
                if (type == ArrayLigaType.class || type == ArrayLigaEType.class
                        || type == ConfigLigaType.class || type == ConfigEstadualType.class
                        || type == java.util.ArrayList.class || type == String.class
                        || type == boolean[].class || type == int[].class || type == Object[].class) {
                    return ObjectInputFilter.Status.ALLOWED;
                }
                return ObjectInputFilter.Status.REJECTED;
            });
            Object value = input.readObject();
            if (input.read() != -1) throw new IOException("Unexpected bytes after Java object");
            if (!(value instanceof ArrayLigaType) && !(value instanceof ArrayLigaEType)) {
                throw new IOException("Unexpected configuration root type");
            }
            return value;
        }
    }

    static byte[] encode(Object value) throws IOException {
        ByteArrayOutputStream result = new ByteArrayOutputStream();
        try (ObjectOutputStream output = new ObjectOutputStream(result)) {
            output.writeObject(value);
        }
        return result.toByteArray();
    }

    private static void inspect(Object root) throws IOException {
        if (root instanceof ArrayLigaType national) {
            if (national.a == null || national.a.isEmpty() || national.a.size() > 16) {
                throw new IOException("Unexpected national division count");
            }
            System.out.println("type=national divisions=" + national.a.size());
            for (ConfigLigaType c : national.a) {
                System.out.printf("division=%d name=%s clubs=%d groups=%d country=%d version=%d%n",
                        c.divisao, c.nomeDivisao, c.nTimes, c.nGrupos, c.pais, c.versaoArquivo);
            }
        } else if (root instanceof ArrayLigaEType state) {
            if (state.a == null || state.a.isEmpty() || state.a.size() > 16) {
                throw new IOException("Unexpected state division count");
            }
            System.out.println("type=state divisions=" + state.a.size());
            for (ConfigEstadualType c : state.a) {
                System.out.printf("division=%d stateId=%d formula=%d relegated=%d%n",
                        c.divisao, c.id, c.formula, c.nRebaixados);
            }
        }
    }

    private static void ensureSafeOutput(Path input, Path output, boolean isTrial) throws IOException {
        Path src = input.toAbsolutePath().normalize();
        Path dst = output.toAbsolutePath().normalize();
        if (src.equals(dst)) throw new IOException("Refusing to overwrite input");
        if (isTrial && src.getParent() != null && src.getParent().getParent() != null
                && "conf_ligas_nacionais".equalsIgnoreCase(src.getParent().getFileName().toString())
                && dst.startsWith(src.getParent().getParent())) {
            throw new IOException("Trial output must be outside the game's installation directory");
        }
        if (Files.exists(dst)) throw new IOException("Output already exists: " + dst);
        if (dst.getParent() == null || !Files.isDirectory(dst.getParent())) {
            throw new IOException("Create output folder outside the game before running");
        }
    }

    private static void trialD(Object root, Path input) throws IOException {
        if (!input.getFileName().toString().equalsIgnoreCase("BRA.cfg")) {
            throw new IOException("Trial is restricted to BRA.cfg");
        }
        if (!(root instanceof ArrayLigaType national) || national.a == null || national.a.size() != 4) {
            throw new IOException("Expected four national divisions");
        }
        int[] expected = {20, 20, 20, 64};
        for (int i=0; i<4; i++) {
            ConfigLigaType current = national.a.get(i);
            if (current.divisao != i+1 || current.pais != 29 || current.nTimes != expected[i]
                    || current.versaoArquivo != 22) {
                throw new IOException("Unexpected original division at index " + i);
            }
        }
        ConfigLigaType d = national.a.get(3);
        if (d.nGrupos != 8 || !"Série D".equals(d.nomeDivisao)) {
            throw new IOException("Expected old Série D format (64 clubs, 8 groups)");
        }
        d.nTimes = 96;
        d.nGrupos = 16;
    }

    static String dumpJson(Object root) throws Exception {
        StringBuilder out = new StringBuilder("[");
        java.util.List<?> items = root instanceof ArrayLigaType n ? n.a : ((ArrayLigaEType) root).a;
        for (int i = 0; i < items.size(); i++) {
            Object item = items.get(i);
            if (i > 0) out.append(',');
            out.append('{');
            java.lang.reflect.Field[] fields = item.getClass().getDeclaredFields();
            Arrays.sort(fields, (a, b) -> a.getName().compareTo(b.getName()));
            boolean first = true;
            for (java.lang.reflect.Field f : fields) {
                if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
                f.setAccessible(true);
                Object v = f.get(item);
                if (!first) out.append(',');
                first = false;
                out.append('"').append(f.getName()).append("\":");
                if (v == null) out.append("null");
                else if (v instanceof String str) out.append('"').append(str.replace("\\", "\\\\").replace("\"", "\\\"")).append('"');
                else if (v instanceof boolean[] b) out.append(Arrays.toString(b));
                else if (v instanceof int[] a) out.append(Arrays.toString(a));
                else out.append(v);
            }
            out.append('}');
        }
        return out.append(']').toString();
    }

    static void setField(Object root, String assignment) throws Exception {
        if (assignment.startsWith("count=")) {
            int count = Integer.parseInt(assignment.substring(6));
            java.util.List<?> all = root instanceof ArrayLigaType n ? n.a : ((ArrayLigaEType) root).a;
            if (count < 1 || count > all.size()) throw new IllegalArgumentException("Invalid count: " + count);
            while (all.size() > count) all.remove(all.size() - 1);
            return;
        }
        int dot = assignment.indexOf('.');
        int eq = assignment.indexOf('=');
        if (dot < 1 || eq < dot) throw new IllegalArgumentException("Expected INDEX.field=value: " + assignment);
        int index = Integer.parseInt(assignment.substring(0, dot));
        String name = assignment.substring(dot + 1, eq);
        String value = assignment.substring(eq + 1);
        java.util.List<?> items = root instanceof ArrayLigaType n ? n.a : ((ArrayLigaEType) root).a;
        Object item = items.get(index);
        java.lang.reflect.Field f = item.getClass().getDeclaredField(name);
        f.setAccessible(true);
        Class<?> t = f.getType();
        if (t == int.class) f.setInt(item, Integer.parseInt(value));
        else if (t == boolean.class) f.setBoolean(item, Boolean.parseBoolean(value));
        else if (t == String.class) f.set(item, value);
        else if (t == boolean[].class) {
            String[] parts = value.split(",");
            boolean[] arr = new boolean[parts.length];
            for (int i = 0; i < parts.length; i++) arr[i] = Boolean.parseBoolean(parts[i].trim());
            f.set(item, arr);
        } else throw new IllegalArgumentException("Unsupported field type: " + name);
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 2 && args[0].equals("dump")) {
            Path in = Path.of(args[1]);
            if (!Files.isRegularFile(in) || Files.size(in) > MAX_INPUT_BYTES) throw new IOException("Invalid source");
            System.out.println(dumpJson(decode(Files.readAllBytes(in))));
            return;
        }
        if (args.length >= 4 && args[0].equals("set")) {
            Path in = Path.of(args[1]);
            Path outPath = Path.of(args[2]);
            if (!Files.isRegularFile(in) || Files.size(in) > MAX_INPUT_BYTES) throw new IOException("Invalid source");
            ensureSafeOutput(in, outPath, true);
            Object root = decode(Files.readAllBytes(in));
            for (int i = 3; i < args.length; i++) setField(root, args[i]);
            byte[] encoded = encode(root);
            Object check = decode(encoded);
            if (!dumpJson(check).equals(dumpJson(root))) throw new IOException("Verification failed");
            Files.write(outPath, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            System.out.println(dumpJson(check));
            return;
        }
        if (args.length < 2 || args.length > 3
                || (!args[0].equals("inspect") && !args[0].equals("roundtrip")
                    && !args[0].equals("trial-serie-d-96"))) {
            throw new IllegalArgumentException("Usage: CompetitionCodec inspect INPUT | roundtrip INPUT OUTPUT | trial-serie-d-96 INPUT OUTPUT");
        }
        String operation = args[0];
        if ((operation.equals("inspect") && args.length != 2)
                || (!operation.equals("inspect") && args.length != 3)) {
            throw new IllegalArgumentException("Wrong number of arguments");
        }
        Path input = Path.of(args[1]);
        if (!Files.isRegularFile(input) || Files.size(input) > MAX_INPUT_BYTES) {
            throw new IOException("Invalid or oversized source file");
        }
        byte[] original = Files.readAllBytes(input);
        Object decoded = decode(original);
        inspect(decoded);
        if (operation.equals("inspect")) return;
        Path output = Path.of(args[2]);
        ensureSafeOutput(input, output, operation.equals("trial-serie-d-96"));
        if (operation.equals("trial-serie-d-96")) trialD(decoded, input);
        byte[] encoded = encode(decoded);
        if (operation.equals("roundtrip") && !Arrays.equals(original, encoded)) {
            throw new IOException("Byte-exact roundtrip failed");
        }
        if (operation.equals("trial-serie-d-96")) {
            Object trial = decode(encoded);
            if (!(trial instanceof ArrayLigaType national) || national.a.get(3).nTimes != 96
                    || national.a.get(3).nGrupos != 16) {
                throw new IOException("Trial serialization failed verification");
            }
            if (encoded.length != original.length) throw new IOException("Unexpected serialized size change");
            int changes = 0;
            for (int i=0; i<original.length; i++) if (original[i] != encoded[i]) changes++;
            if (changes != 2) throw new IOException("Unexpected serialized byte changes: " + changes);
        }
        Files.write(output, encoded, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        System.out.println("Verified output generated outside the game: " + output);
        if (operation.equals("trial-serie-d-96")) {
            System.out.println("EXPERIMENTAL ONLY: NOT tested in Brasfoot. DO NOT install in original game.");
        }
    }
}
