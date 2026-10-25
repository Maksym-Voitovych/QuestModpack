package dev.shadowsoffire.apothic_enchanting.payloads;

import java.util.List;
import java.util.Optional;

import dev.shadowsoffire.apothic_enchanting.ApothEnchClient;
import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.placebo.network.PayloadProvider;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.ConnectionProtocol;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/**
 * Sends a clue message to the client.
 *
 * @param slot
 * @param clues The clues.
 * @param all   If this is all of the enchantments being received.
 */
public record CluePayload(int slot, List<EnchantmentInstance> clues, boolean all) implements CustomPacketPayload {

    public static final Type<CluePayload> TYPE = new Type<>(ApothicEnchanting.loc("clue"));

    public static final StreamCodec<RegistryFriendlyByteBuf, EnchantmentInstance> ENCH_INST_STREAM_CODEC = StreamCodec.composite(
        ByteBufCodecs.holderRegistry(Registries.ENCHANTMENT), i -> i.enchantment,
        ByteBufCodecs.VAR_INT, i -> i.level,
        EnchantmentInstance::new);

    public static final StreamCodec<RegistryFriendlyByteBuf, CluePayload> CODEC = StreamCodec.composite(
        ByteBufCodecs.INT, CluePayload::slot,
        ENCH_INST_STREAM_CODEC.apply(ByteBufCodecs.list()), CluePayload::clues,
        ByteBufCodecs.BOOL, CluePayload::all,
        CluePayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static class Provider implements PayloadProvider<CluePayload> {

        @Override
        public Type<CluePayload> getType() {
            return TYPE;
        }

        @Override
        public StreamCodec<? super RegistryFriendlyByteBuf, CluePayload> getCodec() {
            return CODEC;
        }

        @Override
        public void handle(CluePayload msg, IPayloadContext ctx) {
            ApothEnchClient.handleCluePayload(msg);
        }

        @Override
        public List<ConnectionProtocol> getSupportedProtocols() {
            return List.of(ConnectionProtocol.PLAY);
        }

        @Override
        public Optional<PacketFlow> getFlow() {
            return Optional.of(PacketFlow.CLIENTBOUND);
        }

        @Override
        public String getVersion() {
            return "1";
        }

    }

}
