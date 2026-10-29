package ua.aia2.guard.mixin;

import net.minecraft.world.Containers;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.NasaProductionAccess;
import ua.aia2.guard.GuardedNasaDrop;

@Mixin(Containers.class)
public abstract class NasaDropMixin implements GuardedNasaDrop {
    @Redirect(method = "dropItemStack(Lnet/minecraft/world/level/Level;DDDLnet/minecraft/world/item/ItemStack;)V",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/Level;addFreshEntity(Lnet/minecraft/world/entity/Entity;)Z"), require = 1, allow = 1)
    private static boolean aia2$acceptedDrop(Level level, Entity entity) { return NasaProductionAccess.spawn(level, entity); }
}
