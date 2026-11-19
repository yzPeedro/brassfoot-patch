import best.O;
import java.awt.Component;
import java.io.File;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.prefs.Preferences;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTable;

public final class SetupHarness {
    private static int failures;

    private static void check(boolean condition, String label) {
        System.out.println((condition ? "OK   " : "FALHA ") + label);
        if (!condition) failures++;
    }

    private static Object field(Object owner, String name) throws Exception {
        Field field = owner.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(owner);
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("java.util.prefs.PreferencesFactory", CompHarness.MemoryPrefsFactory.class.getName());
        File game = new File(args[0]).getCanonicalFile();
        System.setProperty("user.dir", game.getPath());
        new best.M(true);
        best.n.cU();
        new c.a();
        c.a.SR.bs = false;
        c.a.vH();
        best.p.dd();
        ArrayList options = c.a.SR.bF;
        StringBuilder names = new StringBuilder();
        boolean configured = true;
        for (Object item : options) {
            O option = (O) item;
            names.append(best.ac.valueOf("P" + option.getPais()).getNome()).append('(').append(option.iB()).append(") ");
            configured &= best.Z.t(option.getPais(), 1) != null;
        }
        check(options.size() > 0 && configured, "lista de paises so com liga nacional configurada: " + names);
        java.util.HashSet seen = new java.util.HashSet();
        boolean unique = true;
        for (Object item : options) unique &= seen.add(((O) item).getPais());
        check(unique, "sem paises duplicados");
        a.hU screen = new a.hU(new JFrame());
        JTable countries = (JTable) field(screen, "JG");
        JTable states = (JTable) field(screen, "Mz");
        int brazilRow = -1, otherRow = -1;
        for (int i = 0; i < options.size(); i++) {
            if (((O) options.get(i)).getPais() == 29) brazilRow = i;
            else if (otherRow < 0) otherRow = i;
        }
        int stateRows = states.getRowCount();
        boolean statesEnabled = ((Component) field(screen, "Mi")).isEnabled();
        check(brazilRow >= 0 && stateRows == 27, "Brasil em foco: " + stateRows + " estados no painel");
        ((O) options.get(otherRow)).v(true);
        countries.setRowSelectionInterval(otherRow, otherRow);
        String other = best.ac.valueOf("P" + ((O) options.get(otherRow)).getPais()).getNome();
        check(states.getRowCount() == 1 && String.valueOf(states.getValueAt(0, 0)).contains(other),
                other + " em foco: painel estadual mostra aviso (" + states.getValueAt(0, 0) + ")");
        check(!((Component) field(screen, "Mi")).isEnabled() && !((Component) field(screen, "Mk")).isEnabled()
                && !((Component) field(screen, "Mb")).isEnabled() && !((Component) field(screen, "Me")).isEnabled(),
                other + " em foco: controles estaduais e regionais desabilitados");
        check(((JLabel) field(screen, "Mp")).getText().contains(other), "titulo do painel indica " + other);
        countries.setRowSelectionInterval(brazilRow, brazilRow);
        check(states.getRowCount() == stateRows, "Brasil de volta: " + states.getRowCount() + " estados restaurados");
        check(((Component) field(screen, "Mi")).isEnabled() == statesEnabled, "Brasil de volta: estado original dos controles restaurado");
        int enabled = 0;
        for (Object item : options) if (((O) item).iC()) enabled++;
        check(((O) options.get(brazilRow)).iC() && ((O) options.get(otherRow)).iC() && enabled == 2,
                "selecao de varios paises preservada (Brasil e " + other + " marcados)");
        System.out.println("falhas=" + failures);
        System.exit(failures == 0 ? 0 : 1);
    }
}
