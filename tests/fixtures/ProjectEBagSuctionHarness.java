package ua.aia2.guard.mixin;

import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import net.minecraft.core.NonNullList;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import ua.aia2.guard.ProjectEPassiveAccess;

/** Actual redirect and real GuardPolicy; native lookup/host/passive API are modeled. */
public final class ProjectEBagSuctionHarness {
    private static int checks;
    private static Method filter;
    private static void check(boolean value, String reason) {
        checks++;
        if (!value) throw new AssertionError(reason);
    }
    private static boolean empty(ItemStack stack, Player player, NonNullList<ItemStack> inventory) throws Exception {
        return (boolean) filter.invoke(null, stack, player, inventory);
    }
    // Same predicates/order as the two frozen native isEmpty call sites. The
    // production redirect does not replace or copy this selection loop.
    private static ItemStack select(Player player, NonNullList<ItemStack> inventory) throws Exception {
        for (ItemStack stack : inventory) {
            if (!empty(stack, player, inventory) && stack.bag) {
                for (ItemStack ring : stack.contents) {
                    if (!empty(ring, player, inventory) && (ring.id.equals("projecte:black_hole_band") || ring.id.equals("projecte:void_ring"))) {
                        if (ring.active) return stack;
                    }
                }
            }
        }
        return ItemStack.EMPTY;
    }
    private static ItemStack bag(String id, ItemStack... contents) {
        var result = new ItemStack(id); result.bag = true; result.contents = List.of(contents); return result;
    }
    private static ItemStack active(String id) {
        var result = new ItemStack(id); result.active = true; return result;
    }
    private static NonNullList<ItemStack> inventory(ItemStack... stacks) {
        var result = new NonNullList<ItemStack>(); result.addAll(List.of(stacks)); return result;
    }
    public static void main(String[] args) throws Exception {
        filter = ProjectEBagSuctionMixin.class.getDeclaredMethod("aia2$unavailableSuctionStack", ItemStack.class, Player.class, NonNullList.class);
        filter.setAccessible(true);
        var policy = ProjectEPassiveAccess.policy;
        policy.setRules(Map.of("projecte:white_alchemical_bag",45,"fixture:future_bag",47,
                "projecte:black_hole_band",45,"projecte:void_ring",47));
        policy.setTeamProgress("early",0); policy.setTeamProgress("current",44); policy.setTeamProgress("late",46); policy.setReady();
        var early = new Player("early"); var current = new Player("current"); var late = new Player("late");
        var ring = active("projecte:black_hole_band"); var white = bag("projecte:white_alchemical_bag", ring);
        var single = inventory(white);
        check(select(early,single)==ItemStack.EMPTY,"imported active bag/ring cannot redirect early player's pickups");
        check(select(current,single)==white,"unlocked active native bag remains selected");
        check(!empty(white,current,single)&&!empty(ring,current,single),"both actual authorized stacks pass native predicates");
        check(empty(white,early,single)&&empty(ring,early,single),"both actual unauthorized stacks are excluded");
        var futureBag=bag("fixture:future_bag",ring);
        check(select(current,inventory(futureBag))==ItemStack.EMPTY,"bag's actual item floor is checked separately from ring");
        check(select(late,inventory(futureBag))==futureBag,"actual addon bag unlocks at its own floor");
        var voidRing=active("projecte:void_ring"); var laterRingBag=bag("projecte:white_alchemical_bag",voidRing);
        check(select(current,inventory(laterRingBag))==ItemStack.EMPTY,"inner ring's own future floor is enforced");
        check(select(late,inventory(laterRingBag))==laterRingBag,"inner ring becomes selectable after its own unlock");
        check(select(current,inventory(futureBag,laterRingBag,white))==white,"locked earlier candidates do not hide a later permitted native bag");
        ring.active=false;check(select(current,single)==ItemStack.EMPTY,"native active-mode predicate is preserved");ring.active=true;
        check(select(current,inventory(bag("projecte:white_alchemical_bag",active("minecraft:stick"))))==ItemStack.EMPTY,"unrelated active item cannot become a suction ring");
        check(select(current,inventory(new ItemStack("projecte:white_alchemical_bag")))==ItemStack.EMPTY,"non-bag type remains rejected even with same modeled ID");
        int count=ring.count; boolean active=ring.active;
        select(early,single);
        check(ring.count==count&&ring.active==active&&white.contents.get(0)==ring,"denial preserves contents/count/active components");
        current.live="early";check(select(current,single)==ItemStack.EMPTY,"changed live team cannot retain old synchronized privileges");current.live="current";
        current.synced=false;check(select(current,single)==ItemStack.EMPTY,"unsynchronized wearer fails closed");current.synced=true;
        current.fake=true;check(select(current,single)==ItemStack.EMPTY,"fake player cannot redirect pickups through personal bag");current.fake=false;
        policy.setTeamProgress("current",43);check(select(current,single)==ItemStack.EMPTY,"same imported items pause immediately after stage downgrade");
        policy.setTeamProgress("current",44);check(select(current,single)==white,"same unchanged items resume after stage restoration");
        policy.clear();check(select(current,single)==ItemStack.EMPTY,"unready reload window fails closed");
        var client=new Player("early");client.client=true;
        check(select(client,single)==white,"client lookup is unchanged; no server authorization is fabricated");
        check(empty(ItemStack.EMPTY,client,single),"empty remains empty on client too");
        System.out.println("ProjectEBagSuctionHarness: "+checks+" actual-handler/real-policy assertions; modeled native selection and passive API, no optional ProjectE dispatch");
    }
}
