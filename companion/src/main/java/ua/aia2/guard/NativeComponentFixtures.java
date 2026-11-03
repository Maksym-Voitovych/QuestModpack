package ua.aia2.guard;

import net.minecraft.SharedConstants;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.registries.RegisterEvent;

import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Development-only codec fixture. Never registers a CDG item/component or a
 * normal-play resource; the three opt-in gates mirror the owned smoke runner.
 */
@EventBusSubscriber(modid = Aia2MachineGuard.MOD_ID, bus = EventBusSubscriber.Bus.MOD)
public final class NativeComponentFixtures {
    static final ResourceLocation PROFILE_ID = ResourceLocation.fromNamespaceAndPath(
            Aia2MachineGuard.MOD_ID, "native_mold_profile");
    private static DataComponentType<ResourceLocation> profile;

    private NativeComponentFixtures() {}

    @SubscribeEvent
    public static void register(RegisterEvent event) {
        if (!Boolean.getBoolean("aia2.guard.nativeSmoke") || !SharedConstants.IS_RUNNING_IN_IDE
                || !Files.isRegularFile(Path.of(".aia2-native-smoke-allow"))
                || !event.getRegistryKey().equals(Registries.DATA_COMPONENT_TYPE)) return;
        DataComponentType<ResourceLocation> fixture = DataComponentType.<ResourceLocation>builder()
                .persistent(ResourceLocation.CODEC)
                .networkSynchronized(ResourceLocation.STREAM_CODEC)
                .build();
        event.register(Registries.DATA_COMPONENT_TYPE, PROFILE_ID, () -> fixture);
        profile = fixture;
    }

    static DataComponentType<ResourceLocation> profile() {
        if (profile == null) throw new IllegalStateException("Owned native component fixture was not registered");
        return profile;
    }
}
