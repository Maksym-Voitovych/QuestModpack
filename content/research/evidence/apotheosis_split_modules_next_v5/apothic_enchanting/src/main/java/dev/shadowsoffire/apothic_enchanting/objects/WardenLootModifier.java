package dev.shadowsoffire.apothic_enchanting.objects;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import dev.shadowsoffire.apothic_enchanting.Ench;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.common.loot.LootModifier;

public class WardenLootModifier extends LootModifier {

    public static final MapCodec<WardenLootModifier> CODEC = RecordCodecBuilder.mapCodec(inst -> codecStart(inst).apply(inst, WardenLootModifier::new));
    public static final ResourceLocation WARDEN_TABLE_ID = ResourceLocation.withDefaultNamespace("entities/warden");

    public WardenLootModifier(LootItemCondition[] conditionsIn) {
        super(conditionsIn);
    }

    @Override
    public MapCodec<? extends IGlobalLootModifier> codec() {
        return CODEC;
    }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> loot, LootContext ctx) {
        if (WARDEN_TABLE_ID.equals(ctx.getQueriedLootTableId())) {
            int amount = 1;
            ItemStack tool = ctx.hasParam(LootContextParams.TOOL) ? ctx.getParam(LootContextParams.TOOL) : ItemStack.EMPTY;
            if (ctx.getRandom().nextFloat() <= 0.10F + tool.getEnchantmentLevel(ctx.getLevel().holderOrThrow(Enchantments.LOOTING)) * 0.10F) {
                amount++;
            }
            loot.add(new ItemStack(Ench.Items.WARDEN_TENDRIL.value(), amount));
        }
        return loot;
    }

}
