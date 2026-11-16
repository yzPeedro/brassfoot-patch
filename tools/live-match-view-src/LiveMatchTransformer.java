import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassVisitor;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.MethodVisitor;
import jdk.internal.org.objectweb.asm.Opcodes;

public final class LiveMatchTransformer {
    private static final Map<String, String> STAT_GETTERS = new HashMap<String, String>();
    static {
        STAT_GETTERS.put("ha()Ljava/lang/String;", "statHa");
        STAT_GETTERS.put("hz()[I", "statHz");
        STAT_GETTERS.put("hA()[I", "statHA");
        STAT_GETTERS.put("hZ()[I", "statHZ");
        STAT_GETTERS.put("ia()[I", "statIa");
        STAT_GETTERS.put("hB()[I", "statHB");
        STAT_GETTERS.put("hC()[I", "statHC");
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("input.class output.class match|teams|players|tooltips:<desc>|about:<desc>|stats:<count>");
        Path input = Paths.get(args[0]);
        Path output = Paths.get(args[1]);
        final boolean matchScreen = "match".equals(args[2]);
        final boolean teamsScreen = "teams".equals(args[2]);
        final boolean playersScreen = "players".equals(args[2]);
        final boolean tooltipsScreen = args[2].startsWith("tooltips:");
        final boolean aboutScreen = args[2].startsWith("about:");
        final boolean aboutSizeScreen = "aboutsize".equals(args[2]);
        final String tooltipCtorDesc = tooltipsScreen ? args[2].substring("tooltips:".length()) : null;
        final String aboutCtorDesc = aboutScreen ? args[2].substring("about:".length()) : null;
        int expectedStats = (matchScreen || teamsScreen || playersScreen || tooltipsScreen || aboutScreen || aboutSizeScreen) ? (matchScreen ? 1 : 0)
                : Integer.parseInt(args[2].substring("stats:".length()));
        ClassReader reader = new ClassReader(Files.readAllBytes(input));
        ClassWriter writer = new ClassWriter(reader,
                aboutScreen ? ClassWriter.COMPUTE_FRAMES : 0);
        final boolean[] patched = {false};
        final int[] steps = {0};
        final int[] penalty = {0};
        final int[] stats = {0};
        final int[] reveals = {0};
        final int[] flushes = {0};
        final int[] teamsPatched = {0};
        final int[] playersPatched = {0};
        final int[] tooltipsPatched = {0};
        final int[] aboutPatched = {0};
        final int[] aboutSizePatched = {0};
        ClassVisitor visitor = new ClassVisitor(Opcodes.ASM7, writer) {
            @Override public MethodVisitor visitMethod(int access, String name, String descriptor,
                                                       String signature, String[] exceptions) {
                MethodVisitor delegate = new MethodVisitor(Opcodes.ASM7,
                        super.visitMethod(access, name, descriptor, signature, exceptions)) {
                    @Override public void visitMethodInsn(int opcode, String owner, String method,
                                                          String desc, boolean isInterface) {
                        String target = opcode == Opcodes.INVOKEVIRTUAL && "best/I".equals(owner)
                                ? STAT_GETTERS.get(method + desc) : null;
                        if (target != null) {
                            String returns = desc.substring(desc.indexOf(')') + 1);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", target,
                                    "(Ljava/lang/Object;)" + returns, false);
                            stats[0]++;
                            return;
                        }
                        super.visitMethodInsn(opcode, owner, method, desc, isInterface);
                    }
                };
                if (playersScreen && "i".equals(name) && "(Lbest/F;)Z".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitMethodInsn(int opcode, String owner, String method,
                                                              String desc, boolean isInterface) {
                            if (opcode == Opcodes.INVOKESTATIC && "best/D".equals(owner)
                                    && "f".equals(method) && "(Ljava/lang/String;)Ljava/lang/String;".equals(desc)) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/PlayerSearch", "normalizedName",
                                        desc, false);
                                playersPatched[0]++;
                                return;
                            }
                            if (opcode == Opcodes.INVOKEVIRTUAL && "java/lang/String".equals(owner)
                                    && "substring".equals(method) && "(II)Ljava/lang/String;".equals(desc)) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/PlayerSearch", "keepFullName",
                                        "(Ljava/lang/String;II)Ljava/lang/String;", false);
                                return;
                            }
                            if (opcode == Opcodes.INVOKEVIRTUAL && "java/lang/String".equals(owner)
                                    && "equalsIgnoreCase".equals(method) && "(Ljava/lang/String;)Z".equals(desc)) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/PlayerSearch", "termMatch",
                                        "(Ljava/lang/String;Ljava/lang/String;)Z", false);
                                return;
                            }
                            super.visitMethodInsn(opcode, owner, method, desc, isInterface);
                        }
                    };
                }
                if (aboutSizeScreen && "rp".equals(name) && "()Z".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitIntInsn(int opcode, int operand) {
                            if (opcode == Opcodes.SIPUSH && operand == 185) {
                                super.visitIntInsn(Opcodes.SIPUSH, 250);
                                aboutSizePatched[0]++;
                                return;
                            }
                            super.visitIntInsn(opcode, operand);
                        }
                    };
                }
                if (aboutScreen && "<init>".equals(name) && aboutCtorDesc.equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitInsn(int opcode) {
                            if (opcode == Opcodes.RETURN) {
                                super.visitVarInsn(Opcodes.ALOAD, 0);
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/AboutPatch", "install",
                                        "(Ljava/lang/Object;)V", false);
                                aboutPatched[0]++;
                            }
                            super.visitInsn(opcode);
                        }
                    };
                }
                if (tooltipsScreen && "<init>".equals(name) && tooltipCtorDesc.equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitInsn(int opcode) {
                            if (opcode == Opcodes.RETURN) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/TooltipTweaks", "install",
                                        "()V", false);
                                tooltipsPatched[0]++;
                            }
                            super.visitInsn(opcode);
                        }
                    };
                }
                if (!matchScreen && !teamsScreen) return delegate;
                if (teamsScreen && "<init>".equals(name)
                        && "(Ljavax/swing/JDialog;Lbest/ah;Lbest/ah;Z)V".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitInsn(int opcode) {
                            if (opcode == Opcodes.RETURN) {
                                super.visitVarInsn(Opcodes.ALOAD, 0);
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/TeamTools", "install",
                                        "(Ljava/lang/Object;)V", false);
                                teamsPatched[0]++;
                            }
                            super.visitInsn(opcode);
                        }
                    };
                }
                if (!matchScreen) return delegate;
                if (("qg".equals(name) || "qc".equals(name)) && "()V".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitCode() {
                            super.visitCode();
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", "flushDeferred",
                                    "(Ljava/lang/Object;)V", false);
                            flushes[0]++;
                        }
                    };
                }
                if ("aa".equals(name) && "(Z)V".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitMethodInsn(int opcode, String owner, String method,
                                                              String desc, boolean isInterface) {
                            if (opcode == Opcodes.INVOKEVIRTUAL && "best/I".equals(owner)
                                    && "q".equals(method) && "(II)V".equals(desc)) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", "engineStep",
                                        "(Ljava/lang/Object;II)V", false);
                                steps[0]++;
                                return;
                            }
                            if (opcode == Opcodes.INVOKEVIRTUAL && "a/dV".equals(owner) && "a".equals(method)
                                    && "(Lcomponents/v;Lbest/I;Lbest/A;I)V".equals(desc)) {
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", "revealFromClock",
                                        "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;I)V", false);
                                reveals[0]++;
                                return;
                            }
                            super.visitMethodInsn(opcode, owner, method, desc, isInterface);
                        }
                    };
                }
                if ("b".equals(name) && "(Lcomponents/v;Lbest/A;)V".equals(descriptor)) {
                    return new MethodVisitor(Opcodes.ASM7, delegate) {
                        @Override public void visitCode() {
                            super.visitCode();
                            super.visitVarInsn(Opcodes.ALOAD, 1);
                            super.visitVarInsn(Opcodes.ALOAD, 2);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", "beforePenaltyKick",
                                    "(Ljava/lang/Object;Ljava/lang/Object;)V", false);
                            penalty[0]++;
                        }
                    };
                }
                if (!"<init>".equals(name) || !"(Ljavax/swing/JFrame;I)V".equals(descriptor)) return delegate;
                return new MethodVisitor(Opcodes.ASM7, delegate) {
                    @Override public void visitInsn(int opcode) {
                        if (opcode == Opcodes.RETURN) {
                            super.visitVarInsn(Opcodes.ALOAD, 0);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC, "mega/LiveMatchPanel", "install",
                                    "(Ljavax/swing/JPanel;)V", false);
                            patched[0] = true;
                        }
                        super.visitInsn(opcode);
                    }
                };
            }
        };
        reader.accept(visitor, 0);
        if (matchScreen) {
            if (!patched[0]) throw new IllegalStateException("recognized match-screen constructor not found");
            if (penalty[0] != 1) throw new IllegalStateException("expected one penalty kick method, found " + penalty[0]);
            if (steps[0] != 1) throw new IllegalStateException("expected one engine step call in aa, found " + steps[0]);
            if (reveals[0] != 1) throw new IllegalStateException("expected one reveal call in aa, found " + reveals[0]);
            if (flushes[0] != 2) throw new IllegalStateException("expected halftime and full-time methods, found " + flushes[0]);
        }
        if (teamsScreen && teamsPatched[0] != 1) {
            throw new IllegalStateException("recognized teams-screen constructor not found");
        }
        if (playersScreen && playersPatched[0] != 1) {
            throw new IllegalStateException("recognized player-filter method not found");
        }
        if (tooltipsScreen && tooltipsPatched[0] != 1) {
            throw new IllegalStateException("recognized tooltip constructor not found");
        }
        if (aboutScreen && aboutPatched[0] != 1) {
            throw new IllegalStateException("recognized about constructor not found");
        }
        if (aboutSizeScreen && aboutSizePatched[0] != 2) {
            throw new IllegalStateException("expected two about dialog sizes, found " + aboutSizePatched[0]);
        }
        if (!tooltipsScreen && !aboutScreen && !aboutSizeScreen && stats[0] != expectedStats) {
            throw new IllegalStateException("expected " + expectedStats + " statistic reads, found " + stats[0]);
        }
        Files.createDirectories(output.getParent());
        Files.write(output, writer.toByteArray());
    }
}
