package mega;

import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.lang.reflect.*;
import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;
import javax.swing.*;

public final class RenderFrame {
    static Field f(Class<?> c, String n) throws Exception { Field x = c.getDeclaredField(n); x.setAccessible(true);
        Field m = Field.class.getDeclaredField("modifiers"); m.setAccessible(true); m.setInt(x, x.getModifiers() & ~Modifier.FINAL); return x; }

    public static void main(String[] a) throws Exception {
        String out = a[0]; int w = Integer.parseInt(a[1]), h = Integer.parseInt(a[2]); double s = Double.parseDouble(a[3]);
        int condition = Integer.parseInt(a[4]);
        Constructor<LiveMatchPanel> k = LiveMatchPanel.class.getDeclaredConstructor(JPanel.class);
        k.setAccessible(true);
        LiveMatchPanel p = k.newInstance(new JPanel());
        ((Timer) f(LiveMatchPanel.class, "timer").get(p)).stop();
        p.setSize(w, h);
        Class<?> dot = Class.forName("mega.LiveMatchPanel$Dot");
        String[] homeNames = {"Cássio","William","Fabrício Bruno","Villalba","Kauã Moraes","Lucas Romero","Lucas Silva","Matheus Pereira","Gerson","Wanderson","Kaio Jorge"};
        String[] awayNames = {"Rossi","Varela","Léo Ortiz","Léo Pereira","Alex Sandro","Pulgar","Jorginho","Paquetá","Carrascal","Samuel Lino","Pedro"};
        double[][] hp = {{.07,.50},{.58,.14},{.44,.40},{.46,.64},{.62,.86},{.55,.44},{.63,.58},{.74,.36},{.70,.74},{.82,.20},{.84,.52}};
        double[][] ap = {{.955,.49},{.86,.30},{.885,.45},{.88,.60},{.85,.80},{.785,.49},{.76,.64},{.66,.30},{.62,.66},{.52,.20},{.50,.50}};
        fill(p, "home", dot, homeNames, hp);
        fill(p, "away", dot, awayNames, ap);
        f(LiveMatchPanel.class, "homeColor").set(p, new Color(12, 64, 196));
        f(LiveMatchPanel.class, "homeAccent").set(p, Color.WHITE);
        f(LiveMatchPanel.class, "awayColor").set(p, new Color(200, 22, 34));
        f(LiveMatchPanel.class, "awayAccent").set(p, new Color(16, 16, 16));
        f(LiveMatchPanel.class, "ballX").set(p, .752);
        f(LiveMatchPanel.class, "ballY").set(p, .385);
        f(LiveMatchPanel.class, "refX").set(p, .66);
        f(LiveMatchPanel.class, "refY").set(p, .52);
        f(LiveMatchPanel.class, "refereeName").set(p, "Anderson Daronco");
        f(LiveMatchPanel.class, "refereeKit").set(p, new Color(240, 210, 20));
        f(LiveMatchPanel.class, "ballAccent").set(p, new Color(20, 120, 220));
        f(LiveMatchPanel.class, "pitchCondition").set(p, condition);
        f(LiveMatchPanel.class, "possessingSide").set(p, 0);
        f(LiveMatchPanel.class, "possessingPlayer").set(p, 7);
        f(LiveMatchPanel.class, "looseBall").set(p, false);
        BufferedImage img = new BufferedImage((int) (w * s), (int) (h * s), BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.scale(s, s);
        Method paint = LiveMatchPanel.class.getDeclaredMethod("paintComponent", Graphics.class);
        paint.setAccessible(true);
        paint.invoke(p, g);
        g.dispose();
        write(img, new File(out));
        System.exit(0);
    }

    static void write(BufferedImage img, File out) throws Exception {
        if (!out.getName().endsWith(".jpg")) {
            ImageIO.write(img, "png", out);
            return;
        }
        ImageWriter writer = ImageIO.getImageWritersByFormatName("jpg").next();
        ImageWriteParam param = writer.getDefaultWriteParam();
        param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
        param.setCompressionQuality(.86f);
        ImageOutputStream stream = ImageIO.createImageOutputStream(out);
        writer.setOutput(stream);
        writer.write(null, new IIOImage(img, null, null), param);
        stream.close();
    }

    static void fill(LiveMatchPanel p, String field, Class<?> dot, String[] names, double[][] pos) throws Exception {
        Object[] team = (Object[]) f(LiveMatchPanel.class, field).get(p);
        for (int i = 0; i < team.length; i++) {
            f(dot, "name").set(team[i], names[i]);
            f(dot, "fullName").set(team[i], names[i]);
            f(dot, "currentX").set(team[i], pos[i][0]);
            f(dot, "currentY").set(team[i], pos[i][1]);
        }
    }
}
