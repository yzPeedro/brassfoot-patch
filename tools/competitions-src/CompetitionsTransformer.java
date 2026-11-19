import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.Label;
import jdk.internal.org.objectweb.asm.Opcodes;
import jdk.internal.org.objectweb.asm.tree.AbstractInsnNode;
import jdk.internal.org.objectweb.asm.tree.ClassNode;
import jdk.internal.org.objectweb.asm.tree.InsnList;
import jdk.internal.org.objectweb.asm.tree.InsnNode;
import jdk.internal.org.objectweb.asm.tree.IntInsnNode;
import jdk.internal.org.objectweb.asm.tree.JumpInsnNode;
import jdk.internal.org.objectweb.asm.tree.LabelNode;
import jdk.internal.org.objectweb.asm.tree.MethodInsnNode;
import jdk.internal.org.objectweb.asm.tree.MethodNode;
import jdk.internal.org.objectweb.asm.tree.VarInsnNode;

public final class CompetitionsTransformer {
    private static final String HELPER = "best/CompBrasil2026";

    private CompetitionsTransformer() {
    }

    private static MethodNode method(ClassNode owner, String name, String desc) {
        MethodNode found = null;
        for (MethodNode candidate : owner.methods) {
            if (candidate.name.equals(name) && candidate.desc.equals(desc)) {
                if (found != null) throw new IllegalStateException("ambiguous " + name + desc);
                found = candidate;
            }
        }
        if (found == null) throw new IllegalStateException("missing " + name + desc);
        return found;
    }

    private static void requireUnpatched(MethodNode method) {
        for (AbstractInsnNode node : method.instructions) {
            if (node instanceof MethodInsnNode call && HELPER.equals(call.owner)) {
                throw new IllegalStateException("already patched: " + method.name);
            }
        }
    }

