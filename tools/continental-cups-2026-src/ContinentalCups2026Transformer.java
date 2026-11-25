import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.Opcodes;
import jdk.internal.org.objectweb.asm.tree.AbstractInsnNode;
import jdk.internal.org.objectweb.asm.tree.ClassNode;
import jdk.internal.org.objectweb.asm.tree.FieldInsnNode;
import jdk.internal.org.objectweb.asm.tree.InsnList;
import jdk.internal.org.objectweb.asm.tree.InsnNode;
import jdk.internal.org.objectweb.asm.tree.LdcInsnNode;
import jdk.internal.org.objectweb.asm.tree.MethodInsnNode;
import jdk.internal.org.objectweb.asm.tree.MethodNode;
import jdk.internal.org.objectweb.asm.tree.VarInsnNode;

/** Injects a first-season participant seed without replacing competition logic. */
public final class ContinentalCups2026Transformer {
    private static final String HELPER = "best/CupParticipants2026";
    private static final String QUOTAS = "(Ljava/util/ArrayList;Ljava/util/ArrayList;Ljava/util/ArrayList;Z)V";

    private ContinentalCups2026Transformer() {}

    public static void main(String[] args) throws Exception {
        if (args.length < 4) throw new IllegalArgumentException("MODE ORIGINAL OUTPUT METHOD [KEY FIELD1 FIELD2]");
        ClassReader reader = new ClassReader(Files.readAllBytes(Path.of(args[1])));
        ClassNode owner = new ClassNode();
        reader.accept(owner, 0);
        MethodNode method = unique(owner.methods, args[3]);
        if ("libertadores".equals(args[0])) {
            int fixed = 0;
            for (AbstractInsnNode instruction : method.instructions.toArray()) {
                if (!(instruction instanceof MethodInsnNode call)) continue;
                if (call.getOpcode() == Opcodes.INVOKESTATIC && HELPER.equals(call.owner)
                        && "prepareLibertadores".equals(call.name)) {
                    method.instructions.remove(call);
                } else if (call.getOpcode() == Opcodes.INVOKEVIRTUAL && "best/f".equals(call.owner)
                        && "isGruposIntPadrao".equals(call.name) && "()Z".equals(call.desc)) {
                    InsnList off = new InsnList();
                    off.add(new InsnNode(Opcodes.POP));
                    off.add(new InsnNode(Opcodes.ICONST_0));
                    method.instructions.insert(call, off);
                    method.instructions.remove(call);
                    fixed++;
                }
            }
            if (fixed != 1) throw new IllegalArgumentException("fixed groups check absent");
            String[] names = {"libertadoresHolders", "libertadoresDirect", "libertadoresQualifying"};
            int quotas = 0;
            for (AbstractInsnNode instruction : unique(owner.methods, "ys").instructions.toArray()) {
                if (instruction instanceof MethodInsnNode call && call.getOpcode() == Opcodes.INVOKESTATIC
                        && "f/b".equals(call.owner) && "a".equals(call.name) && QUOTAS.equals(call.desc)) {
                    if (quotas == names.length) throw new IllegalArgumentException("unexpected quota call");
                    call.owner = HELPER;
                    call.name = names[quotas++];
                }
            }
            if (quotas != names.length) throw new IllegalArgumentException("quota calls absent");
        } else if ("priority".equals(args[0])) {
            InsnList call = new InsnList();
            call.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "prioritize", "()V", false));
            for (AbstractInsnNode instruction : method.instructions.toArray()) {
                if (instruction instanceof MethodInsnNode existing && HELPER.equals(existing.owner)) {
                    throw new IllegalArgumentException("priority already applied");
                }
            }
            method.instructions.insert(call);
        } else if ("seed-after-clear".equals(args[0]) && args.length == 7) {
            AbstractInsnNode lastClear = null;
            for (AbstractInsnNode instruction : method.instructions) {
                if (instruction instanceof MethodInsnNode call
                        && call.getOpcode() == Opcodes.INVOKEVIRTUAL
                        && "java/util/ArrayList".equals(call.owner)
                        && "clear".equals(call.name) && "()V".equals(call.desc)) {
                    lastClear = instruction;
                }
            }
            if (lastClear == null) throw new IllegalArgumentException("clear anchor absent");
            InsnList seed = new InsnList();
            seed.add(new LdcInsnNode(args[4]));
            seed.add(new VarInsnNode(Opcodes.ALOAD, 0));
            seed.add(new FieldInsnNode(Opcodes.GETFIELD, owner.name, args[5], "Ljava/util/ArrayList;"));
            if ("-".equals(args[6])) {
                seed.add(new InsnNode(Opcodes.ACONST_NULL));
            } else {
                seed.add(new VarInsnNode(Opcodes.ALOAD, 0));
                seed.add(new FieldInsnNode(Opcodes.GETFIELD, owner.name, args[6], "Ljava/util/ArrayList;"));
            }
            seed.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "best/CupParticipants2026", "seed",
                    "(Ljava/lang/String;Ljava/util/ArrayList;Ljava/util/ArrayList;)V", false));
            method.instructions.insert(lastClear, seed);
        } else {
            throw new IllegalArgumentException("unsupported transformer arguments");
        }
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        owner.accept(writer);
        Files.write(Path.of(args[2]), writer.toByteArray());
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
