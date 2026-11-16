package mega;

import javax.swing.ToolTipManager;

public final class TooltipTweaks {
    private static boolean applied;

    private TooltipTweaks() {
    }

    public static synchronized void install() {
        if (applied) return;
        applied = true;
        ToolTipManager manager = ToolTipManager.sharedInstance();
        manager.setInitialDelay(0);
        manager.setReshowDelay(0);
    }
}