    private static boolean pairing(ClassNode owner) {
        MethodNode target = method(owner, "b", "(Lf/z;Ljava/util/ArrayList;IZIIIZ)V");
        requireUnpatched(target);
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 1));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 2));
        hook.add(new VarInsnNode(Opcodes.ILOAD, 3));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "pairing",
                "(Lf/G;Lf/z;Ljava/util/ArrayList;I)V", false));
        target.instructions.insert(hook);
        return false;
    }

    private static boolean participants(ClassNode owner) {
        MethodNode target = method(owner, "Q", "(I)Ljava/util/ArrayList;");
        requireUnpatched(target);
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ILOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "serieD", "(I)Ljava/util/ArrayList;", false));
        hook.add(new InsnNode(Opcodes.DUP));
        hook.add(new JumpInsnNode(Opcodes.IFNULL, original));
        hook.add(new InsnNode(Opcodes.ARETURN));
        hook.add(original);
        hook.add(new InsnNode(Opcodes.POP));
        target.instructions.insert(hook);
        return true;
    }

    private static boolean promotion(ClassNode owner) {
        MethodNode target = method(owner, "ee", "()V");
        requireUnpatched(target);
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "promotion", "(Lbest/Z;)Z", false));
        hook.add(new JumpInsnNode(Opcodes.IFEQ, original));
        hook.add(new InsnNode(Opcodes.RETURN));
        hook.add(original);
        target.instructions.insert(hook);
        return true;
    }

    private static boolean divisionOrder(ClassNode owner) {
        MethodNode target = method(owner, "Ar", "()V");
        AbstractInsnNode anchor = null;
        for (AbstractInsnNode node : target.instructions) {
            if (node instanceof MethodInsnNode call && "java/util/Collections".equals(call.owner)
                    && "sort".equals(call.name) && node.getPrevious() instanceof jdk.internal.org.objectweb.asm.tree.FieldInsnNode field
                    && "cN".equals(field.name)) {
                if (anchor != null) throw new IllegalStateException("ambiguous sort anchor");
                anchor = node;
            }
        }
        if (anchor == null) throw new IllegalStateException("sort anchor absent");
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 1));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "divisionOrder",
                "(Ljava/util/ArrayList;Lbest/Z;)V", false));
        target.instructions.insert(anchor, hook);
        return false;
    }

    private static boolean resetRounds(ClassNode owner) {
        MethodNode target = method(owner, "aN", "(Z)V");
        int returns = 0;
        for (AbstractInsnNode node : target.instructions.toArray()) {
            if (node.getOpcode() == Opcodes.RETURN) {
                InsnList call = new InsnList();
                call.add(new VarInsnNode(Opcodes.ALOAD, 0));
                call.add(new MethodInsnNode(Opcodes.INVOKEVIRTUAL, owner.name, "yH", "()V", false));
                target.instructions.insertBefore(node, call);
                returns++;
            }
        }
        if (returns == 0) throw new IllegalStateException("aN without return");
        return true;
    }

    private static boolean afterTie(ClassNode owner) {
        MethodNode target = method(owner, "b", "(ZZ)V");
        requireUnpatched(target);
        int returns = 0;
        for (AbstractInsnNode node : target.instructions.toArray()) {
            if (node.getOpcode() == Opcodes.RETURN) {
                InsnList call = new InsnList();
                call.add(new VarInsnNode(Opcodes.ALOAD, 0));
                call.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "afterTie", "(Lf/G;)V", false));
                target.instructions.insertBefore(node, call);
                returns++;
            }
        }
        if (returns == 0) throw new IllegalStateException("b(ZZ) without return");
        return true;
    }

    private static boolean copaStart(ClassNode owner) {
        int patched = 0;
        for (String name : new String[]{"a", "b"}) {
            MethodNode target = method(owner, name, "(Lf/f;Ljava/util/ArrayList;[Z)V");
            requireUnpatched(target);
            LabelNode original = new LabelNode(new Label());
            InsnList hook = new InsnList();
            hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
            hook.add(new VarInsnNode(Opcodes.ALOAD, 2));
            hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "copa", "(Lf/f;Ljava/util/ArrayList;)Z", false));
            hook.add(new JumpInsnNode(Opcodes.IFEQ, original));
            hook.add(new InsnNode(Opcodes.RETURN));
            hook.add(original);
            target.instructions.insert(hook);
            patched++;
        }
        return patched == 2;
    }

    private static boolean copaNames(ClassNode owner) {
        MethodNode target = method(owner, "b", "(Lbest/L;)[Ljava/lang/String;");
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "copaNames", "(Lf/f;)[Ljava/lang/String;", false));
        hook.add(new InsnNode(Opcodes.DUP));
        hook.add(new JumpInsnNode(Opcodes.IFNULL, original));
        hook.add(new InsnNode(Opcodes.ARETURN));
        hook.add(original);
        hook.add(new InsnNode(Opcodes.POP));
        target.instructions.insert(hook);
        return true;
    }

    private static boolean mainPhase(ClassNode owner) {
        MethodNode target = method(owner, "mB", "()[Lbest/L;");
        requireUnpatched(target);
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "mainPhase", "(Lf/B;)[Lbest/L;", false));
        hook.add(new InsnNode(Opcodes.DUP));
        hook.add(new JumpInsnNode(Opcodes.IFNULL, original));
        hook.add(new InsnNode(Opcodes.ARETURN));
        hook.add(original);
        hook.add(new InsnNode(Opcodes.POP));
        target.instructions.insert(hook);
        return true;
    }

    private static boolean supercopa(ClassNode owner) {
        MethodNode target = method(owner, "Ab", "()V");
        requireUnpatched(target);
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "supercopa", "(Lbest/at;)Z", false));
        hook.add(new JumpInsnNode(Opcodes.IFEQ, original));
        hook.add(new InsnNode(Opcodes.RETURN));
        hook.add(original);
        target.instructions.insert(hook);
        return true;
    }

    private static boolean beforeReturns(ClassNode owner, String name, String desc, InsnList template) {
        MethodNode target = method(owner, name, desc);
        for (AbstractInsnNode node : target.instructions) {
            if (node instanceof MethodInsnNode call && "mega/SetupPanels".equals(call.owner)) {
                throw new IllegalStateException("already patched: " + name);
            }
        }
        int returns = 0;
        for (AbstractInsnNode node : target.instructions.toArray()) {
            if (node.getOpcode() == Opcodes.RETURN) {
                InsnList copy = new InsnList();
                for (AbstractInsnNode item : template) copy.add(item.clone(null));
                target.instructions.insertBefore(node, copy);
                returns++;
            }
        }
        if (returns == 0) throw new IllegalStateException(name + " without return");
        return true;
    }

    private static boolean setupInstall(ClassNode owner) {
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "mega/SetupPanels", "install", "(La/hU;)V", false));
        return beforeReturns(owner, "<init>", "(Ljavax/swing/JFrame;)V", hook);
    }

    private static boolean countryFilter(ClassNode owner) {
        InsnList hook = new InsnList();
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "mega/SetupPanels", "filterCountries", "()V", false));
        return beforeReturns(owner, "dd", "()V", hook);
    }

    private static boolean playoffStart(ClassNode owner) {
        MethodNode target = method(owner, "BQ", "()V");
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "playoffStart", "(Lf/B;)Z", false));
        hook.add(new JumpInsnNode(Opcodes.IFEQ, original));
        hook.add(new InsnNode(Opcodes.RETURN));
        hook.add(original);
        target.instructions.insert(hook);
        return true;
    }

    private static boolean resort(ClassNode owner) {
        MethodNode target = method(owner, "pO", "()V");
        AbstractInsnNode anchor = null;
        for (AbstractInsnNode node : target.instructions) {
            if (node instanceof MethodInsnNode call && "java/util/Collections".equals(call.owner) && "sort".equals(call.name)
                    && node.getPrevious() instanceof jdk.internal.org.objectweb.asm.tree.FieldInsnNode field
                    && "abn".equals(field.name) && field.getPrevious() instanceof jdk.internal.org.objectweb.asm.tree.FieldInsnNode list
                    && "Zb".equals(list.name)) {
                if (anchor != null) throw new IllegalStateException("ambiguous Zb sort");
                anchor = node;
            }
        }
        if (anchor == null) throw new IllegalStateException("Zb sort absent");
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, HELPER, "resort", "(Lf/s;)V", false));
        target.instructions.insert(anchor, hook);
        return false;
    }

    private static boolean estadualDivision(ClassNode owner) {
        MethodNode target = method(owner, "dY", "()V");
        AbstractInsnNode anchor = null;
        for (AbstractInsnNode node : target.instructions) {
            if (node.getOpcode() == Opcodes.NEW && "f/s".equals(((jdk.internal.org.objectweb.asm.tree.TypeInsnNode) node).desc)) {
                if (anchor != null) throw new IllegalStateException("ambiguous f/s creation");
                anchor = node;
            }
        }
        if (anchor == null) throw new IllegalStateException("f/s creation absent");
        AbstractInsnNode first = anchor.getNext().getNext();
        AbstractInsnNode second = first.getNext();
        if (!(first instanceof VarInsnNode options) || options.var != 9 || !(second instanceof VarInsnNode list) || list.var != 7) {
            throw new IllegalStateException("unexpected f/s arguments");
        }
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 9));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 7));
        hook.add(new VarInsnNode(Opcodes.ALOAD, 14));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "best/CompEstaduais", "division",
                "(Lbest/w;Lest/LoadLigaOptions;Ljava/util/ArrayList;Lf/o;)V", false));
        target.instructions.insertBefore(anchor, hook);
        return true;
    }

    private static boolean estadualKnockout(ClassNode owner) {
        MethodNode target = method(owner, "yP", "()V");
        LabelNode original = new LabelNode(new Label());
        InsnList hook = new InsnList();
        hook.add(new VarInsnNode(Opcodes.ALOAD, 0));
        hook.add(new MethodInsnNode(Opcodes.INVOKESTATIC, "best/CompEstaduais", "knockout", "(Lf/s;)Z", false));
        hook.add(new JumpInsnNode(Opcodes.IFEQ, original));
        hook.add(new InsnNode(Opcodes.RETURN));
        hook.add(original);
        target.instructions.insert(hook);
        return true;
    }

    private static boolean singleRoundSerieC(ClassNode owner) {
        MethodNode target = method(owner, "a", "(Ljava/util/ArrayList;ZZLjava/util/ArrayList;)V");
        int changed = 0;
        for (AbstractInsnNode node : target.instructions) {
            if (node instanceof IntInsnNode push && push.getOpcode() == Opcodes.BIPUSH && push.operand == 20
                    && push.getPrevious() instanceof MethodInsnNode size && "size".equals(size.name)
                    && push.getNext() instanceof JumpInsnNode jump && jump.getOpcode() == Opcodes.IF_ICMPNE) {
                AbstractInsnNode after = jump.getNext();
                boolean nearSerieC = false;
                for (int i = 0; i < 12 && after != null; i++, after = after.getNext()) {
                    if (after instanceof IntInsnNode code
                            && code.getOpcode() == Opcodes.SIPUSH && code.operand == 1020) {
                        nearSerieC = true;
                    }
                }
                if (nearSerieC) {
                    jump.setOpcode(Opcodes.IF_ICMPLT);
                    changed++;
                }
            }
        }
        if (changed != 1) throw new IllegalStateException("Serie C anchor count " + changed);
        return false;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("MODE INPUT OUTPUT GAME_JAR");
        byte[] input = Files.readAllBytes(Path.of(args[1]));
        ClassReader reader = new ClassReader(input);
        ClassNode owner = new ClassNode();
        reader.accept(owner, 0);
        boolean frames;
        switch (args[0]) {
            case "pairing": frames = pairing(owner); break;
            case "participants": frames = participants(owner); break;
            case "promotion": frames = promotion(owner); break;
            case "reset-rounds": frames = resetRounds(owner); break;
            case "after-tie": frames = afterTie(owner); break;
            case "copa-start": frames = copaStart(owner); break;
            case "copa-names": frames = copaNames(owner); break;
            case "main-phase": frames = mainPhase(owner); break;
            case "supercopa": frames = supercopa(owner); break;
            case "setup-install": frames = setupInstall(owner); break;
            case "country-filter": frames = countryFilter(owner); break;
            case "playoff-start": frames = playoffStart(owner); break;
            case "resort": frames = resort(owner); break;
            case "estadual-division": frames = estadualDivision(owner); break;
            case "estadual-knockout": frames = estadualKnockout(owner); break;
            case "division-order": frames = divisionOrder(owner); break;
            case "serie-c-rounds": frames = singleRoundSerieC(owner); break;
            default: throw new IllegalArgumentException("unknown mode " + args[0]);
        }
        final URLClassLoader loader = new URLClassLoader(new URL[]{Path.of(args[3]).toUri().toURL()}, null);
        ClassWriter writer = new ClassWriter(frames ? ClassWriter.COMPUTE_FRAMES : ClassWriter.COMPUTE_MAXS) {
            @Override
            protected String getCommonSuperClass(String a, String b) {
                try {
                    Class<?> first = Class.forName(a.replace('/', '.'), false, loader);
                    Class<?> second = Class.forName(b.replace('/', '.'), false, loader);
                    if (first.isAssignableFrom(second)) return a;
                    if (second.isAssignableFrom(first)) return b;
                    if (first.isInterface() || second.isInterface()) return "java/lang/Object";
                    do {
                        first = first.getSuperclass();
                    } while (!first.isAssignableFrom(second));
                    return first.getName().replace('.', '/');
                } catch (ClassNotFoundException error) {
                    throw new IllegalStateException(error);
                }
            }
        };
        owner.accept(writer);
        Files.write(Path.of(args[2]), writer.toByteArray());
    }
}
