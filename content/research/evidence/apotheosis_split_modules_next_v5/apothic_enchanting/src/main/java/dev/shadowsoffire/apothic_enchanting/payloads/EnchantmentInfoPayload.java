package dev.shadowsoffire.apothic_enchanting.payloads;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.EnchantmentInfo;
import dev.shadowsoffire.placebo.network.PayloadProvider;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.ConnectionProtocol;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.item.enchantment.Enchantment;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.server.ServerLifecycleHooks;

public record EnchantmentInfoPayload(Map<Holder<Enchantment>, EnchantmentInfo> info) implements CustomPacketPayload {

    public static final Type<EnchantmentInfoPayload> TYPE = new Type<>(ApothicEnchanting.loc("enchantment_info"));

    public static final StreamCodec<RegistryFriendlyByteBuf, EnchantmentInfoPayload> STREAM_CODEC = StreamCodec.composite(
        ByteBufCodecs.map(HashMap::new, ByteBufCodecs.holderRegistry(Registries.ENCHANTMENT), EnchantmentInfo.STREAM_CODEC), EnchantmentInfoPayload::info,
        EnchantmentInfoPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static class Provider implements PayloadProvider<EnchantmentInfoPayload> {

        @Override
        public Type<EnchantmentInfoPayload> getType() {
            return TYPE;
        }

        @Override
        public StreamCodec<? super RegistryFriendlyByteBuf, EnchantmentInfoPayload> getCodec() {
            return STREAM_CODEC;
        }

        @Override
        public void handle(EnchantmentInfoPayload msg, IPayloadContext ctx) {
            if (ServerLifecycleHooks.getCurrentServer() != null) {
                return;
            }

            ApothicEnchanting.ENCHANTMENT_INFO.clear();
            ApothicEnchanting.ENCHANTMENT_INFO.putAll(msg.info);
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
