package mega.lab;

import e.t;
import est.ArrayLigaType;
import est.ConfigLigaType;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public final class SyntheticWorld {
    private static final int[] LEVELS = {18, 14, 11, 8, 6, 5, 4, 3, 2, 1};

    private SyntheticWorld() {
    }

    public static void main(String[] args) throws Exception {
        File teams = new File(args[0]);
        File template = new File(teams, args[1]);
        String[] countries = args[2].split(",");
        int divisions = Integer.parseInt(args[3]);
        int perDivision = Integer.parseInt(args[4]);
        ConfigLigaType base = args.length > 5 ? baseConfig(new File(args[5])) : null;
        if (base != null) {
            new best.M(true);
        }
        File configs = new File(teams.getParentFile(), "conf_ligas_nacionais");
        int id = 900000;
        int written = 0;
        for (String code : countries) {
            int country = Integer.parseInt(code.trim());
            for (int division = 0; division < divisions; division++) {
                for (int index = 0; index < perDivision; index++) {
                    t team = read(template);
                    String name = "lab_" + country + "_" + (division + 1) + "_" + (index + 1);
                    team.setPais(country);
                    team.setEstado(0);
                    team.setNivel(LEVELS[Math.min(division, LEVELS.length - 1)]);
                    team.setNome("Lab " + country + " D" + (division + 1) + " " + (index + 1));
                    team.setFileRef(name);
                    team.setId(id);
                    team.setTid(id);
                    team.setSid(id);
                    team.setAid(id);
                    team.setValid(true);
                    team.setVid(185);
                    write(team, new File(teams, name + ".ban"));
                    id++;
                    written++;
                }
            }
            if (base != null) {
                ArrayLigaType leagues = new ArrayLigaType();
                for (int division = 1; division <= divisions; division++) {
                    ConfigLigaType config = (ConfigLigaType) copy(base);
                    config.setPais(country);
                    config.setDivisao(division);
                    config.setnTimes(perDivision);
                    config.setnGrupos(1);
                    config.setnRebaixados(division == divisions ? 0 : 4);
                    config.setRebaixadosDireto(division == divisions ? 0 : 4);
                    config.setNome2("Lab " + country);
                    config.setNomeDivisao("Divisao " + division);
                    leagues.a.add(config);
                }
                write(leagues, new File(configs, best.ac.valueOf("P" + country).jA() + ".cfg"));
            }
        }
        System.out.println(written);
    }

    private static t read(File file) throws Exception {
        ObjectInputStream input = new ObjectInputStream(new FileInputStream(file));
        try {
            return (t) input.readObject();
        } finally {
            input.close();
        }
    }

    private static ConfigLigaType baseConfig(File file) throws Exception {
        ObjectInputStream input = new ObjectInputStream(new FileInputStream(file));
        try {
            return (ConfigLigaType) ((ArrayLigaType) input.readObject()).a.get(0);
        } finally {
            input.close();
        }
    }

    private static Object copy(Object value) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        ObjectOutputStream output = new ObjectOutputStream(bytes);
        output.writeObject(value);
        output.close();
        return new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray())).readObject();
    }

    private static void write(Object team, File file) throws Exception {
        ObjectOutputStream output = new ObjectOutputStream(new FileOutputStream(file));
        try {
            output.writeObject(team);
        } finally {
            output.close();
        }
    }
}
