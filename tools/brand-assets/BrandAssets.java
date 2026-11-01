import java.awt.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;

public final class BrandAssets {
    static final Color BRAND = new Color(0x0b4be0);
    static final Color MARK = new Color(0x074bdb);
    static final Color MARK_ACCENT = new Color(0x88b4ff);
    static final Color INK = new Color(0x0b1633);
    static final Color MUTED = new Color(0x5b6885);
    static final Color LINE = new Color(0xe1e7f3);
    static final Color SOFT = new Color(0xeaf0ff);
    static final Color SURFACE = new Color(0xf4f7fd);
    static final Color OK = new Color(0x0b7a55);
    static final Color OK_SOFT = new Color(0xe3f8ef);
    static final Color LIVE = new Color(0xd6203f);
    static final String MARK_PATH = "M17 15h18c14 0 17 17 7 21 12 6 7 18-6 18H17V15zm11 10v8h7c6 0 6-8 0-8h-7zm0 17v3h9c4 0 4-7 0-7h-9v4z";

    public static void main(String[] args) throws Exception {
        String mode = args[0];
        if (mode.equals("icon")) {
            int size = Integer.parseInt(args[1]);
            BufferedImage image = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g = quality(image.createGraphics());
            drawMark(g, 0, 0, size);
            g.dispose();
            ImageIO.write(image, "png", new File(args[2]));
            return;
        }
        int width = Integer.parseInt(args[1]);
        int height = Integer.parseInt(args[2]);
        BufferedImage pitch = ImageIO.read(new File(args[3]));
        String[] clubs = args[5].split("\\|");
        String clubs2026 = args[6];
        String updated = args[7];
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = quality(image.createGraphics());
        double unit = width / 1600.0;
        background(g, width, height, unit);
        int left = (int) (88 * unit);
        int top = (int) (88 * unit);
        drawMark(g, left, top, (int) (64 * unit));
        g.setColor(INK);
        g.setFont(font(Font.BOLD, 15 * unit));
        tracked(g, "BRASFOOT", left + (int) (82 * unit), top + (int) (26 * unit), 3.2f * (float) unit);
        g.setColor(BRAND);
        g.setFont(font(Font.BOLD, 24 * unit));
        g.drawString("MEGA PATCH 2026", left + (int) (82 * unit), top + (int) (56 * unit));
        int headlineY = top + (int) (190 * unit);
        g.setFont(font(Font.BOLD, 76 * unit));
        g.setColor(INK);
        g.drawString("O mundo no", left - (int) (3 * unit), headlineY);
        g.setPaint(new GradientPaint(left, 0, new Color(0x0837b5), left + (float) (520 * unit), 0, new Color(0x2f6bff)));
        g.drawString("seu Brasfoot.", left - (int) (3 * unit), headlineY + (int) (84 * unit));
        g.setColor(MUTED);
        g.setFont(font(Font.PLAIN, 25 * unit));
        g.drawString("Campo animado ao vivo, " + clubs2026 + " clubes", left, headlineY + (int) (150 * unit));
        g.drawString("e " + updated + " elencos atualizados para 2026.", left, headlineY + (int) (186 * unit));
        int pillY = headlineY + (int) (236 * unit);
        String url = "yzpeedro.github.io/brassfoot-patch";
        g.setFont(font(Font.BOLD, 21 * unit));
        int urlWidth = g.getFontMetrics().stringWidth(url);
        RoundRectangle2D pill = new RoundRectangle2D.Double(left, pillY, urlWidth + 74 * unit, 54 * unit, 54 * unit, 54 * unit);
        g.setColor(BRAND);
        g.fill(pill);
        g.setColor(Color.WHITE);
        g.drawString(url, left + (int) (26 * unit), pillY + (int) (35 * unit));
        g.drawString("→", left + urlWidth + (int) (38 * unit), pillY + (int) (35 * unit));
        int cardX = (int) (760 * unit);
        int cardY = (int) (88 * unit);
        int cardW = width - cardX - (int) (72 * unit);
        int imageW = cardW - (int) (28 * unit);
        int imageH = imageW * pitch.getHeight() / pitch.getWidth();
        int cardH = imageH + (int) (86 * unit);
        shadow(g, cardX, cardY, cardW, cardH, unit);
        g.setColor(Color.WHITE);
        g.fill(new RoundRectangle2D.Double(cardX, cardY, cardW, cardH, 30 * unit, 30 * unit));
        g.setColor(LINE);
        g.setStroke(new BasicStroke((float) Math.max(1, 1.5 * unit)));
        g.draw(new RoundRectangle2D.Double(cardX, cardY, cardW, cardH, 30 * unit, 30 * unit));
        int barY = cardY + (int) (36 * unit);
        for (int i = 0; i < 3; i++) {
            g.setColor(i == 0 ? BRAND : LINE);
            g.fill(new Ellipse2D.Double(cardX + (22 + i * 18) * unit, barY - 7 * unit, 12 * unit, 12 * unit));
        }
        g.setColor(MUTED);
        g.setFont(font(Font.BOLD, 14 * unit));
        tracked(g, "BRASFOOT 22–23 · TELA DE PARTIDA", cardX + (int) (86 * unit), barY + (int) (4 * unit), 1.6f * (float) unit);
        livePill(g, cardX + cardW - (int) (128 * unit), barY - (int) (18 * unit), unit);
        Shape clip = new RoundRectangle2D.Double(cardX + 14 * unit, cardY + 64 * unit, imageW, imageH, 18 * unit, 18 * unit);
        Shape previous = g.getClip();
        g.setClip(clip);
        g.drawImage(pitch, cardX + (int) (14 * unit), cardY + (int) (64 * unit), imageW, imageH, null);
        g.setClip(previous);
        int chipsY = cardY + cardH + (int) (54 * unit);
        g.setColor(INK);
        g.setFont(font(Font.BOLD, 15 * unit));
        tracked(g, "ELENCOS ATUALIZADOS", cardX, chipsY, 2.4f * (float) unit);
        int x = cardX;
        int y = chipsY + (int) (22 * unit);
        g.setFont(font(Font.BOLD, 19 * unit));
        for (String club : clubs) {
            int w = g.getFontMetrics().stringWidth(club) + (int) (56 * unit);
            if (x + w > width - 72 * unit) {
                x = cardX;
                y += (int) (54 * unit);
            }
            if (y + 46 * unit > height - 24 * unit) break;
            g.setColor(Color.WHITE);
            g.fill(new RoundRectangle2D.Double(x, y, w, 44 * unit, 44 * unit, 44 * unit));
            g.setColor(LINE);
            g.draw(new RoundRectangle2D.Double(x, y, w, 44 * unit, 44 * unit, 44 * unit));
            g.setColor(OK);
            g.fill(new Ellipse2D.Double(x + 18 * unit, y + 17 * unit, 10 * unit, 10 * unit));
            g.setColor(INK);
            g.drawString(club, x + (int) (38 * unit), y + (int) (29 * unit));
            x += w + (int) (10 * unit);
        }
        g.dispose();
        write(image, new File(args[4]));
    }

