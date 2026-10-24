package velrondevs.botania.common.advancements;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.advancements.Criterion;
import net.minecraft.advancements.critereon.*;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import org.jetbrains.annotations.NotNull;

import java.util.Optional;

import static velrondevs.botania.common.lib.ResourceLocationHelper.prefix;

public class AlfheimPortalTrigger extends SimpleCriterionTrigger<AlfheimPortalTrigger.Instance> {
	public static final ResourceLocation ID = prefix("open_elf_portal");
	public static final AlfheimPortalTrigger INSTANCE = new AlfheimPortalTrigger();

	private AlfheimPortalTrigger() {}

	@NotNull
	@Override
	public Codec<Instance> codec() {
		return Instance.CODEC;
	}

	public void trigger(ServerPlayer player, ServerLevel world, BlockPos pos, ItemStack wand) {
		trigger(player, instance -> instance.test(world, pos, wand));
	}

	public record Instance(Optional<ContextAwarePredicate> player, Optional<ItemPredicate> wand,
			Optional<LocationPredicate> pos) implements SimpleCriterionTrigger.SimpleInstance {
		public static final Codec<Instance> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				EntityPredicate.ADVANCEMENT_CODEC.optionalFieldOf("player").forGetter(Instance::player),
				ItemPredicate.CODEC.optionalFieldOf("wand").forGetter(Instance::wand),
				LocationPredicate.CODEC.optionalFieldOf("location").forGetter(Instance::pos)
		).apply(instance, Instance::new));

		public static Criterion<Instance> openPortal(Optional<ItemPredicate> wand, Optional<LocationPredicate> pos) {
			return INSTANCE.createCriterion(new Instance(Optional.empty(), wand, pos));
		}

		public static Criterion<Instance> openPortal() {
			return openPortal(Optional.empty(), Optional.empty());
		}

		boolean test(ServerLevel world, BlockPos pos, ItemStack wand) {
			return (this.wand.isEmpty() || this.wand.get().test(wand))
					&& (this.pos.isEmpty() || this.pos.get().matches(world, pos.getX(), pos.getY(), pos.getZ()));
		}
	}
}
