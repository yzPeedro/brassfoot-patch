package mega;

import java.io.InputStream;
import java.lang.reflect.Field;
import javax.swing.JLabel;

public final class AboutPatch {
    private AboutPatch() {
    }

    private static String version() {
        try {
            InputStream stream = AboutPatch.class.getResourceAsStream("/mega/patch-version.txt");
            if (stream == null) return "2026";
            byte[] data = new byte[64];
            int length = stream.read(data);
            stream.close();
            if (length <= 0) return "2026";
            return new String(data, 0, length, "UTF-8").trim();
        } catch (Throwable ignored) {
            return "2026";
        }
    }

    public static void install(Object screen) {
        try {
            Field field = screen.getClass().getDeclaredField("vy");
            field.setAccessible(true);
            JLabel label = (JLabel) field.get(screen);
            if (label == null) return;
            String text = "<html><div style='font:bold 12px Tahoma;color:#fff8a0'>"
                    + "Brasfoot Mega Patch " + version() + "</div>"
                    + "<div style='font:11px Tahoma;color:#ffffff'>Criado por Pedro Pessoa</div>"
                    + "<div style='font:11px Tahoma;color:#ffffff'>pedrocruzpessoa16@gmail.com</div></html>";
            label.setText(text);
        } catch (Throwable ignored) {
        }
    }
}
