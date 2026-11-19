package mega;

import est.ConfigLigaType;
import java.awt.Component;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.Map;
import javax.swing.JLabel;
import javax.swing.JTable;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableModel;

public final class SetupPanels {
    private static final int BRAZIL = 29;
    private static final String[] STATE_CONTROLS = {"Mz", "Mb", "Mi"};
    private static final String[] REGIONAL_CONTROLS = {"Mk", "Me"};
    private static final Map STATE = new IdentityHashMap();

    private SetupPanels() {
    }

    private static Object field(Object owner, String name) throws Exception {
        Field field = owner.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(owner);
    }

    public static void filterCountries() {
        try {
            ArrayList options = c.a.SR.bF;
            if (options == null) return;
            ArrayList kept = new ArrayList();
            for (int i = 0; i < options.size(); i++) {
                best.O option = (best.O) options.get(i);
                ConfigLigaType first = best.Z.t(option.getPais(), 1);
                if (first != null && option.iB() >= first.getnTimes()) kept.add(option);
            }
            if (!kept.isEmpty()) {
                options.clear();
                options.addAll(kept);
            }
        } catch (Throwable error) {
            System.err.println("[SetupPanels] filtro de paises: " + error);
        }
    }

    public static void install(final a.hU screen) {
        try {
            final JTable countries = (JTable) field(screen, "JG");
            countries.getSelectionModel().addListSelectionListener(new ListSelectionListener() {
                public void valueChanged(ListSelectionEvent event) {
                    if (!event.getValueIsAdjusting()) refresh(screen, countries);
                }
            });
            refresh(screen, countries);
        } catch (Throwable error) {
            System.err.println("[SetupPanels] instalacao: " + error);
        }
    }

    private static int focusedCountry(JTable countries) {
        int row = countries.getSelectedRow();
        ArrayList options = c.a.SR.bF;
        if (row < 0 || options == null || row >= options.size()) return BRAZIL;
        return ((best.O) options.get(row)).getPais();
    }

    private static void refresh(a.hU screen, JTable countries) {
        try {
            int country = focusedCountry(countries);
            Saved saved = (Saved) STATE.get(screen);
            if (country == BRAZIL) {
                if (saved != null) {
                    saved.restore(screen);
                    STATE.remove(screen);
                }
                return;
            }
            if (saved == null) {
                saved = new Saved(screen);
                STATE.put(screen, saved);
            }
            String name = best.ac.valueOf("P" + country).getNome();
            JTable states = (JTable) field(screen, "Mz");
            DefaultTableModel notice = new DefaultTableModel(new Object[][]{
                    {"Competições estaduais ainda não integradas para " + name + "."}}, new Object[]{"Estado"}) {
                public boolean isCellEditable(int row, int column) {
                    return false;
                }
            };
            states.setModel(notice);
            for (int i = 0; i < STATE_CONTROLS.length; i++) ((Component) field(screen, STATE_CONTROLS[i])).setEnabled(false);
            for (int i = 0; i < REGIONAL_CONTROLS.length; i++) ((Component) field(screen, REGIONAL_CONTROLS[i])).setEnabled(false);
            ((JLabel) field(screen, "Mp")).setText(" Estaduais — " + name);
            ((JLabel) field(screen, "Mq")).setText("Regionais — " + name + " (ainda não integrados)");
        } catch (Throwable error) {
            System.err.println("[SetupPanels] painel: " + error);
        }
    }

    private static final class Saved {
        private final TableModel model;
        private final int[] widths;
        private final int selected;
        private final boolean[] enabled = new boolean[STATE_CONTROLS.length + REGIONAL_CONTROLS.length];
        private final String stateTitle;
        private final String regionalTitle;

        Saved(a.hU screen) throws Exception {
            JTable states = (JTable) field(screen, "Mz");
            model = states.getModel();
            widths = new int[states.getColumnModel().getColumnCount()];
            for (int i = 0; i < widths.length; i++) widths[i] = states.getColumnModel().getColumn(i).getPreferredWidth();
            selected = states.getSelectedRow();
            for (int i = 0; i < STATE_CONTROLS.length; i++) enabled[i] = ((Component) field(screen, STATE_CONTROLS[i])).isEnabled();
            for (int i = 0; i < REGIONAL_CONTROLS.length; i++) {
                enabled[STATE_CONTROLS.length + i] = ((Component) field(screen, REGIONAL_CONTROLS[i])).isEnabled();
            }
            stateTitle = ((JLabel) field(screen, "Mp")).getText();
            regionalTitle = ((JLabel) field(screen, "Mq")).getText();
        }

        void restore(a.hU screen) throws Exception {
            JTable states = (JTable) field(screen, "Mz");
            states.setModel(model);
            for (int i = 0; i < widths.length && i < states.getColumnModel().getColumnCount(); i++) {
                states.getColumnModel().getColumn(i).setPreferredWidth(widths[i]);
            }
            if (selected >= 0 && selected < states.getRowCount()) states.setRowSelectionInterval(selected, selected);
            for (int i = 0; i < STATE_CONTROLS.length; i++) ((Component) field(screen, STATE_CONTROLS[i])).setEnabled(enabled[i]);
            for (int i = 0; i < REGIONAL_CONTROLS.length; i++) {
                ((Component) field(screen, REGIONAL_CONTROLS[i])).setEnabled(enabled[STATE_CONTROLS.length + i]);
            }
            ((JLabel) field(screen, "Mp")).setText(stateTitle);
            ((JLabel) field(screen, "Mq")).setText(regionalTitle);
        }
    }
}
