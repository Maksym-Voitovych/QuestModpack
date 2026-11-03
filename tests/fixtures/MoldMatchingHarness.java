package ua.aia2.tests;

import dev.ftb.mods.ftbquests.api.ItemFilterAdapter;
import dev.ftb.mods.ftbquests.integration.item_filtering.ItemMatchingSystem;
import dev.ftb.mods.ftbquests.integration.item_filtering.ItemMatchingSystem.ComponentMatchType;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Actual FTB matcher and adapter interface; item/component maps are modeled hosts. */
public final class MoldMatchingHarness {
    private static final Item MOLD = new Item("createdieselgenerators:mold");
    private static final Item OTHER = new Item("minecraft:iron_ingot");
    private static final DataComponentType<ResourceLocation> PROFILE =
            new DataComponentType<>("createdieselgenerators:mold_type");
    private static final DataComponentType<String> NAME = new DataComponentType<>("minecraft:custom_name");
    private static final String[] PROFILES = {"bowl", "lines", "chain", "bar"};
    private static int assertions;

    private static void check(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    private static ItemStack mold(String profile) {
        return new ItemStack(MOLD, 1).with(PROFILE,
                ResourceLocation.parse("createdieselgenerators:"+profile));
    }

    private static boolean matches(ItemStack filter, ItemStack candidate, ComponentMatchType mode) {
        return ItemMatchingSystem.INSTANCE.doesItemMatch(filter, candidate, mode, null);
    }

    private static void plainMoldMatching() {
        check(ItemMatchingSystem.INSTANCE.adapters().isEmpty(),
                "Ordinary Mold tests start without filter adapters; adapter recognition is a separate scope");
        for (String shape : PROFILES) {
            ItemStack filter = mold(shape);
            for (String candidateShape : PROFILES) {
                boolean result = matches(filter, mold(candidateShape), ComponentMatchType.FUZZY);
                check(result == shape.equals(candidateShape),
                        "A wrong Mold profile must not satisfy fuzzy matching: "+shape+" vs "+candidateShape);
            }
            check(!matches(filter, new ItemStack(MOLD, 1), ComponentMatchType.FUZZY),
                    "Generic Mold without profile cannot satisfy a specialized objective");
            check(!matches(filter, mold(shape).with(PROFILE, null), ComponentMatchType.FUZZY),
                    "Removing a component has absent semantics, not an equal null profile");
            check(!matches(filter, new ItemStack(OTHER, 1).with(PROFILE,
                    ResourceLocation.parse("createdieselgenerators:"+shape)), ComponentMatchType.FUZZY),
                    "Other item cannot satisfy Mold task even with the same component");
            check(!matches(filter, ItemStack.EMPTY, ComponentMatchType.FUZZY),
                    "Normal empty inventory slots do not match");
            check(!matches(filter, filter.with(PROFILE, ResourceLocation.parse(shape)), ComponentMatchType.FUZZY),
                    "Bare identifier resolves to minecraft namespace and must not match full CDG profile");
            check(!matches(filter, filter.with(PROFILE,
                    ResourceLocation.parse("createdieselgenerators:unknown_profile")), ComponentMatchType.FUZZY),
                    "A different valid identifier is not the requested profile");
            check(matches(filter, filter.with(NAME, "Моя форма"), ComponentMatchType.FUZZY),
                    "Fuzzy allows extra candidate custom_name while retaining the required shape");
            check(!matches(filter, filter.with(NAME, "Моя форма"), ComponentMatchType.STRICT),
                    "Strict equality rejects extra candidate components");
            check(matches(filter, mold(shape), ComponentMatchType.STRICT),
                    "Strict accepts identical effective component maps");
            check(matches(filter, new ItemStack(MOLD, 1), ComponentMatchType.NONE),
                    "NONE deliberately ignores shape, proving why it cannot be used for profile tasks");
            check(matches(filter, filter.copyWithCount(64), ComponentMatchType.FUZZY),
                    "Stack count is handled by task progress, not profile identity");
            check(matches(filter, filter.copyWithCount(64), ComponentMatchType.STRICT),
                    "Strict stack identity also ignores count");
            check(!matches(filter, filter.with(ItemStack.MAX_STACK_SIZE, 16), ComponentMatchType.FUZZY),
                    "Fuzzy compares default effective components, not only the explicit profile patch");
            check(!matches(filter, filter.with(ItemStack.RARITY, "rare"), ComponentMatchType.FUZZY),
                    "Changed default rarity is also constrained by the filter");
            check(matches(filter, filter, ComponentMatchType.FUZZY),
                    "Same non-null stack identity follows FTB short-circuit behavior");
        }
        check(ComponentMatchType.NAME_MAP.get("fuzzy") == ComponentMatchType.FUZZY,
                "Serialized mode fuzzy resolves explicitly");
        check(ComponentMatchType.NAME_MAP.get("strict") == ComponentMatchType.STRICT,
                "Serialized mode strict resolves explicitly");
        check(ComponentMatchType.NAME_MAP.get("none") == ComponentMatchType.NONE,
                "Serialized mode none resolves explicitly");
        check(ComponentMatchType.NAME_MAP.get("ALL") == ComponentMatchType.NONE,
                "Unknown enum spelling falls back to NONE and must be rejected by author validation");
        check(ComponentMatchType.NAME_MAP.get("fuzzzzy") == ComponentMatchType.NONE,
                "A typo is dangerous because it falls back to shape-agnostic NONE");
        check(ItemMatchingSystem.INSTANCE.getAllMatchingStacks(mold("lines"), null).size() == 1,
                "An ordinary Mold displays its own component-bearing filter stack");
        boolean nullRejected = false;
        try { matches(mold("lines"), null, ComponentMatchType.FUZZY); }
        catch (NullPointerException expected) { nullRejected = true; }
        check(nullRejected, "The matcher is not a null-stack API; ItemTask supplies non-null inventory stacks");
    }

    private static void adapterBoundary() {
        ItemFilterAdapter adapter = new ItemFilterAdapter() {
            @Override public String getName() { return "explicit host-only adapter"; }
            @Override public boolean isFilterStack(ItemStack stack) { return stack.getItem() == MOLD; }
            @Override public boolean doesItemMatch(ItemStack filter, ItemStack candidate,
                                                    HolderLookup.Provider provider) { return true; }
            @Override public Matcher getMatcher(ItemStack stack, HolderLookup.Provider provider) {
                return ignored -> true;
            }
            @Override public ItemStack makeTagFilterStack(TagKey<Item> tag) { return ItemStack.EMPTY; }
        };
        ItemMatchingSystem.INSTANCE.registerFilterAdapter(adapter);
        check(ItemMatchingSystem.INSTANCE.isItemFilter(mold("lines")),
                "Adapter recognition is a different explicit matching boundary");
        check(matches(mold("lines"), mold("bowl"), ComponentMatchType.FUZZY),
                "A recognized filter adapter overrides ordinary component matching");
        check(matches(mold("lines"), new ItemStack(OTHER, 1), ComponentMatchType.STRICT),
                "Even strict is subordinate to an explicitly recognized filter adapter");
        boolean immutable = false;
        try { ItemMatchingSystem.INSTANCE.adapters().clear(); }
        catch (UnsupportedOperationException expected) { immutable = true; }
        check(immutable, "Adapter collection cannot be silently cleared by a caller");
    }

    public static void main(String[] args) {
        plainMoldMatching();
        adapterBoundary(); // Last: the actual singleton intentionally retains the registered adapter.
        System.out.println(assertions+" Mold actual-FTB-matcher assertions PASS; MC components/NameMap/display host modeled; no Minecraft or optional-mod dispatch");
    }
}
