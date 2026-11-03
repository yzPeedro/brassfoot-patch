package app;

import est.ArrayLigaType;
import est.ConfigLigaType;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

public final class WorldLeagues {
    private static final int COLUMNS = 10;

    private WorldLeagues() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 2 && "dump".equals(args[0])) {
            dump((ArrayLigaType) CompetitionCodec.decode(Files.readAllBytes(Path.of(args[1]))));
            return;
        }
        if (args.length != 3) {
            System.err.println("WorldLeagues <template.cfg> <plan.tsv> <new-dir> | WorldLeagues dump <file.cfg>");
            System.exit(2);
        }
        ArrayLigaType template = (ArrayLigaType) CompetitionCodec.decode(Files.readAllBytes(Path.of(args[0])));
        Path output = Path.of(args[2]);
        if (Files.exists(output)) throw new IllegalArgumentException("Output must be a new directory");
        Files.createDirectories(output);
        Map<String, ArrayLigaType> files = new LinkedHashMap<>();
        for (String row : Files.readAllLines(Path.of(args[1]), StandardCharsets.UTF_8)) {
            String[] v = row.split("\t", -1);
            if (v.length != COLUMNS) throw new IllegalArgumentException("Expected " + COLUMNS + " columns: " + row);
            if (!v[0].matches("[A-Z]{3}")) throw new IllegalArgumentException("Invalid country file " + v[0]);
            int division = parse(v[2], 1, 12);
            ConfigLigaType source = template.a.get(parse(v[8], 1, template.a.size()) - 1);
            ConfigLigaType config = copy(source);
            config.pais = parse(v[1], 0, 223);
            config.divisao = division;
            config.nTimes = parse(v[3], 2, 200);
            config.nGrupos = parse(v[4], 0, 32);
            config.nRebaixados = parse(v[5], 0, 20);
            config.rebaixadosDireto = config.nRebaixados;
            config.nome = decode(v[6], 40);
            config.nomeDivisao = decode(v[7], 40);
            if (!"true".equals(v[9]) && !"false".equals(v[9])) throw new IllegalArgumentException("Invalid round robin " + v[9]);
            config.doisTurnos = Boolean.parseBoolean(v[9]);
            files.computeIfAbsent(v[0], key -> {
                ArrayLigaType value = new ArrayLigaType();
                value.a = new ArrayList<>();
                return value;
            }).a.add(config);
        }
        for (Map.Entry<String, ArrayLigaType> entry : files.entrySet()) {
            byte[] data = CompetitionCodec.encode(entry.getValue());
            CompetitionCodec.decode(data);
            Files.write(output.resolve(entry.getKey() + ".cfg"), data, StandardOpenOption.CREATE_NEW);
        }
        System.out.println("{\"files\":" + files.size() + "}");
    }

    private static ConfigLigaType copy(ConfigLigaType config) throws Exception {
        ArrayLigaType holder = new ArrayLigaType();
        holder.a = new ArrayList<>();
        holder.a.add(config);
        return ((ArrayLigaType) CompetitionCodec.decode(CompetitionCodec.encode(holder))).a.get(0);
    }

    private static int parse(String value, int min, int max) {
        int result = Integer.parseInt(value);
        if (result < min || result > max) throw new IllegalArgumentException("Out of range: " + value);
        return result;
    }

    private static String decode(String value, int maximum) {
        String text = new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8).strip();
        if (text.isEmpty() || text.length() > maximum) throw new IllegalArgumentException("Invalid name");
        return text;
    }

    private static void dump(ArrayLigaType root) {
        for (ConfigLigaType c : root.a) {
            System.out.println("divisao=" + c.divisao + " nTimes=" + c.nTimes + " nGrupos=" + c.nGrupos + " formula=" + c.formula
                    + " nRebaixados=" + c.nRebaixados + " rebaixadosDireto=" + c.rebaixadosDireto
                    + " playoffRebaixamento=" + c.playoffRebaixamento + " numeroTimesMataMata=" + c.numeroTimesMataMata
                    + " vagasSobemPeloMataMata=" + c.vagasSobemPeloMataMata + " doisTurnos=" + c.doisTurnos
                    + " jogosDentroGrupo=" + c.jogosDentroGrupo + " classificaPeloGeral=" + c.classificaPeloGeral
                    + " melhoresTerceiros=" + c.melhoresTerceiros + " rebaixadoPeloGrupo=" + c.rebaixadoPeloGrupo
                    + " desempate=" + c.desempate + " valido=" + c.valido + " versao=" + c.versaoArquivo
                    + " nome=" + c.nome + " nomeDivisao=" + c.nomeDivisao);
        }
    }
}
