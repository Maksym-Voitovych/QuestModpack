package dev.shadowsoffire.apothic_enchanting;

import dev.shadowsoffire.placebo.config.Configuration;

public class ApothEnchConfig {

    public static boolean showEnchantedBookMetadata = true;
    public static int sculkShelfNoiseChance = 200;
    public static boolean enableInlineEnchDescs = false;

    public static void load(Configuration c) {
        c.setTitle("Apotheosis Enchantment Module Config");

        showEnchantedBookMetadata = c.getBoolean("Show Enchanted Book Metadata", "client", true, "If enchanted book metadata (treasure, tradeable, etc) are shown in the tooltip.");
        sculkShelfNoiseChance = c.getInt("Sculkshelf Noise Chance", "client", 200, 0, 32767, "The 1/n chance that a sculkshelf plays a sound, per client tick. Set to 0 to disable.");
        enableInlineEnchDescs = c.getBoolean("Enable Inlined Enchantment Descriptions", "client", false,
            "If enchantment descriptions are shown inline in item tooltips.\nTranslations for vanilla enchantments require the 'Enchantment Descriptions' mod.");

        if (c.hasChanged()) c.save();
    }

}
