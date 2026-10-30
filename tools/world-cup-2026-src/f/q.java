package f;

import best.Z;
import best.ah;
import best.at;
import c.a;
import est.LoadLigaOptions;
import java.util.ArrayList;

/** Compile-only method template. The patcher transplants only ya() into the verified game class. */
public class q extends at {
    private s YD;
    private ArrayList YE;
    private int YH;
    private ArrayList YF;
    private ArrayList YM;
    private Z YN;
    private Z YG;

    public void ya() {
        if (a.SR.H() > 1) {
            this.Bu();
            return;
        }
        this.YE.clear();
        this.YF.clear();
        this.YD = null;
        ++this.YH;
        this.YG = this.eY(0);
        int[] countries = new int[]{131, 1, 49, 159, 38, 27, 39, 180,
            29, 129, 84, 62, 68, 150, 14, 192, 3, 8, 50, 60,
            85, 107, 179, 190, 21, 57, 98, 143, 65, 35, 9, 195,
            72, 169, 99, 142, 11, 10, 15, 108, 154, 157, 196, 46,
            97, 52, 75, 147};
        for (int countryId : countries) {
            Z country = a.SR.s(countryId);
            this.YE.add(country);
            this.YF.add(country.jo());
            country.z(true);
        }
        boolean[] knockoutLegs = new boolean[7];
        LoadLigaOptions options = new LoadLigaOptions();
        options.nTimes = 48;
        options.nGrupos = 12;
        options.numeroTimesMataMata = 2;
        options.melhoresTerceiros = true;
        options.doisTurnos = false;
        options.duasVoltasMataMata = knockoutLegs;
        this.YD = new s(options, this.YF, 0, null, null, null, 7, null, false, null, true, this);
        this.YD.setNome(this.getNome());
        a.afQ.L(this.YF);
        this.YM.clear();
        this.YN = null;
        this.YF.clear();
        this.YE.clear();
    }

    public void Bu() { throw new UnsupportedOperationException(); }
    public Z eY(int value) { throw new UnsupportedOperationException(); }
}
