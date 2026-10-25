package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;

import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.animal.Sheep;

@Mixin(value = Sheep.class, remap = false)
public class SheepMixin {

    @ModifyConstant(method = "shear", constant = @Constant(intValue = 3), require = 1)
    public int apoth_shearFortune(int oldVal, SoundSource category) {
        int fortune = ((Sheep) (Object) this).getPersistentData().getInt("apoth.sheep_fortune");
        return oldVal + fortune * 2;
    }

}
