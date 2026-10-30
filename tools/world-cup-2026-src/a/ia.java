package a;

import c.a;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.swing.JCheckBox;

/** Compile-only method template. The patcher transplants only actionPerformed(). */
class ia implements ActionListener {
    @Override
    public void actionPerformed(ActionEvent event) {
        ((JCheckBox)event.getSource()).setSelected(true);
        a.SR.setUsarGruposReaisCopa(true);
        a.vM().setUsarGruposReaisCopa(true);
        a.vJ();
    }
}
