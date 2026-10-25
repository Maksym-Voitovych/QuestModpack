package dev.shadowsoffire.apothic_enchanting.table;

import net.minecraft.ChatFormatting;

public enum LegacyRarity {
    COMMON(10, ChatFormatting.WHITE),
    UNCOMMON(5, ChatFormatting.YELLOW),
    RARE(2, ChatFormatting.BLUE),
    VERY_RARE(1, ChatFormatting.GOLD);

    private final int weight;
    private final int color;

    private LegacyRarity(int pWeight, ChatFormatting color) {
        this.weight = pWeight;
        this.color = color.getColor();
    }

    public int weight() {
        return this.weight;
    }

    public int color() {
        return this.color;
    }

    public static LegacyRarity byWeight(int weight) {
        if (weight > 10) return COMMON;
        else if (weight > 5) return UNCOMMON;
        else if (weight > 2) return RARE;
        else return VERY_RARE;
    }

}
