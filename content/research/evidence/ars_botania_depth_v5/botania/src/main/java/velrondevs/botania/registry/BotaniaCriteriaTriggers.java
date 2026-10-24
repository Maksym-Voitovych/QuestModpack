package velrondevs.botania.registry;

import net.minecraft.advancements.CriterionTrigger;
import net.minecraft.resources.ResourceLocation;

import java.util.function.BiConsumer;

import velrondevs.botania.common.advancements.AlfheimPortalBreadTrigger;
import velrondevs.botania.common.advancements.AlfheimPortalTrigger;
import velrondevs.botania.common.advancements.CorporeaRequestTrigger;
import velrondevs.botania.common.advancements.GaiaGuardianNoArmorTrigger;
import velrondevs.botania.common.advancements.LokiPlaceTrigger;
import velrondevs.botania.common.advancements.ManaBlasterTrigger;
import velrondevs.botania.common.advancements.RelicBindTrigger;
import velrondevs.botania.common.advancements.UseItemSuccessTrigger;

public class BotaniaCriteriaTriggers {
	public static void init(BiConsumer<CriterionTrigger<?>, ResourceLocation> r) {
		r.accept(AlfheimPortalTrigger.INSTANCE, AlfheimPortalTrigger.ID);
		r.accept(CorporeaRequestTrigger.INSTANCE, CorporeaRequestTrigger.ID);
		r.accept(GaiaGuardianNoArmorTrigger.INSTANCE, GaiaGuardianNoArmorTrigger.ID);
		r.accept(RelicBindTrigger.INSTANCE, RelicBindTrigger.ID);
		r.accept(UseItemSuccessTrigger.INSTANCE, UseItemSuccessTrigger.ID);
		r.accept(ManaBlasterTrigger.INSTANCE, ManaBlasterTrigger.ID);
		r.accept(LokiPlaceTrigger.INSTANCE, LokiPlaceTrigger.ID);
		r.accept(AlfheimPortalBreadTrigger.INSTANCE, AlfheimPortalBreadTrigger.ID);
	}
}
