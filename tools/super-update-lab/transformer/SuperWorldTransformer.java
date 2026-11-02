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
    private static final String[][] LOCAL_INDEX_RULES = {
        {"best/Z", "a", "(Ljava/util/ArrayList;Lbest/al;ZZ)V", "10", "3"},
    };

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
                    changes += clampLocalIndexes(node.name, method);
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
        java.util.Set<Integer> divisionLocals = new java.util.HashSet<Integer>();
        java.util.Set<Integer> otherLocals = new java.util.HashSet<Integer>();
        for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
            if (insn.getOpcode() != Opcodes.ISTORE) continue;
            int local = ((VarInsnNode) insn).var;
            if (isDivision(previous(insn))) {
                divisionLocals.add(local);
            } else {
                otherLocals.add(local);
            }
        }
        divisionLocals.removeAll(otherLocals);
        int changes = 0;
        for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
            boolean source = isDivision(insn) || (insn.getOpcode() == Opcodes.ILOAD && divisionLocals.contains(((VarInsnNode) insn).var));
            if (!source) continue;
            AbstractInsnNode next = following(insn);
            if (next == null || (next.getOpcode() != Opcodes.IALOAD && next.getOpcode() != Opcodes.AALOAD
                    && next.getOpcode() != Opcodes.LALOAD)) continue;
            method.instructions.insert(insn, new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "tableDivision", "(I)I", false));
            changes++;
        }
        return changes;
    }

    private static int clampLocalIndexes(String owner, MethodNode method) {
        int changes = 0;
        for (String[] rule : LOCAL_INDEX_RULES) {
            if (!rule[0].equals(owner) || !rule[1].equals(method.name) || !rule[2].equals(method.desc)) continue;
            int local = Integer.parseInt(rule[3]);
            int max = Integer.parseInt(rule[4]);
            int found = 0;
            for (AbstractInsnNode insn = method.instructions.getFirst(); insn != null; insn = insn.getNext()) {
                if (insn.getOpcode() != Opcodes.ILOAD || ((VarInsnNode) insn).var != local) continue;
                AbstractInsnNode next = following(insn);
                if (next == null || next.getOpcode() != Opcodes.AALOAD) continue;
                InsnList clamp = new InsnList();
                clamp.add(new jdk.internal.org.objectweb.asm.tree.LdcInsnNode(max));
                clamp.add(new MethodInsnNode(Opcodes.INVOKESTATIC, RUNTIME, "clampIndex", "(II)I", false));
                method.instructions.insert(insn, clamp);
                found++;
            }
            if (found == 0) throw new IllegalStateException("regra sem efeito: " + String.join(" ", rule));
            changes += found;
        }
        return changes;
    }

    private static boolean isDivision(AbstractInsnNode insn) {
        if (insn == null) return false;
        if (insn.getOpcode() == Opcodes.INVOKEVIRTUAL) {
            MethodInsnNode call = (MethodInsnNode) insn;
            return "best/ah".equals(call.owner) && "getDivisao".equals(call.name) && "()I".equals(call.desc);
        }
        if (insn.getOpcode() == Opcodes.GETFIELD) {
            FieldInsnNode field = (FieldInsnNode) insn;
            return "best/ah".equals(field.owner) && "divisao".equals(field.name);
        }
        return false;
    }

    private static AbstractInsnNode previous(AbstractInsnNode insn) {
        AbstractInsnNode item = insn.getPrevious();
        while (item != null && item.getOpcode() < 0) item = item.getPrevious();
        return item;
    }

    private static AbstractInsnNode following(AbstractInsnNode insn) {
        AbstractInsnNode item = insn.getNext();
        while (item != null && item.getOpcode() < 0) item = item.getNext();
        return item;
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
