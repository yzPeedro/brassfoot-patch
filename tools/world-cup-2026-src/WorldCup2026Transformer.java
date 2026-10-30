import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.tree.ClassNode;
import jdk.internal.org.objectweb.asm.tree.MethodNode;

/** Replaces one verified method with a compile-only template method of the same name and descriptor. */
public final class WorldCup2026Transformer {
    private WorldCup2026Transformer() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 5 || !"replace-method".equals(args[0])) {
            throw new IllegalArgumentException("replace-method ORIGINAL TEMPLATE METHOD OUTPUT");
        }
        ClassReader originalReader = new ClassReader(Files.readAllBytes(Path.of(args[1])));
        ClassNode original = new ClassNode();
        originalReader.accept(original, 0);
        ClassNode template = new ClassNode();
        new ClassReader(Files.readAllBytes(Path.of(args[2]))).accept(template, 0);
        String methodName = args[3];
        MethodNode replacement = unique(template.methods, methodName);
        MethodNode current = unique(original.methods, methodName);
        replacement.access = current.access;
        int index = original.methods.indexOf(current);
        original.methods.set(index, replacement);
        ClassWriter writer = new ClassWriter(originalReader, ClassWriter.COMPUTE_MAXS);
        original.accept(writer);
        Files.write(Path.of(args[4]), writer.toByteArray());
    }

    private static MethodNode unique(List<MethodNode> methods, String name) {
        MethodNode found = null;
        for (MethodNode method : methods) {
            if (name.equals(method.name)) {
                if (found != null) throw new IllegalArgumentException("ambiguous method " + name);
                found = method;
            }
        }
        if (found == null) throw new IllegalArgumentException("missing method " + name);
        return found;
    }
}
