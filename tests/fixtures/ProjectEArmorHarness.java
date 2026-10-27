package ua.aia2.guard.mixin;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.*;
import java.util.function.BiConsumer;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.attributes.*;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.injection.callback.*;
import ua.aia2.guard.*;

/** Actual armor helpers/handlers and real GuardPolicy; Minecraft/parent passive bridge are modeled. */
public final class ProjectEArmorHarness {
    private static int checks;
    private static final Holder<Attribute> ARMOR = new Holder<>("minecraft:armor");
    private static final Holder<Attribute> FLIGHT = new Holder<>("neoforge:creative_flight");
    private static final ResourceLocation ARMOR_ID = ResourceLocation.parse("minecraft:armor.chestplate");
    private static final AttributeModifier GEM = new AttributeModifier(ARMOR_ID, 20, AttributeModifier.Operation.ADD_VALUE);
    private static final AttributeModifier VANILLA = new AttributeModifier(ARMOR_ID, 8, AttributeModifier.Operation.ADD_VALUE);
    private static final AttributeModifier ARCANA = new AttributeModifier(ResourceLocation.parse("projecte:arcana_flight"),1,AttributeModifier.Operation.ADD_VALUE);
    private static final Map<EquipmentSlot,ItemStack> NO_CHANGE = Map.of();
    private static final class Chest extends ProjectEGemChestMixin {}
    private static final class Helmet extends ProjectEGemHelmetMixin {}
    private static final class Feet extends ProjectEGemFeetMixin {}
    private static void check(boolean value,String reason) { checks++;if(!value)throw new AssertionError(reason); }
    private static Method method(Class<?> type,String name,Class<?>... args)throws Exception {
        var found=type.getDeclaredMethod(name,args);found.setAccessible(true);return found;
    }
    private static Object invoke(Method method,Object receiver,Object... args)throws Exception {
        try{return method.invoke(receiver,args);}catch(InvocationTargetException failure){if(failure.getCause() instanceof RuntimeException cause)throw cause;throw failure;}
    }
    private static void stage(String team,int completed) {ProjectEPassiveAccess.POLICY.setTeamProgress(team,completed);}
    private static ItemStack gem() {return new ItemStack("projecte:gem_chestplate").with(EquipmentSlot.CHEST,ARMOR,GEM);}
    private static List<ItemStack> list(Iterable<ItemStack> input) {var result=new ArrayList<ItemStack>();input.forEach(result::add);return result;}
    private static boolean present(Player player,Holder<Attribute> attribute,AttributeModifier modifier) {return modifier.equals(player.getAttribute(attribute).getModifier(modifier.id()));}
    public static void main(String[] args)throws Exception {
        var policy=ProjectEPassiveAccess.POLICY;
        policy.setRules(Map.of("projecte:gem_helmet",47,"projecte:gem_chestplate",47,"projecte:gem_boots",47,"projecte:gem_leggings",47,"projecte:dm_chestplate",45,"projecte:arcana_ring",45));
        stage("a",44);stage("other",46);policy.setReady();
        var player=new Player();var chest=gem();var helmet=new ItemStack("projecte:gem_helmet");var ordinary=new ItemStack("minecraft:iron_boots");
        player.equipment.put(EquipmentSlot.CHEST,chest);player.equipment.put(EquipmentSlot.HEAD,helmet);player.equipment.put(EquipmentSlot.FEET,ordinary);
        var view=list(ProjectEArmorAccess.armor(player));
        check(!view.contains(chest)&&!view.contains(helmet)&&view.contains(ordinary),"damage/fire views hide locked armor and preserve unrelated gear");
        check(player.getItemBySlot(EquipmentSlot.CHEST)==chest&&chest.count==1,"views never unequip or modify the actual stack");
        check(ProjectEArmorAccess.equipment(player,EquipmentSlot.HEAD).isEmpty(),"direct Gem and walking selectors hide locked helmet");
        check(!ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.CHEST),"packet ability rejects actual locked chest");
        stage("a",46);
        check(ProjectEArmorAccess.equipment(player,EquipmentSlot.HEAD)==helmet,"unlock restores view immediately without equipment change");
        check(ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.CHEST)&&ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.HEAD),"correct unlocked Gem pieces authorize their own abilities");
        check(!ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.FEET),"unsupported ability slot is never inferred from another piece");
        player.equipment.put(EquipmentSlot.CHEST,new ItemStack("projecte:dm_chestplate"));
        check(!ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.CHEST),"available DM armor cannot impersonate a Gem chest ability");player.equipment.put(EquipmentSlot.CHEST,chest);
        player.live="other";
        check(!ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.HEAD),"stale synced team loses Gem ability immediately");player.live="a";
        player.fake=true;check(!ProjectEArmorAccess.mayUseGemAbility(player,EquipmentSlot.HEAD),"fake player cannot use personal Gem ability");player.fake=false;
        var mob=new LivingEntity();mob.equipment.put(EquipmentSlot.CHEST,chest);
        check(list(ProjectEArmorAccess.armor(mob)).contains(chest),"non-player native damage calculation is unchanged");
        stage("a",44);player.level.client=true;check(ProjectEArmorAccess.equipment(player,EquipmentSlot.CHEST)==chest,"client visual view remains native");player.level.client=false;

        var damage=method(ProjectEArmorEventsMixin.class,"aia2$availableDamageArmor",LivingEntity.class);
        var fire=method(ProjectEArmorFireMixin.class,"aia2$availableFireArmor",Player.class);
        check(!list((Iterable<ItemStack>)invoke(damage,null,player)).contains(chest),"damage handler forwards actual protected view");
        check(!list((Iterable<ItemStack>)invoke(fire,null,player)).contains(chest),"fire handler forwards actual protected view");
        var piece=method(ProjectEGemArmorMixin.class,"aia2$availableGemPiece",Player.class,EquipmentSlot.class);
        var walk=method(ProjectEArmorAbilitiesMixin.class,"aia2$availableWalkingArmor",Player.class,EquipmentSlot.class);
        check(((ItemStack)invoke(piece,null,player,EquipmentSlot.HEAD)).isEmpty(),"Gem set handler uses actual slot policy");
        check(((ItemStack)invoke(walk,null,player,EquipmentSlot.CHEST)).isEmpty(),"InternalAbilities selector hides unavailable water/lava armor");
        var explode=method(ProjectEGemChestMixin.class,"aia2$guardChestAbility",Player.class,CallbackInfo.class);
        var chestFire=method(ProjectEGemChestMixin.class,"aia2$guardChestFire",ItemStack.class,Player.class,CallbackInfoReturnable.class);
        var vision=method(ProjectEGemHelmetMixin.class,"aia2$guardVisionToggle",ItemStack.class,Player.class,CallbackInfo.class);
        var zap=method(ProjectEGemHelmetMixin.class,"aia2$guardHelmetAbility",Player.class,CallbackInfo.class);
        var step=method(ProjectEGemFeetMixin.class,"aia2$guardStepToggle",ItemStack.class,Player.class,CallbackInfo.class);
        var ci=new CallbackInfo();invoke(explode,null,player,ci);check(ci.canceled,"locked chest explosion canceled before native action");
        var cir=new CallbackInfoReturnable<Boolean>();invoke(chestFire,new Chest(),chest,player,cir);check(cir.canceled&&Boolean.FALSE.equals(cir.value),"locked chest fire protector returns false");
        ci=new CallbackInfo();invoke(vision,null,helmet,player,ci);check(ci.canceled,"locked helmet mode packet canceled");
        ci=new CallbackInfo();invoke(zap,null,player,ci);check(ci.canceled,"locked helmet lightning canceled");
        ci=new CallbackInfo();invoke(step,null,new ItemStack("projecte:gem_boots"),player,ci);check(ci.canceled,"locked boot mode packet canceled");
        stage("a",46);
        ci=new CallbackInfo();invoke(explode,null,player,ci);check(!ci.canceled,"unlocked chest preserves native explosion path");
        cir=new CallbackInfoReturnable<Boolean>();invoke(chestFire,new Chest(),chest,player,cir);check(!cir.canceled,"unlocked chest preserves native fire calculation");
        ci=new CallbackInfo();invoke(vision,null,helmet,player,ci);check(!ci.canceled,"unlocked helmet mode remains native");
        ci=new CallbackInfo();invoke(zap,null,player,ci);check(!ci.canceled,"unlocked helmet lightning remains native");
        ci=new CallbackInfo();invoke(step,null,new ItemStack("projecte:gem_boots"),player,ci);check(!ci.canceled,"unlocked boot mode remains native");
        check(chest.count==1&&helmet.components.isEmpty(),"all deny/allow handlers leave equipment and item modes untouched");

        // The actual vanilla addition wrapper is invoked on the modeled LivingEntity mixin host.
        var apply=method(ProjectEEquipmentAttributesMixin.class,"aia2$availableEquipmentAttributes",ItemStack.class,EquipmentSlot.class,BiConsumer.class);
        var reconcile=method(ProjectEEquipmentAttributesMixin.class,"aia2$currentEquipmentPolicy",CallbackInfoReturnable.class);
        var tracked=new Player();tracked.equipment.put(EquipmentSlot.CHEST,gem());var stats=tracked.getAttribute(ARMOR);
        BiConsumer<Holder<Attribute>,AttributeModifier> add=(attribute,modifier)->tracked.getAttribute(attribute).addTransientModifier(modifier);
        stage("a",44);invoke(apply,tracked,tracked.getItemBySlot(EquipmentSlot.CHEST),EquipmentSlot.CHEST,add);
        check(stats.adds==0,"new locked PE equipment adds no vanilla armor attribute");
        var base=new ItemStack("minecraft:diamond_chestplate").with(EquipmentSlot.CHEST,ARMOR,VANILLA);
        invoke(apply,tracked,base,EquipmentSlot.CHEST,add);
        check(present(tracked,ARMOR,VANILLA),"unrelated vanilla attribute application remains unchanged even while PE is locked");
        stats.modifiers.clear();stats.adds=0;stats.removes=0;
        // Existing stack from before a stage/team change, including preexisting native attribute.
        stats.modifiers.put(GEM.id(),GEM);
        var state=new CallbackInfoReturnable<Map<EquipmentSlot,ItemStack>>();state.value=NO_CHANGE;
        invoke(reconcile,tracked,state);
        check(stats.getModifier(GEM.id())==null&&stats.removes==1,"locked unchanged equipment loses only matching native modifier");
        check(tracked.getItemBySlot(EquipmentSlot.CHEST).count==1,"attribute policy never changes equipment or quantity");
        int beforeAdds=stats.adds,beforeRemoves=stats.removes;
        invoke(reconcile,tracked,state);check(stats.adds==beforeAdds&&stats.removes==beforeRemoves,"stable locked frame makes zero modifier writes");
        stage("a",46);invoke(reconcile,tracked,state);
        check(present(tracked,ARMOR,GEM)&&stats.adds==beforeAdds+1,"unlock without re-equipping restores suppressed native modifier exactly once");
        invoke(reconcile,tracked,state);check(stats.adds==beforeAdds+1&&stats.removes==beforeRemoves,"stable unlocked frame makes zero modifier writes");
        stage("a",44);invoke(reconcile,tracked,state);check(stats.getModifier(GEM.id())==null,"downgrade after unlock removes stale effect");
        stage("a",46);invoke(reconcile,tracked,state);tracked.live="other";invoke(reconcile,tracked,state);
        check(stats.getModifier(GEM.id())==null,"live team change removes current equipment effects before resync");tracked.live="a";
        invoke(reconcile,tracked,state);check(present(tracked,ARMOR,GEM),"resync restores actual allowed stack effect");
        tracked.fake=true;invoke(reconcile,tracked,state);check(stats.getModifier(GEM.id())==null,"fake context removes inherited PE attributes");tracked.fake=false;

        var foreign=new Player();foreign.equipment.put(EquipmentSlot.CHEST,gem());foreign.getAttribute(ARMOR).modifiers.put(GEM.id(),VANILLA);
        stage("a",44);ProjectEArmorAttributes.reconcile(foreign,NO_CHANGE);
        check(present(foreign,ARMOR,VANILLA)&&foreign.getAttribute(ARMOR).removes==0,"same ID with unrelated value is never removed");
        var shared=new Player();shared.equipment.put(EquipmentSlot.CHEST,gem());shared.equipment.put(EquipmentSlot.HEAD,new ItemStack("minecraft:helmet").with(EquipmentSlot.HEAD,ARMOR,VANILLA));
        shared.getAttribute(ARMOR).modifiers.put(VANILLA.id(),VANILLA);ProjectEArmorAttributes.reconcile(shared,NO_CHANGE);
        check(present(shared,ARMOR,VANILLA)&&shared.getAttribute(ARMOR).removes==0,"allowed unrelated equipped provider protects shared attribute ID");
        shared.equipment.remove(EquipmentSlot.HEAD);shared.getAttribute(ARMOR).modifiers.put(GEM.id(),GEM);ProjectEArmorAttributes.reconcile(shared,Map.of(EquipmentSlot.HEAD,ItemStack.EMPTY));
        check(shared.getAttribute(ARMOR).getModifier(GEM.id())==null,"after unrelated provider removed locked PE effect cannot persist");
        var curioShared=new Player();curioShared.equipment.put(EquipmentSlot.CHEST,gem());curioShared.getAttribute(ARMOR).modifiers.put(GEM.id(),GEM);
        var curioKey=new ProjectECurioAttributes.Key(curioShared,ARMOR,GEM.id());ProjectECurioAttributes.allowed.add(curioKey);
        ProjectEArmorAttributes.reconcile(curioShared,NO_CHANGE);
        check(present(curioShared,ARMOR,GEM)&&curioShared.getAttribute(ARMOR).removes==0,"actual allowed Curio provider protects its shared native modifier from blocked armor");
        ProjectECurioAttributes.allowed.remove(curioKey);ProjectEArmorAttributes.reconcile(curioShared,Map.of(EquipmentSlot.CHEST,curioShared.getItemBySlot(EquipmentSlot.CHEST)));
        check(curioShared.getAttribute(ARMOR).getModifier(GEM.id())==null,"after Curio provider removed current equipment update suppresses remaining blocked modifier");
        ProjectECurioAttributes.allowed.add(curioKey);stage("a",46);ProjectEArmorAttributes.reconcile(curioShared,NO_CHANGE);
        check(curioShared.getAttribute(ARMOR).getModifier(GEM.id())==null&&curioShared.getAttribute(ARMOR).adds==0,"unlock does not restore an armor-owned value over a currently allowed Curio provider");ProjectECurioAttributes.allowed.remove(curioKey);
        var offhand=new Player();var ring=new ItemStack("projecte:arcana_ring").with(EquipmentSlot.OFFHAND,FLIGHT,ARCANA);
        offhand.equipment.put(EquipmentSlot.OFFHAND,ring);offhand.getAttribute(FLIGHT).modifiers.put(ARCANA.id(),ARCANA);
        stage("a",43);ProjectEArmorAttributes.reconcile(offhand,NO_CHANGE);
        check(offhand.getAttribute(FLIGHT).getModifier(ARCANA.id())==null,"offhand Arcana default ANY attribute also guarded");
        stage("a",44);ProjectEArmorAttributes.reconcile(offhand,NO_CHANGE);check(present(offhand,FLIGHT,ARCANA),"offhand ring unlock restores same stack effect");
        offhand.equipment.remove(EquipmentSlot.OFFHAND);offhand.getAttribute(FLIGHT).modifiers.remove(ARCANA.id());ProjectEArmorAttributes.reconcile(offhand,Map.of(EquipmentSlot.OFFHAND,ItemStack.EMPTY));
        stage("a",46);ProjectEArmorAttributes.reconcile(offhand,NO_CHANGE);check(offhand.getAttribute(FLIGHT).getModifier(ARCANA.id())==null,"unequipped ring is never restored later");
        var client=new Player();client.level.client=true;client.equipment.put(EquipmentSlot.CHEST,gem());client.getAttribute(ARMOR).modifiers.put(GEM.id(),GEM);stage("a",43);ProjectEArmorAttributes.reconcile(client,NO_CHANGE);
        check(present(client,ARMOR,GEM)&&client.getAttribute(ARMOR).removes==0,"client attribute reconciliation remains native");
        policy.clear();ProjectEArmorAttributes.reconcile(tracked,NO_CHANGE);check(tracked.getAttribute(ARMOR).getModifier(GEM.id())==null,"unready policy fails closed for existing equipment");
        System.out.println("ProjectEArmorHarness: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/passive bridge, no optional ProjectE dispatch or client movement test");
    }
}
