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
@Mixin(targets="earth.terrarium.adastra.common.handlers.SpaceStationHandler",remap=false)
public abstract class AdAstraStationRegisterMixin {
 @Inject(method="constructSpaceStation(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/network/chat/Component;)V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
 private static void aia2$register(ServerPlayer p,ServerLevel l,Component n,CallbackInfo c){if(!StationConstructionAccess.beforeRegister(p,l,n))c.cancel();}
 @Inject(method="constructSpaceStation(Lnet/minecraft/server/level/ServerPlayer;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/network/chat/Component;)V",at=@At("RETURN"),remap=false,require=1)
 private static void aia2$registered(ServerPlayer p,ServerLevel l,Component n,CallbackInfo c){StationConstructionAccess.afterRegister(p,l,n);}
}
