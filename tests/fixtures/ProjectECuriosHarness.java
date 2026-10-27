package ua.aia2.guard.mixin;

import com.google.common.collect.Multimap;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import moze_intel.projecte.integration.curios.IExposesCurioAttributes;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectECurioAttributes;
import ua.aia2.guard.ProjectEPassiveAccess;

public final class ProjectECuriosHarness {
    static final Holder<Attribute> FLIGHT = new Holder<>("neoforge:creative_flight");
    static final ResourceLocation ID = ResourceLocation.parse("projecte:arcana_flight");
    static final AttributeModifier MOD = new AttributeModifier(ID,1,Operation.ADD_VALUE);
    private static int assertions;
    private static void check(boolean value,String message){assertions++;if(!value)throw new AssertionError(message);}
    private static final class Arcana extends Item implements IExposesCurioAttributes {
        Arcana(){super("projecte:arcana_ring");}
        @Override public void addAttributes(Multimap<Holder<Attribute>,AttributeModifier> modifiers){modifiers.put(FLIGHT,MOD);}
    }
    private static final class Bag implements IItemHandler {
        List<ItemStack> contents;
        Bag(ItemStack... stacks){contents=List.of(stacks);}
        public int getSlots(){return contents.size();}
        public ItemStack getStackInSlot(int slot){return contents.get(slot);}
    }
    public record SlotContext(LivingEntity entity, boolean cosmetic) {}
    private static boolean exposes(Player player, ItemStack stack) throws Exception {
        var mixin = new ProjectECurioAttributesMixin(){};
        var field=ProjectECurioAttributesMixin.class.getDeclaredField("stack");field.setAccessible(true);field.set(mixin,stack);
        var callback=new CallbackInfoReturnable<Multimap<Holder<Attribute>,AttributeModifier>>();
        Method method=ProjectECurioAttributesMixin.class.getDeclaredMethod("aia2$usableCurioAttributes",Object.class,ResourceLocation.class,CallbackInfoReturnable.class);
        method.setAccessible(true);method.invoke(mixin,new SlotContext(player,false),ID,callback);
        return !callback.canceled;
    }
    private static void tick(Player player) throws Exception {
        var method=ProjectECurioReconcileMixin.class.getDeclaredMethod("aia2$currentCurioPolicy",CallbackInfo.class);
        method.setAccessible(true);method.invoke(player,new CallbackInfo());
    }
    public static void main(String[] args) throws Exception {
        var policy=ProjectEPassiveAccess.POLICY;
        policy.setRules(Map.of("projecte:arcana_ring",45));policy.setTeamProgress("a",43);policy.setTeamProgress("b",44);policy.setReady();
        Player player=new Player();ItemStack arcana=new ItemStack(new Arcana());player.handler=new Bag(arcana);
        var attribute=player.getAttribute(FLIGHT);attribute.addTransientModifier(MOD);
        check(!exposes(player,arcana),"locked fresh Curio query suppressed");tick(player);
        check(attribute.getModifier(ID)==null,"preexisting locked unchanged Curio modifier removed");
        check(arcana.count==1 && arcana.components.isEmpty(),"item identity/count/components unchanged");
        check(!ProjectECurioAttributes.hasAllowedModifier(player,FLIGHT,ID),"locked Curio not a shared contributor");
        policy.setTeamProgress("a",44);tick(player);
        check(attribute.getModifier(ID).equals(MOD),"unlock restores unchanged equipped Curio");
        check(exposes(player,arcana),"unlocked fresh query stays native");
        check(ProjectECurioAttributes.hasAllowedModifier(player,FLIGHT,ID),"active usable Curio protects shared modifier");
        int adds=attribute.adds,removes=attribute.removes;tick(player);tick(player);
        check(attribute.adds==adds && attribute.removes==removes,"stable ticks write no modifiers");
        attribute.removeModifier(ID);tick(player);
        check(attribute.getModifier(ID).equals(MOD),"missing native allowed modifier restored once");
        adds=attribute.adds;tick(player);check(attribute.adds==adds,"restoration not duplicated");
        policy.setTeamProgress("a",43);tick(player);
        check(attribute.getModifier(ID)==null,"same-stack downgrade removes effect");
        player.live="b";tick(player);check(attribute.getModifier(ID)==null,"stale team not borrowed from unlocked team");
        player.synced="b";tick(player);check(attribute.getModifier(ID).equals(MOD),"live synchronized team unlock works");
        player.fake=true;tick(player);check(attribute.getModifier(ID)==null,"fake wearer denied");
        player.fake=false;tick(player);check(attribute.getModifier(ID).equals(MOD),"real player restored");
        policy.clear();tick(player);check(attribute.getModifier(ID)==null,"reload-unready suppresses unchanged Curio");
        check(!exposes(player,arcana),"reload fresh-query gate closed");
        policy.setRules(Map.of("projecte:arcana_ring",45));policy.setTeamProgress("b",44);policy.setReady();tick(player);
        check(attribute.getModifier(ID).equals(MOD),"reload ready restores native value");
        player.handler=new Bag();tick(player);check(attribute.getModifier(ID)==null,"unequip cleans previously restored effect");
        tick(player);check(attribute.getModifier(ID)==null,"empty inventory stable");
        player.handler=new Bag(arcana,arcana);tick(player);
        check(attribute.getModifier(ID).equals(MOD),"duplicate native contributor id not duplicated");
        adds=attribute.adds;tick(player);check(attribute.adds==adds,"duplicate stack stable no write");
        player.handler=null;tick(player);check(attribute.getModifier(ID)==null,"capability invalidation cleans tracked effect");
        player.handler=new Bag(arcana);policy.setTeamProgress("b",43);
        var foreign=new AttributeModifier(ID,7,Operation.ADD_VALUE);attribute.addTransientModifier(foreign);tick(player);
        check(attribute.getModifier(ID).equals(foreign),"same ID different value never removed");
        policy.setTeamProgress("b",44);tick(player);check(attribute.getModifier(ID).equals(foreign),"same ID foreign value never overwritten");
        attribute.removeModifier(ID);tick(player);check(attribute.getModifier(ID).equals(MOD),"restore after unrelated value removed");
        policy.setTeamProgress("b",43);
        var vanilla=new ItemStack("minecraft:stone").with(EquipmentSlot.OFFHAND,FLIGHT,MOD);
        player.equipment.put(EquipmentSlot.OFFHAND,vanilla);tick(player);
        check(attribute.getModifier(ID).equals(MOD),"allowed vanilla contributor with same key protected");
        player.equipment.clear();tick(player);check(attribute.getModifier(ID)==null,"last allowed shared contributor gone");
        player.level.client=true;attribute.addTransientModifier(MOD);tick(player);
        check(attribute.getModifier(ID).equals(MOD),"client reconciliation performs no writes");
        check(exposes(player,arcana),"client prediction remains native");player.level.client=false;
        check(!ProjectECurioAttributes.mayExpose(null,arcana),"null slot context denied");
        check(!ProjectECurioAttributes.mayExpose(new SlotContext(new LivingEntity(),false),arcana),"nonplayer wearer denied");
        System.out.println(assertions+" actual-helper/handler/real-policy Curios model assertions PASS");
    }
}
