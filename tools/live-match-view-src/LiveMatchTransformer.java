import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import jdk.internal.org.objectweb.asm.ClassReader;
import jdk.internal.org.objectweb.asm.ClassVisitor;
import jdk.internal.org.objectweb.asm.ClassWriter;
import jdk.internal.org.objectweb.asm.MethodVisitor;
import jdk.internal.org.objectweb.asm.Opcodes;

public final class LiveMatchTransformer {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("input.class output.class");
        Path input = Paths.get(args[0]);
        Path output = Paths.get(args[1]);
        ClassReader reader = new ClassReader(Files.readAllBytes(input));
        ClassWriter writer = new ClassWriter(reader, 0);
        final boolean[] patched = {false};
        final int[] steps = {0};
        ClassVisitor visitor = new ClassVisitor(Opcodes.ASM7, writer) {
            @Override public MethodVisitor visitMethod(int access, String name, String descriptor,
                                                       String signature, String[] exceptions) {
                MethodVisitor delegate = super.visitMethod(access, name, descriptor, signature, exceptions);
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
                            super.visitMethodInsn(opcode, owner, method, desc, isInterface);
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
        if (!patched[0]) throw new IllegalStateException("recognized match-screen constructor not found");
        if (steps[0] != 1) throw new IllegalStateException("expected one engine step call in aa, found " + steps[0]);
        Files.createDirectories(output.getParent());
        Files.write(output, writer.toByteArray());
    }
}
