package dev.shadowsoffire.apothic_enchanting.payloads;

import java.util.List;
import java.util.Optional;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.table.RavenEnchantmentMenu;
import dev.shadowsoffire.placebo.network.PayloadProvider;
import net.minecraft.network.ConnectionProtocol;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/**
 * Client→server commit of the three slider values on the Enchanting Table of the Raven's screen.
 * Validation + clamping happens server-side in {@link RavenEnchantmentMenu#setPlayerStats}.
 */
public record SetRavenStatsPayload(int eterna, int quanta, int arcana) implements CustomPacketPayload {

    public static final Type<SetRavenStatsPayload> TYPE = new Type<>(ApothicEnchanting.loc("set_raven_stats"));

    public static final StreamCodec<RegistryFriendlyByteBuf, SetRavenStatsPayload> CODEC = StreamCodec.composite(
        ByteBufCodecs.INT, SetRavenStatsPayload::eterna,
        ByteBufCodecs.INT, SetRavenStatsPayload::quanta,
        ByteBufCodecs.INT, SetRavenStatsPayload::arcana,
        SetRavenStatsPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static class Provider implements PayloadProvider<SetRavenStatsPayload> {

        @Override
        public Type<SetRavenStatsPayload> getType() {
            return TYPE;
        }

        @Override
        public StreamCodec<? super RegistryFriendlyByteBuf, SetRavenStatsPayload> getCodec() {
            return CODEC;
        }

        @Override
        public void handle(SetRavenStatsPayload msg, IPayloadContext ctx) {
            // Flow is restricted to SERVERBOUND below, so this only runs on the logical server.
            if (ctx.player().containerMenu instanceof RavenEnchantmentMenu menu) {
                menu.setPlayerStats(msg.eterna(), msg.quanta(), msg.arcana());
            }
        }

        @Override
        public List<ConnectionProtocol> getSupportedProtocols() {
            return List.of(ConnectionProtocol.PLAY);
        }

        @Override
        public Optional<PacketFlow> getFlow() {
            return Optional.of(PacketFlow.SERVERBOUND);
        }

        @Override
        public String getVersion() {
            return "1";
        }

    }

}
