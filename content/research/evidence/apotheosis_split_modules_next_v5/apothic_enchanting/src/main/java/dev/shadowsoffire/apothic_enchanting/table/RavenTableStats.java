package dev.shadowsoffire.apothic_enchanting.table;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.neoforged.neoforge.attachment.AttachmentType;

/**
 * Persistent per-block-entity storage for the three player-set stats on an
 * {@link RavenEnchantingTableBlock} ("Enchanting Table of the Raven"). Attached to the shared
 * {@link net.minecraft.world.level.block.entity.EnchantingTableBlockEntity}, alongside the
 * existing {@link EnchantmentTableItemHandler#TYPE} attachment.
 * <p>
 * Mutable so {@link RavenEnchantmentMenu#setPlayerStats} can update in place without churning
 * attachment instances.
 */
public class RavenTableStats {

    public static final Codec<RavenTableStats> CODEC = RecordCodecBuilder.create(i -> i.group(
        Codec.intRange(0, 100).optionalFieldOf("eterna", 0).forGetter(s -> s.eterna),
        Codec.intRange(0, 100).optionalFieldOf("quanta", 0).forGetter(s -> s.quanta),
        Codec.intRange(0, 100).optionalFieldOf("arcana", 0).forGetter(s -> s.arcana))
        .apply(i, RavenTableStats::new));

    public static final AttachmentType<RavenTableStats> TYPE = AttachmentType
        .builder(RavenTableStats::new)
        .serialize(CODEC)
        .build();

    private int eterna;
    private int quanta;
    private int arcana;

    public RavenTableStats() {
        this(0, 0, 0);
    }

    public RavenTableStats(int eterna, int quanta, int arcana) {
        this.eterna = eterna;
        this.quanta = quanta;
        this.arcana = arcana;
    }

    public int eterna() {
        return this.eterna;
    }

    public int quanta() {
        return this.quanta;
    }

    public int arcana() {
        return this.arcana;
    }

    public void set(int eterna, int quanta, int arcana) {
        this.eterna = eterna;
        this.quanta = quanta;
        this.arcana = arcana;
    }

}
