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
@Mixin(targets="earth.terrarium.adastra.common.network.packets.ServerboundConstructSpaceStationPacket$Type",remap=false)
public abstract class AdAstraStationPacketMixin {
 @Inject(method="handle(Learth/terrarium/adastra/common/network/packets/ServerboundConstructSpaceStationPacket;)Ljava/util/function/Consumer;",at=@At("RETURN"),cancellable=true,remap=false,require=1)
 private void aia2$stationScope(@Coerce Object packet,CallbackInfoReturnable<Consumer<Player>> callback){callback.setReturnValue(StationConstructionAccess.wrap(packet,callback.getReturnValue()));}
}
