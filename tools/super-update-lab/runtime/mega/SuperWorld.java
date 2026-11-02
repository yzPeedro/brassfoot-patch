package mega;

import est.ConfigLigaType;
import java.lang.reflect.Array;
import java.util.ArrayList;

public final class SuperWorld {
    public static final int TABLE_DIVISIONS = 4;
    public static final int MAX_DIVISIONS = 12;

    private SuperWorld() {
    }

    public static int maxDivisions(int country) {
        int divisions = 4;
        ArrayList configs = c.a.SR == null ? null : c.a.SR.bG;
        if (configs != null) {
            for (Object item : configs) {
                ConfigLigaType config = (ConfigLigaType) item;
                if (config.getPais() == country && config.getDivisao() > divisions) {
                    divisions = config.getDivisao();
                }
            }
        }
        return Math.min(divisions, MAX_DIVISIONS);
    }

    public static Object padDivisions(Object table) {
        int length = Array.getLength(table);
        if (length == 0 || length > MAX_DIVISIONS) {
            return table;
        }
        Object padded = Array.newInstance(table.getClass().getComponentType(), MAX_DIVISIONS + 1);
        for (int index = 0; index <= MAX_DIVISIONS; index++) {
            Array.set(padded, index, Array.get(table, Math.min(index, length - 1)));
        }
        return padded;
    }

    public static void padDivisionsAt(Object[] table, int index) {
        table[index] = padDivisions(table[index]);
    }

    public static int clampIndex(int index, int max) {
        return index > max ? max : index;
    }

    public static int tableDivision(int division) {
        return division > TABLE_DIVISIONS ? TABLE_DIVISIONS : division;
    }
}