    static Graphics2D quality(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
        return g;
    }

    static Font font(int style, double size) {
        return new Font("Segoe UI", style, 1).deriveFont(style, (float) size);
    }

    static void tracked(Graphics2D g, String text, int x, int y, float spacing) {
        float position = x;
        FontMetrics metrics = g.getFontMetrics();
        for (char c : text.toCharArray()) {
            g.drawString(String.valueOf(c), position, y);
            position += metrics.charWidth(c) + spacing;
        }
    }

    static void background(Graphics2D g, int width, int height, double unit) {
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, width, height);
        g.setPaint(new RadialGradientPaint(new Point2D.Double(width * .92, 0), (float) (width * .55),
                new float[] {0f, 1f}, new Color[] {new Color(0xe3ecff), new Color(255, 255, 255, 0)}));
        g.fillRect(0, 0, width, height);
        double step = 64 * unit;
        for (double x = 0; x < width; x += step) {
            double fade = Math.max(0, 1 - Math.abs(x - width * .66) / (width * .5));
            g.setColor(new Color(11, 75, 224, (int) (14 * fade)));
            g.fill(new Rectangle2D.Double(x, 0, Math.max(1, unit), height));
        }
        for (double y = 0; y < height; y += step) {
            g.setColor(new Color(11, 75, 224, 8));
            g.fill(new Rectangle2D.Double(0, y, width, Math.max(1, unit)));
        }
        g.setPaint(new GradientPaint(0, 0, Color.WHITE, (float) (width * .42), 0, new Color(255, 255, 255, 0)));
        g.fillRect(0, 0, (int) (width * .42), height);
    }

    static void shadow(Graphics2D g, int x, int y, int w, int h, double unit) {
        for (int i = 18; i > 0; i--) {
            double spread = i * 2.2 * unit;
            g.setColor(new Color(11, 75, 224, 3));
            g.fill(new RoundRectangle2D.Double(x - spread / 2, y + 14 * unit - spread / 3, w + spread, h + spread,
                    (30 + spread) * unit, (30 + spread) * unit));
        }
    }

    static void livePill(Graphics2D g, int x, int y, double unit) {
        RoundRectangle2D pill = new RoundRectangle2D.Double(x, y, 106 * unit, 34 * unit, 34 * unit, 34 * unit);
        g.setColor(new Color(0xfff0f3));
        g.fill(pill);
        g.setColor(new Color(0xffd0d8));
        g.draw(pill);
        g.setColor(LIVE);
        g.fill(new Ellipse2D.Double(x + 14 * unit, y + 13 * unit, 9 * unit, 9 * unit));
        g.setFont(font(Font.BOLD, 13 * unit));
        tracked(g, "AO VIVO", x + (int) (32 * unit), y + (int) (22 * unit), 1.8f * (float) unit);
    }

    static void drawMark(Graphics2D g, int x, int y, int size) {
        AffineTransform previous = g.getTransform();
        g.translate(x, y);
        g.scale(size / 64.0, size / 64.0);
        g.setColor(MARK);
        g.fill(new RoundRectangle2D.Double(0, 0, 64, 64, 32, 32));
        g.setColor(Color.WHITE);
        g.fill(parse(MARK_PATH));
        g.setColor(MARK_ACCENT);
        g.fill(new Rectangle2D.Double(47, 10, 7, 7));
        g.setTransform(previous);
    }

    static Path2D parse(String d) {
        Path2D.Double path = new Path2D.Double(Path2D.WIND_NON_ZERO);
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("[MmHhVvCcZz]|-?\\d*\\.?\\d+").matcher(d);
        java.util.List<String> tokens = new java.util.ArrayList<String>();
        while (m.find()) tokens.add(m.group());
        double cx = 0, cy = 0, sx = 0, sy = 0;
        char command = 'M';
        int i = 0;
        while (i < tokens.size()) {
            String token = tokens.get(i);
            if (Character.isLetter(token.charAt(0))) {
                command = token.charAt(0);
                i++;
                if (command == 'z' || command == 'Z') {
                    path.closePath();
                    cx = sx;
                    cy = sy;
                    continue;
                }
            }
            boolean relative = Character.isLowerCase(command);
            switch (Character.toUpperCase(command)) {
                case 'M': {
                    double nx = Double.parseDouble(tokens.get(i++)), ny = Double.parseDouble(tokens.get(i++));
                    cx = relative ? cx + nx : nx;
                    cy = relative ? cy + ny : ny;
                    path.moveTo(cx, cy);
                    sx = cx;
                    sy = cy;
                    command = relative ? 'l' : 'L';
                    break;
                }
                case 'L': {
                    double nx = Double.parseDouble(tokens.get(i++)), ny = Double.parseDouble(tokens.get(i++));
                    cx = relative ? cx + nx : nx;
                    cy = relative ? cy + ny : ny;
                    path.lineTo(cx, cy);
                    break;
                }
                case 'H': {
                    double nx = Double.parseDouble(tokens.get(i++));
                    cx = relative ? cx + nx : nx;
                    path.lineTo(cx, cy);
                    break;
                }
                case 'V': {
                    double ny = Double.parseDouble(tokens.get(i++));
                    cy = relative ? cy + ny : ny;
                    path.lineTo(cx, cy);
                    break;
                }
                case 'C': {
                    double[] v = new double[6];
                    for (int k = 0; k < 6; k++) v[k] = Double.parseDouble(tokens.get(i++));
                    if (relative) {
                        for (int k = 0; k < 6; k += 2) {
                            v[k] += cx;
                            v[k + 1] += cy;
                        }
                    }
                    path.curveTo(v[0], v[1], v[2], v[3], v[4], v[5]);
                    cx = v[4];
                    cy = v[5];
                    break;
                }
                default:
                    throw new IllegalArgumentException("unsupported path command " + command);
            }
        }
        return path;
    }

    static void write(BufferedImage image, File out) throws Exception {
        if (!out.getName().endsWith(".jpg")) {
            ImageIO.write(image, "png", out);
            return;
        }
        ImageWriter writer = ImageIO.getImageWritersByFormatName("jpg").next();
        ImageWriteParam param = writer.getDefaultWriteParam();
        param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
        param.setCompressionQuality(.9f);
        ImageOutputStream stream = ImageIO.createImageOutputStream(out);
        writer.setOutput(stream);
        writer.write(null, new IIOImage(image, null, null), param);
        stream.close();
    }
}
