package ua.aia2.guard.mixin;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import ua.aia2.guard.Aia2MachineGuard;

/** Actual redirect and real policy; Minecraft ticker host is modeled. */
public final class ProjectEWatchHarness {
    private static int checks;
    private static final Level WORLD=new Level();
    private static final BlockPos POS=new BlockPos(4,64,5);
    private static final ProjectETimeWatchMixin HANDLER=new ProjectETimeWatchMixin() {};
    private static final Method REDIRECT;
    static {
        try {
            REDIRECT=ProjectETimeWatchMixin.class.getDeclaredMethod("aia2$ownedBonusTick",BlockEntityTicker.class,
                    Level.class,BlockPos.class,BlockState.class,BlockEntity.class);
            REDIRECT.setAccessible(true);
        } catch(Exception error){throw new ExceptionInInitializerError(error);}
    }
    private static void check(boolean test,String why){checks++;if(!test)throw new AssertionError(why);}
    private static void invoke(BlockEntity target,BlockEntityTicker<BlockEntity> ticker) {
        try {REDIRECT.invoke(HANDLER,ticker,WORLD,POS,target==null?null:target.state,target);}
        catch(InvocationTargetException wrapper){
            if(wrapper.getCause() instanceof RuntimeException runtime)throw runtime;
            if(wrapper.getCause() instanceof Error error)throw error;
            throw new IllegalStateException(wrapper.getCause());
        } catch(ReflectiveOperationException impossible){throw new IllegalStateException(impossible);}
    }
    private static void ready(){
        var policy=Aia2MachineGuard.policy;
        policy.clear();policy.setRules(Map.of("test:machine",8,"test:early_machine",2,"test:postgame",99,"projecte:dm_pedestal",47));
        policy.setTeamProgress("late",48);policy.setTeamProgress("ready",7);policy.setTeamProgress("early",1);policy.setReady();
    }
    public static void main(String[] args){
        ready();int[] ticks={0};
        var pedestal=new BlockEntity(WORLD,"projecte:dm_pedestal","late");
        var locked=new BlockEntity(WORLD,"test:machine","early");
        var allowed=new BlockEntity(WORLD,"test:machine","ready");
        var early=new BlockEntity(WORLD,"test:early_machine","early");
        var parent=Aia2MachineGuard.enterTick(pedestal);
        check(parent==null,"fixture begins outside a native context");
        invoke(locked,(w,p,s,b)->ticks[0]++);
        check(ticks[0]==0,"late pedestal cannot give bonus ticks to a locked target");
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"denial preserves parent context");
        invoke(allowed,(w,p,s,b)->{
            ticks[0]++;
            check(b==allowed&&w==WORLD&&p==POS&&s==allowed.state,"redirect preserves exact ticker receiver and arguments");
            check(Aia2MachineGuard.currentTickOwner()==allowed,"native ticker runs with actual target owner");
            check(Aia2MachineGuard.mayProcessStage(8),"target's own unlocked recipe stage remains available");
            invoke(early,(x,y,z,nested)->check(!Aia2MachineGuard.mayProcessStage(8),"allowed early machine cannot borrow parent late recipe privileges"));
            check(Aia2MachineGuard.currentTickOwner()==allowed,"nested bonus tick restores its immediate target parent");
        });
        check(ticks[0]==1,"authorized target receives one native tick");
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"authorized completion restores pedestal context");
        RuntimeException original=new IllegalArgumentException("native ticker failure");
        boolean propagated=false;
        try{invoke(allowed,(w,p,s,b)->{throw original;});}catch(RuntimeException failure){propagated=failure==original;}
        check(propagated,"native ticker exception propagates without being hidden");
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"exception restores parent in finally");
        invoke(null,(w,p,s,b)->{throw new AssertionError("null target executed");});
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"null receiver fails closed without disturbing context");
        invoke(new BlockEntity(WORLD,"test:machine",null),(w,p,s,b)->{throw new AssertionError("unowned target executed");});
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"unowned staged receiver is denied");
        invoke(new BlockEntity(WORLD,"unclassified:machine","late"),(w,p,s,b)->{throw new AssertionError("unknown target executed");});
        check(Aia2MachineGuard.currentTickOwner()==pedestal,"unknown target remains quarantined after completed48");
        Aia2MachineGuard.exitTick(null);
        invoke(allowed,(w,p,s,b)->check(Aia2MachineGuard.currentTickOwner()==allowed,"inventory watch path also installs actual target context"));
        check(Aia2MachineGuard.currentTickOwner()==null,"inventory watch path removes temporary context");
        int[] batch={0};
        for(int i=0;i<3;i++)invoke(allowed,(w,p,s,b)->{batch[0]++;Aia2MachineGuard.policy.setTeamProgress("ready",6);});
        check(batch[0]==1,"each bonus tick rechecks stage changes during a batch");
        check(Aia2MachineGuard.currentTickOwner()==null,"batch denial never leaks its last target context");
        ready();Aia2MachineGuard.policy.clear();
        invoke(allowed,(w,p,s,b)->{throw new AssertionError("unready guard executed staged target");});
        check(Aia2MachineGuard.currentTickOwner()==null,"unready guard fails closed for staged bonus ticks");
        invoke(new BlockEntity(WORLD,"minecraft:furnace",null),(w,p,s,b)->check(Aia2MachineGuard.currentTickOwner()==b,"ungated vanilla tick retains native behavior with own context"));
        check(Aia2MachineGuard.currentTickOwner()==null,"vanilla completion cleans its context");
        System.out.println("ProjectEWatchHarness: "+checks+" actual-handler/real-policy assertions; modeled Minecraft host, no optional ProjectE dispatch");
    }
}
