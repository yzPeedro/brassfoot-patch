import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.Opcodes;
import jdk.internal.org.objectweb.asm.tree.AbstractInsnNode;
import jdk.internal.org.objectweb.asm.tree.ClassNode;
import jdk.internal.org.objectweb.asm.tree.FieldInsnNode;
import jdk.internal.org.objectweb.asm.tree.InsnList;
import jdk.internal.org.objectweb.asm.tree.InsnNode;
import jdk.internal.org.objectweb.asm.tree.MethodInsnNode;
import jdk.internal.org.objectweb.asm.tree.MethodNode;
import jdk.internal.org.objectweb.asm.tree.VarInsnNode;

public final class SuperWorldTransformer {
    private static final String RUNTIME = "mega/SuperWorld";
    private static final List<String> DIVISION_TABLES = Arrays.asList("qg", "sC", "sD");
    private static final String NESTED_DIVISION_TABLE = "qK";

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("game.jar output-dir");
        Path output = Paths.get(args[1]);
        Map<String, Integer> report = new TreeMap<String, Integer>();
        try (ZipFile jar = new ZipFile(args[0])) {
            Enumeration<? extends ZipEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (!entry.getName().endsWith(".class")) continue;
                byte[] original;
                try (InputStream stream = jar.getInputStream(entry)) {
                    original = stream.readAllBytes();
                }
                ClassNode node = new ClassNode();
                new ClassReader(original).accept(node, 0);
                int changes = 0;
                for (MethodNode method : node.methods) {
                    changes += clampDivisionIndexes(method);
                    if ("best/aq".equals(node.name) && "<clinit>".equals(method.name)) {
                        changes += padDivisionTables(method);
                    }
                    if ("best/Z".equals(node.name) && "Ar".equals(method.name) && "()V".equals(method.desc)) {
                        changes += divisionLoopLimit(method);
                    }
                }
                if (changes == 0) continue;
                ClassWriter writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
                node.accept(writer);
                Path target = output.resolve(entry.getName());
                Files.createDirectories(target.getParent());
                Files.write(target, writer.toByteArray());
                report.put(entry.getName(), changes);
            }
        }
        if (!report.containsKey("best/Z.class")) throw new IllegalStateException("best/Z.Ar sem limite de divisões");
        if (report.getOrDefault("best/aq.class", 0) != DIVISION_TABLES.size() + 1) throw new IllegalStateException("tabelas por divisão de best/aq incompletas");
        for (Map.Entry<String, Integer> item : report.entrySet()) {
            System.out.println(item.getKey() + "\t" + item.getValue());
        }
    }

    private static int clampDivisionIndexes(MethodNode method) {
        int changes = 0;
        for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
            if (insn.getOpcode() != Opcodes.INVOKEVIRTUAL) continue;
            MethodInsnNode call = (MethodInsnNode) insn;
            if (!"best/ah".equals(call.owner) || !"getDivisao".equals(call.name) || !"()I".equals(call.desc)) continue;
            AbstractInsnNode next = call.getNext();
            while (next != null && next.getOpcode() < 0) next = next.getNext();
            if (next == null || (next.getOpcode() != Opcodes.IALOAD && next.getOpcode() != Opcodes.AALOAD)) continue;
            method.instructions.insert(call, new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "tableDivision", "(I)I", false));
            changes++;
        }
        return changes;
    }

    private static int padDivisionTables(MethodNode method) {
        int changes = 0;
        for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
            if (insn.getOpcode() != Opcodes.PUTSTATIC) continue;
            FieldInsnNode field = (FieldInsnNode) insn;
            if (!"best/aq".equals(field.owner)) continue;
            if (DIVISION_TABLES.contains(field.name)) {
                InsnList pad = new InsnList();
                pad.add(new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "padDivisions", "(Ljava/lang/Object;)Ljava/lang/Object;", false));
                pad.add(new jdk.internal.org.objectweb.asm.tree.TypeInsnNode(Opcodes.CHECKCAST, field.desc));
                method.instructions.insertBefore(field, pad);
                changes++;
            } else if (NESTED_DIVISION_TABLE.equals(field.name)) {
                InsnList pad = new InsnList();
                pad.add(new FieldInsnNode(Opcodes.GETSTATIC, "best/aq", field.name, field.desc));
                pad.add(new InsnNode(Opcodes.ICONST_1));
                pad.add(new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "padDivisionsAt", "([Ljava/lang/Object;I)V", false));
                method.instructions.insert(field, pad);
                changes++;
            }
        }
        return changes;
    }

    private static int divisionLoopLimit(MethodNode method) {
        for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
            if (insn.getOpcode() != Opcodes.ICONST_4) continue;
            AbstractInsnNode next = insn.getNext();
            if (next == null || next.getOpcode() != Opcodes.ISTORE) continue;
            InsnList replacement = new InsnList();
            replacement.add(new VarInsnNode(Opcodes.ALOAD, 0));
            replacement.add(new FieldInsnNode(Opcodes.GETFIELD, "best/Z", "pais", "I"));
            replacement.add(new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "maxDivisions", "(I)I", false));
            method.instructions.insertBefore(insn, replacement);
            method.instructions.remove(insn);
            return 1;
        }
        throw new IllegalStateException("constante 4 do laço de divisões não encontrada");
    }
}
