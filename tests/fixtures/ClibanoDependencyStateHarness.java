package ua.aia2.guard;

import java.util.*;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Actual durable helper, modeled NBT primitives; no optional mod dispatch. */
public final class ClibanoDependencyStateHarness {
    private static int checks;
    private static final String A="a".repeat(64), B="b".repeat(64), C="c".repeat(64);
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static void rejects(Runnable run,String label){boolean rejected=false;try{run.run();}catch(IllegalArgumentException|IllegalStateException|NullPointerException expected){rejected=true;}check(rejected,label);}
    private static CompoundTag saved(Object machine){CompoundTag root=new CompoundTag();ClibanoDependencyState.save(machine,root);return root;}
    private static CompoundTag original(){Object machine=new Object();ClibanoDependencyState.setLane(machine,0,A);ClibanoDependencyState.setLane(machine,1,B);ClibanoDependencyState.setResidues(machine,Map.of("test:iron",new ClibanoDependencyState.Residue(C,9)));return saved(machine);}
    public static void main(String[] args){
        Object machine=new Object();ClibanoDependencyState.load(machine,new CompoundTag());
        check(ClibanoDependencyState.status(machine)==ClibanoDependencyState.Status.EMPTY,"legacy absence stays empty");
        check(ClibanoDependencyState.lane(machine,0).isEmpty()&&ClibanoDependencyState.residues(machine).isEmpty(),"legacy has no invented history");
        ClibanoDependencyState.setLane(machine,0,A);ClibanoDependencyState.setLane(machine,1,B);
        Map<String,ClibanoDependencyState.Residue> supplied=new HashMap<>();supplied.put("test:iron",new ClibanoDependencyState.Residue(C,9));
        ClibanoDependencyState.setResidues(machine,supplied);supplied.clear();
        check(ClibanoDependencyState.residues(machine).get("test:iron").amount()==9,"caller map cannot mutate durable balance");
        check(ClibanoDependencyState.lane(machine,0).orElseThrow().equals(A)&&ClibanoDependencyState.lane(machine,1).orElseThrow().equals(B),"residue update preserves both lanes");
        boolean immutable=false;try{ClibanoDependencyState.residues(machine).clear();}catch(UnsupportedOperationException expected){immutable=true;}check(immutable,"exposed historical map immutable");
        CompoundTag incoming=saved(machine),frozen=incoming.copy();Object restored=new Object();ClibanoDependencyState.load(restored,incoming);
        incoming.getCompound(ClibanoDependencyState.TAG).putString("first",C);
        check(saved(restored).equals(frozen),"load owns defensive NBT copy");
        Tag copy=ClibanoDependencyState.rawState(restored);((CompoundTag)copy).putString("first",C);
        check(saved(restored).equals(frozen),"rawState cannot mutate retained NBT");
        ClibanoDependencyState.setLane(restored,0,null);
        check(ClibanoDependencyState.lane(restored,0).isEmpty()&&ClibanoDependencyState.lane(restored,1).orElseThrow().equals(B),"clearing first lane preserves second");
        check(ClibanoDependencyState.residues(restored).get("test:iron").amount()==9,"clearing a lane retains residues");
        ClibanoDependencyState.clearLanes(restored);
        check(ClibanoDependencyState.lane(restored,1).isEmpty()&&ClibanoDependencyState.residues(restored).size()==1,"explicit cooking cancellation retains residue history");
        ClibanoDependencyState.setResidues(restored,Map.of());
        check(ClibanoDependencyState.status(restored)==ClibanoDependencyState.Status.EMPTY&&ClibanoDependencyState.rawState(restored)==null,"last trusted resource removal writes tombstone");
        CompoundTag tombstone=frozen.copy();tombstone.putString("foreign","retain");ClibanoDependencyState.save(restored,tombstone);
        check(!tombstone.contains(ClibanoDependencyState.TAG)&&tombstone.getString("foreign").equals("retain"),"durable clear removes only owned tag");
        Object full=new Object();ClibanoDependencyState.setResidues(full,Map.of("test:iron",new ClibanoDependencyState.Residue(A,64)));
        check(ClibanoDependencyState.residues(full).get("test:iron").amount()==64,"capacity64 valid");
        Map<String,ClibanoDependencyState.Residue> tooMany=new HashMap<>();for(int i=0;i<65;i++)tooMany.put("test:r"+i,new ClibanoDependencyState.Residue(A,1));
        rejects(()->ClibanoDependencyState.setResidues(full,tooMany),"65types denied");
        rejects(()->ClibanoDependencyState.setResidues(full,Map.of("test:a",new ClibanoDependencyState.Residue(A,64),"test:b",new ClibanoDependencyState.Residue(B,1))),"sum65 denied");
        check(ClibanoDependencyState.residues(full).get("test:iron").amount()==64,"failed updates preserve original history");
        for(int amount:new int[]{-1,0,65,Integer.MAX_VALUE})rejects(()->new ClibanoDependencyState.Residue(A,amount),"invalid historical amount "+amount);
        for(String hash:new String[]{"",A.substring(1),A+"a",A.toUpperCase(),"g".repeat(64)}){
            rejects(()->new ClibanoDependencyState.Residue(hash,1),"invalid residue SHA");
            rejects(()->ClibanoDependencyState.setLane(full,0,hash),"invalid lane SHA");
        }
        for(String id:new String[]{"", "missing", "Upper:case", "x:",":x","x:a b","x:"+"a".repeat(255)})rejects(()->ClibanoDependencyState.setResidues(full,Map.of(id,new ClibanoDependencyState.Residue(A,1))),"invalid residue ID");
        rejects(()->ClibanoDependencyState.setLane(full,-1,A),"negative lane");rejects(()->ClibanoDependencyState.lane(full,2),"third lane");
        List<CompoundTag> badRoots=new ArrayList<>();CompoundTag scalar=new CompoundTag();scalar.putString(ClibanoDependencyState.TAG,"opaque");badRoots.add(scalar);
        for(int mode=0;mode<15;mode++){
            CompoundTag root=original(),tag=root.getCompound(ClibanoDependencyState.TAG);
            switch(mode){
                case 0->tag.putInt("schema",2);case 1->tag.remove("schema");case 2->tag.putBoolean("schema",true);
                case 3->tag.putString("unknown","retain");case 4->tag.putInt("first",1);case 5->tag.putString("second","short");
                case 6->tag.remove("residues");case 7->tag.putString("residues","opaque");
                case 8->tag.getCompound("residues").putString("test:iron","opaque");
                case 9->tag.getCompound("residues").getCompound("test:iron").putInt("amount",0);
                case 10->tag.getCompound("residues").getCompound("test:iron").putBoolean("amount",true);
                case 11->tag.getCompound("residues").getCompound("test:iron").putString("definition","short");
                case 12->tag.getCompound("residues").getCompound("test:iron").putString("unknown","retain");
                case 13->{var row=tag.getCompound("residues").getCompound("test:iron").copy();tag.getCompound("residues").remove("test:iron");tag.getCompound("residues").put("Upper:case",row);}
                case 14->tag.getCompound("residues").getCompound("test:iron").remove("definition");
            }badRoots.add(root);
        }
        for(CompoundTag invalid:badRoots){
            Object bad=new Object();CompoundTag before=invalid.copy();ClibanoDependencyState.load(bad,invalid);
            check(ClibanoDependencyState.status(bad)==ClibanoDependencyState.Status.CORRUPT,"bad history stays corrupt");
            check(ClibanoDependencyState.lane(bad,0).isEmpty()&&ClibanoDependencyState.residues(bad).isEmpty(),"bad history authorizes nothing");
            rejects(()->ClibanoDependencyState.setLane(bad,0,A),"lane update cannot overwrite corrupt history");
            rejects(()->ClibanoDependencyState.setResidues(bad,Map.of()),"empty residue update cannot erase corrupt data");
            rejects(()->ClibanoDependencyState.clearLanes(bad),"cooking cancellation cannot erase corrupt residue journal");
            check(saved(bad).equals(before),"unsupported raw history preserved exactly");
            invalid.putString(ClibanoDependencyState.TAG,"caller mutation");check(saved(bad).equals(before),"corrupt raw defensive copy");
            ClibanoDependencyState.clear(bad);check(saved(bad).getAllKeys().isEmpty(),"only explicit trusted recovery clears corrupt history");
        }
        System.out.println("ClibanoDependencyStateHarness: "+checks+" actual-helper modeled assertions PASS");
    }
}
