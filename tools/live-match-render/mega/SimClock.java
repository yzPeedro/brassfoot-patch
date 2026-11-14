package mega;

import java.util.ArrayList;
import java.util.List;

public final class SimClock {
    public static long time = 1000000L;
    public static boolean dialog;
    private static final List<Runnable> LATER = new ArrayList<Runnable>();

    private SimClock() {
    }

    public static long now() {
        return time;
    }

    public static void later(Runnable runnable) {
        synchronized (LATER) {
            LATER.add(runnable);
        }
    }

    public static void runLater() {
        List<Runnable> batch;
        synchronized (LATER) {
            if (LATER.isEmpty()) return;
            batch = new ArrayList<Runnable>(LATER);
            LATER.clear();
        }
        for (Runnable runnable : batch) runnable.run();
    }

    public static void reset() {
        time = 1000000L;
        dialog = false;
        synchronized (LATER) {
            LATER.clear();
        }
    }
}
