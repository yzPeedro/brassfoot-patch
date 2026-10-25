package est;
import java.io.Serializable;
public final class ConfigLigaType implements Serializable {
    private static final long serialVersionUID = 16L;
    public boolean classificaPeloGeral, doisTurnos, jogosDentroGrupo, melhoresTerceiros, rebaixadoPeloGrupo, valido;
    public int desempate, divisao, formula, nGrupos, nRebaixados, nTimes, numeroTimesMataMata, pais,
            playoffRebaixamento, rebaixadosDireto, vagasSobemPeloMataMata, versaoArquivo;
    public boolean[] duasVoltasMataMata, duasVoltasMataMataSobe, duasVoltasplayoffReb;
    public String nome, nomeDivisao;
}
