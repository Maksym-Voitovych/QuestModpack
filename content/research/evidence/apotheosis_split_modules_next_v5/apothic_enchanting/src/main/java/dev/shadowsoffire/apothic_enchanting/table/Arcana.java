package dev.shadowsoffire.apothic_enchanting.table;

/**
 * Arcana Tiers, each represents a new rarity set.
 */
public enum Arcana {
    EMPTY(0, 10, 5, 2, 1),
    LITTLE(10, 8, 5, 3, 1),
    FEW(20, 7, 5, 4, 2),
    SOME(30, 5, 5, 4, 2),
    LESS(40, 5, 5, 4, 3),
    MEDIUM(50, 5, 5, 5, 5),
    MORE(60, 3, 4, 5, 5),
    VALUE(70, 2, 4, 5, 5),
    EXTRA(80, 2, 4, 5, 7),
    ALMOST(90, 1, 3, 5, 8),
    MAX(99, 1, 2, 5, 10);

    private final float threshold;
    private final int[] rarities;

    Arcana(float threshold, int common, int uncommon, int rare, int veryRare) {
        this.threshold = threshold;
        this.rarities = new int[] { common, uncommon, rare, veryRare };
    }

    static Arcana[] VALUES = values();

    public int[] getRarities() {
        return this.rarities;
    }

    /**
     * Quantizes a new weight value into a {@link LegacyRarity} and then performs the arcana weight lookup with the rarity.
     * 
     * @param weight The weight of an enchantment.
     * @return The new weight of the enchantment, given this Arcana level.
     */
    public int adjustWeight(int weight) {
        LegacyRarity rarity = LegacyRarity.byWeight(weight);
        return this.getRarities()[rarity.ordinal()];
    }

    public static Arcana getForThreshold(float threshold) {
        for (int i = VALUES.length - 1; i >= 0; i--) {
            if (threshold >= VALUES[i].threshold) return VALUES[i];
        }
        return EMPTY;
    }

}
