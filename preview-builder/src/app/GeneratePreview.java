package app;
import e.t;import e.g;
import java.io.*;import java.nio.file.*;import java.util.*;
import java.nio.charset.StandardCharsets;
/** Fictional 2026 alpha clubs, NOT authentic 2026 players. */
public final class GeneratePreview {
 public static void main(String[] args) throws Exception {
  if(args.length!=2)throw new IllegalArgumentException("Usage: GeneratePreview INPUT_TSV OUTPUT_DIRECTORY");
  Path in=Path.of(args[0]),out=Path.of(args[1]);Files.createDirectories(out);
  int count=0;Set<String> names=new HashSet<>();Set<Integer> ids=new HashSet<>();
  for(String line:Files.readAllLines(in,StandardCharsets.UTF_8)){
   if(line.isBlank()||line.startsWith("#"))continue;
   String[] cells=line.split("\t",-1);
   if(cells.length!=5)throw new IOException("Invalid team manifest line");
   String id=cells[0],display=cells[1],state=cells[2],division=cells[3];
   int internal=Integer.parseInt(cells[4]);
   if(!id.matches("[a-z0-9_-]+")||!state.matches("[A-Z]{2}")||!division.matches("[CD]")||display.isBlank()||!names.add(id)||!ids.add(internal)||internal<50000)throw new IOException("Unsafe identity: "+id);
   t team=new t();team.e=display;team.d=id;team.a=29;team.id=internal;
   team.tid=0;team.sid=0;team.aid=0;team.b=1;team.c=8;team.g=1000;
   team.i=29;team.n=0;team.o=0;team.vid=185;team.valid=true;
   team.f="Estadio de testes";team.h="Tecnico experimental";
   team.cor1="FFFFFF";team.cor2="000000";
   team.l=new ArrayList<>();team.m=new ArrayList<>();
   for(int i=0;i<18;i++){
    g player=new g();player.a="Atleta ficticio "+(i+1);player.aid=0;
    player.b=false;player.c=29;player.d=23+(i%9);
    player.e=i<2?0:(i<8?1:(i<14?2:3));
    player.f=i%2;player.g=5+(i%6);player.h=5+(i%6);
    player.hash=5;player.i=i%2;player.j=false;player.sid=0;
    player.tid=internal*100+i+1;team.l.add(player);
   }
   Path target=out.resolve(id+".ban");
   try(ObjectOutputStream o=new ObjectOutputStream(Files.newOutputStream(target,StandardOpenOption.CREATE_NEW))){o.writeObject(team);}
   try(ObjectInputStream input=new ObjectInputStream(Files.newInputStream(target))){
    t check=(t)input.readObject();
    if(check.id!=internal||!display.equals(check.e)||check.l.size()!=18)throw new IOException("Roundtrip failure");
   }
   count++;
  }
  if(count<1||count>46)throw new IOException("Expected from 1 to 46 placeholder teams, got "+count);
  System.out.println("Generated "+count+" fictional teams with 18 placeholder players each.");
 }
}
