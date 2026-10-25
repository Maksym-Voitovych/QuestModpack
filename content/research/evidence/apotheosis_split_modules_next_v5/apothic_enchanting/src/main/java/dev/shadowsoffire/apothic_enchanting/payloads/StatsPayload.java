package dev.shadowsoffire.apothic_enchanting.payloads;

import java.util.List;
import java.util.Optional;

import dev.shadowsoffire.apothic_enchanting.ApothEnchClient;
import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.table.EnchantmentTableStats;
import dev.shadowsoffire.placebo.network.PayloadProvider;
import net.minecraft.network.ConnectionProtocol;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

public record StatsPayload(EnchantmentTableStats stats) implements CustomPacketPayload {

    public static final Type<StatsPayload> TYPE = new Type<>(ApothicEnchanting.loc("stats"));

    public static final StreamCodec<RegistryFriendlyByteBuf, StatsPayload> CODEC = EnchantmentTableStats.STREAM_CODEC.map(StatsPayload::new, StatsPayload::stats);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static class Provider implements PayloadProvider<StatsPayload> {

        @Override
        public Type<StatsPayload> getType() {
            return TYPE;
        }

        @Override
        public StreamCodec<? super RegistryFriendlyByteBuf, StatsPayload> getCodec() {
            return CODEC;
        }

        @Override
        public void handle(StatsPayload msg, IPayloadContext ctx) {
            ApothEnchClient.handleStatsPayload(msg);
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
