package velrondevs.botania.common.helper;

import com.google.gson.JsonObject;
import com.mojang.serialization.JsonOps;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import org.jetbrains.annotations.Contract;
import org.jetbrains.annotations.Nullable;

import velrondevs.botania.api.mana.ManaItem;
import velrondevs.botania.xplat.XplatAbstractions;

import java.util.function.Consumer;

public final class ItemNBTHelper {

	private static final int[] EMPTY_INT_ARRAY = new int[0];
	private static final long[] EMPTY_LONG_ARRAY = new long[0];

	@SuppressWarnings("deprecation")
	public static CompoundTag peekTag(ItemStack stack) {
		return stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).getUnsafe();
	}

	public static CompoundTag getTagCopy(ItemStack stack) {
		return stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
	}

	public static boolean hasTag(ItemStack stack) {
		return stack.has(DataComponents.CUSTOM_DATA);
	}

	public static void setTag(ItemStack stack, @Nullable CompoundTag tag) {
		if (tag == null || tag.isEmpty()) {
			stack.remove(DataComponents.CUSTOM_DATA);
		} else {
			stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
		}
	}

	public static void updateTag(ItemStack stack, Consumer<CompoundTag> updater) {
		CustomData.update(DataComponents.CUSTOM_DATA, stack, updater);
	}

	public static void set(ItemStack stack, String tag, Tag nbt) {
		updateTag(stack, t -> t.put(tag, nbt));
	}

	public static void setBoolean(ItemStack stack, String tag, boolean b) {
		updateTag(stack, t -> t.putBoolean(tag, b));
	}

	public static void setByte(ItemStack stack, String tag, byte b) {
		updateTag(stack, t -> t.putByte(tag, b));
	}

	public static void setShort(ItemStack stack, String tag, short s) {
		updateTag(stack, t -> t.putShort(tag, s));
	}

	public static void setInt(ItemStack stack, String tag, int i) {
		updateTag(stack, t -> t.putInt(tag, i));
	}

	public static void setIntArray(ItemStack stack, String tag, int[] val) {
		updateTag(stack, t -> t.putIntArray(tag, val));
	}

	public static void setLong(ItemStack stack, String tag, long l) {
		updateTag(stack, t -> t.putLong(tag, l));
	}

	public static void setLongArray(ItemStack stack, String tag, long[] val) {
		updateTag(stack, t -> t.putLongArray(tag, val));
	}

	public static void setFloat(ItemStack stack, String tag, float f) {
		updateTag(stack, t -> t.putFloat(tag, f));
	}

	public static void setDouble(ItemStack stack, String tag, double d) {
		updateTag(stack, t -> t.putDouble(tag, d));
	}

	public static void setCompound(ItemStack stack, String tag, CompoundTag cmp) {
		updateTag(stack, t -> t.put(tag, cmp));
	}

	public static void setString(ItemStack stack, String tag, String s) {
		updateTag(stack, t -> t.putString(tag, s));
	}

	public static void setList(ItemStack stack, String tag, ListTag list) {
		updateTag(stack, t -> t.put(tag, list));
	}

	public static void removeEntry(ItemStack stack, String tag) {
		if (verifyExistance(stack, tag)) {
			updateTag(stack, t -> t.remove(tag));
		}
	}

	public static boolean verifyExistance(ItemStack stack, String tag) {
		return !stack.isEmpty() && peekTag(stack).contains(tag);
	}

	public static boolean verifyType(ItemStack stack, String tag, Class<? extends Tag> tagClass) {
		return !stack.isEmpty() && tagClass.isInstance(peekTag(stack).get(tag));
	}

	@Nullable
	public static Tag get(ItemStack stack, String tag) {
		Tag t = verifyExistance(stack, tag) ? peekTag(stack).get(tag) : null;
		return t == null ? null : t.copy();
	}

	public static boolean getBoolean(ItemStack stack, String tag, boolean defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getBoolean(tag) : defaultExpected;
	}

	public static byte getByte(ItemStack stack, String tag, byte defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getByte(tag) : defaultExpected;
	}

	public static short getShort(ItemStack stack, String tag, short defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getShort(tag) : defaultExpected;
	}

	public static int getInt(ItemStack stack, String tag, int defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getInt(tag) : defaultExpected;
	}

	public static int[] getIntArray(ItemStack stack, String tag) {
		return verifyExistance(stack, tag) ? peekTag(stack).getIntArray(tag).clone() : EMPTY_INT_ARRAY;
	}

	public static long getLong(ItemStack stack, String tag, long defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getLong(tag) : defaultExpected;
	}

	public static long[] getLongArray(ItemStack stack, String tag) {
		return verifyExistance(stack, tag) ? peekTag(stack).getLongArray(tag).clone() : EMPTY_LONG_ARRAY;
	}

	public static float getFloat(ItemStack stack, String tag, float defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getFloat(tag) : defaultExpected;
	}

	public static double getDouble(ItemStack stack, String tag, double defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getDouble(tag) : defaultExpected;
	}

	@Nullable
	@Contract("_, _, false -> !null")
	public static CompoundTag getCompound(ItemStack stack, String tag, boolean nullifyOnFail) {
		return verifyExistance(stack, tag) ? peekTag(stack).getCompound(tag).copy() : nullifyOnFail ? null : new CompoundTag();
	}

	@Nullable
	@Contract("_, _, !null -> !null")
	public static String getString(ItemStack stack, String tag, String defaultExpected) {
		return verifyExistance(stack, tag) ? peekTag(stack).getString(tag) : defaultExpected;
	}

	@Nullable
	@Contract("_, _, _, false -> !null")
	public static ListTag getList(ItemStack stack, String tag, int objtype, boolean nullifyOnFail) {
		return verifyExistance(stack, tag) ? peekTag(stack).getList(tag, objtype).copy() : nullifyOnFail ? null : new ListTag();
	}

	public static int getFullness(ManaItem item) {
		int mana = item.getMana();
		if (mana == 0) {
			return 0;
		} else if (mana == item.getMaxMana()) {
			return 2;
		} else {
			return 1;
		}
	}

	public static ItemStack duplicateAndClearMana(ItemStack stack) {
		ItemStack copy = stack.copy();
		ManaItem manaItem = XplatAbstractions.INSTANCE.findManaItem(copy);
		if (manaItem != null) {
			manaItem.addMana(-manaItem.getMana());
		}
		return copy;
	}

	public static boolean matchTagAndManaFullness(ItemStack stack1, ItemStack stack2) {
		if (!ItemStack.isSameItem(stack1, stack2)) {
			return false;
		}
		ManaItem manaItem1 = XplatAbstractions.INSTANCE.findManaItem(stack1);
		ManaItem manaItem2 = XplatAbstractions.INSTANCE.findManaItem(stack2);
		if (manaItem1 != null && manaItem2 != null) {
			if (getFullness(manaItem1) != getFullness(manaItem2)) {
				return false;
			} else {
				return ItemStack.matches(duplicateAndClearMana(stack1), duplicateAndClearMana(stack2));
			}
		}
		return ItemStack.isSameItemSameComponents(stack1, stack2);
	}

	public static JsonObject serializeStack(ItemStack stack) {
		return ItemStack.CODEC.encodeStart(JsonOps.INSTANCE, stack).getOrThrow().getAsJsonObject();
	}

	public static void renameTag(CompoundTag nbt, String oldName, String newName) {
		Tag tag = nbt.get(oldName);
		if (tag != null) {
			nbt.remove(oldName);
			nbt.put(newName, tag);
		}
	}
}
