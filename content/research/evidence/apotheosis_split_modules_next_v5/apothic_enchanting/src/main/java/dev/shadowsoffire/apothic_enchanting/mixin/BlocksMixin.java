package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import dev.shadowsoffire.apothic_enchanting.table.ApothEnchantingTableBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EnchantingTableBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;

@Mixin(value = Blocks.class, remap = false)
public class BlocksMixin {

    @Redirect(at = @At(value = "NEW", target = "net/minecraft/world/level/block/EnchantingTableBlock"), method = "<clinit>", require = 1)
    private static EnchantingTableBlock apoth_overrideEnchTableBlock(BlockBehaviour.Properties properties) {
        return new ApothEnchantingTableBlock(properties);
    }

}
