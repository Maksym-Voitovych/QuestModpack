package ua.aia2.guard.mixin;
import java.util.function.Consumer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.*;
import ua.aia2.guard.StationConstructionAccess;
@Pseudo
@Mixin(targets="earth.terrarium.adastra.common.recipes.SpaceStationRecipe",remap=false)
public abstract class AdAstraStationRecipeMixin {
 @Inject(method="hasIngredients(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/level/Level;Learth/terrarium/adastra/common/recipes/SpaceStationRecipe;)Z",at=@At("HEAD"),cancellable=true,remap=false,require=1)
 private static void aia2$plan(Player p,Level l,@Coerce Object r,CallbackInfoReturnable<Boolean> c){if(StationConstructionAccess.hasScope())c.setReturnValue(StationConstructionAccess.hasIngredients(p,l,r));}
 @Inject(method="consumeIngredients(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/level/Level;)V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
 private static void aia2$pay(Player p,Level l,CallbackInfo c){if(!l.isClientSide()){if(StationConstructionAccess.hasScope())StationConstructionAccess.consume(p,l);c.cancel();}}
}
