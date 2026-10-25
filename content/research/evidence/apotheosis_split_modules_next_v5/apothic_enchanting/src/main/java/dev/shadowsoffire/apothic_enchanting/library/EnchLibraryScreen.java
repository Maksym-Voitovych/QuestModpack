package dev.shadowsoffire.apothic_enchanting.library;

import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

import javax.annotation.Nullable;

import org.lwjgl.glfw.GLFW;

import com.google.common.base.Strings;
import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.blaze3d.vertex.PoseStack;

import dev.shadowsoffire.apothic_attributes.ApothicAttributes;
import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.placebo.payloads.ButtonClickPayload;
import dev.shadowsoffire.placebo.util.DrawsOnLeft;
import it.unimi.dsi.fastutil.objects.Object2IntMap.Entry;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.resources.language.I18n;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.CommonComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FormattedText;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.neoforged.neoforge.network.PacketDistributor;

public class EnchLibraryScreen extends AbstractContainerScreen<EnchLibraryContainer> implements DrawsOnLeft {

    public static final ResourceLocation TEXTURES = ApothicEnchanting.loc("textures/gui/library.png");
    public static final int MAX_ENTRIES = 5;
    public static final int ENTRY_WIDTH = 113;
    public static final int ENTRY_HEIGHT = 20;

    protected float scrollOffs;
    protected boolean scrolling;
    protected int startIndex;

    protected List<LibrarySlot> data = new ArrayList<>();
    protected EditBox filter = null;

    public EnchLibraryScreen(EnchLibraryContainer container, Inventory inv, Component title) {
        super(container, inv, title);
        this.imageHeight = 230;
        this.containerChanged();
        container.setNotifier(this::containerChanged);
    }

    @Override
    protected void init() {
        super.init();
        this.filter = this.addRenderableWidget(new EditBox(this.font, this.getGuiLeft() + 16, this.getGuiTop() + 16, 110, 11, this.filter, Component.literal("")));
        this.filter.setBordered(false);
        this.filter.setTextColor(0x97714F);
        this.filter.setResponder(t -> this.containerChanged());
        this.setFocused(this.filter);
        this.containerChanged();
    }

    @Override
    public boolean keyPressed(int pKeyCode, int pScanCode, int pModifiers) {
        InputConstants.Key mouseKey = InputConstants.getKey(pKeyCode, pScanCode);
        if (this.minecraft.options.keyInventory.isActiveAndMatches(mouseKey) && this.getFocused() == this.filter) {
            return true;
        }
        return super.keyPressed(pKeyCode, pScanCode, pModifiers);
    }

    @Override
    public void render(GuiGraphics gfx, int mouseX, int mouseY, float partialTicks) {
        super.render(gfx, mouseX, mouseY, partialTicks);
        this.renderTooltip(gfx, mouseX, mouseY);
    }

    @Override
    protected void renderTooltip(GuiGraphics gfx, int mouseX, int mouseY) {
        super.renderTooltip(gfx, mouseX, mouseY);
        LibrarySlot libSlot = this.getHoveredSlot(mouseX, mouseY);
        if (libSlot != null) {
            List<FormattedText> list = new ArrayList<>();

            MutableComponent name = libSlot.ench.value().description().copy().setStyle(Style.EMPTY.withColor(TextColor.fromRgb(0xFFFF80)).withUnderlined(true));
            if (ApothicAttributes.getTooltipFlag().isAdvanced()) {
                name = name.append(Component.literal(" [" + libSlot.ench.getKey().location() + "]").withStyle(Style.EMPTY.withColor(ChatFormatting.DARK_GRAY).withUnderlined(false)));
            }
            list.add(name);

            String descKey = libSlot.ench.getKey().location().toLanguageKey("enchantment") + ".desc";

            if (I18n.exists(descKey) || ApothicAttributes.getTooltipFlag().isAdvanced()) {
                Component txt = Component.translatable(descKey).setStyle(Style.EMPTY.withColor(ChatFormatting.GRAY).withItalic(true));
                list.addAll(this.font.getSplitter().splitLines(txt, this.getGuiLeft() - 16, txt.getStyle()));
                list.add(CommonComponents.SPACE);
            }

            list.add(Component.translatable("tooltip.enchlib.max_lvl", Component.translatable("enchantment.level." + libSlot.maxLvl)).withStyle(ChatFormatting.GRAY));
            list.add(Component.translatable("tooltip.enchlib.points", format(libSlot.points), format(this.menu.getPointCap())).withStyle(ChatFormatting.GRAY));
            list.add(CommonComponents.SPACE);
            ItemStack outSlot = this.menu.ioInv.getItem(1);
            int current = EnchantmentHelper.getEnchantmentsForCrafting(outSlot).getLevel(libSlot.ench);
            boolean shift = Screen.hasShiftDown();
            int targetLevel = shift ? Math.min(libSlot.maxLvl, 1 + (int) (Math.log(libSlot.points + EnchLibraryTile.levelToPoints(current)) / Math.log(2))) : current + 1;
            if (targetLevel == current) targetLevel++;
            int cost = EnchLibraryTile.levelToPoints(targetLevel) - EnchLibraryTile.levelToPoints(current);
            if (targetLevel > libSlot.maxLvl) list.add(Component.translatable("tooltip.enchlib.unavailable").setStyle(Style.EMPTY.withColor(ChatFormatting.RED)));
            else {
                list.add(Component.translatable("tooltip.enchlib.extracting", Component.translatable("enchantment.level." + targetLevel)).withStyle(ChatFormatting.BLUE));
                list.add(Component.translatable("tooltip.enchlib.cost", cost).withStyle(cost > libSlot.points ? ChatFormatting.RED : ChatFormatting.GOLD));
            }
            this.drawOnLeft(gfx, list, mouseY);
        }
    }

    @Override
    protected void renderBg(GuiGraphics gfx, float partial, int mouseX, int mouseY) {
        int left = this.leftPos;
        int top = this.topPos;
        gfx.blit(TEXTURES, left, top, 0, 0, this.imageWidth, this.imageHeight, 307, 256);
        int scrollbarPos = (int) (90F * this.scrollOffs);
        gfx.blit(TEXTURES, left + 13, top + 29 + scrollbarPos, 303, 40 + (this.isScrollBarActive() ? 0 : 12), 4, 12, 307, 256);
        int idx = this.startIndex;
        while (idx < this.startIndex + MAX_ENTRIES && idx < this.data.size()) {
            this.renderEntry(gfx, this.data.get(idx), this.leftPos + 20, this.topPos + 30 + ENTRY_HEIGHT * (idx - this.startIndex), mouseX, mouseY);
            idx++;
        }
    }

    private void renderEntry(GuiGraphics gfx, LibrarySlot data, int x, int y, int mouseX, int mouseY) {
        LibrarySlot hover = this.getHoveredSlot(mouseX, mouseY);
        gfx.blit(TEXTURES, x, y, 194, data == hover ? ENTRY_HEIGHT : 0, ENTRY_WIDTH, ENTRY_HEIGHT, 307, 256);
        int progress = (int) Math.round(85 * Math.sqrt(data.points) / (float) Math.sqrt(this.menu.getPointCap()));
        gfx.blit(TEXTURES, x + 3, y + 14, 197, 42, progress, 3, 307, 256);
        PoseStack stack = gfx.pose();
        stack.pushPose();
        Component txt = data.ench().value().description().plainCopy();
        float scale = 1;
        if (this.font.width(txt) > 85) {
            scale = 85F / this.font.width(txt);
        }
        stack.scale(scale, scale, 1);
        gfx.drawString(this.font, txt, (int) ((x + 3) / scale), (int) ((y + 3) / scale), 0x8EE14D, false);
        stack.popPose();
    }

    @Override
    public boolean mouseClicked(double pMouseX, double pMouseY, int pButton) {
        this.scrolling = false;
        if (this.isHovering(14, 29, 4, 103, pMouseX, pMouseY)) {
            this.scrolling = true;
            this.mouseDragged(pMouseX, pMouseY, pButton, 0, 0);
            return true;
        }

        LibrarySlot libSlot = this.getHoveredSlot((int) pMouseX, (int) pMouseY);
        if (libSlot != null) {
            int id = Minecraft.getInstance().level.registryAccess().registryOrThrow(Registries.ENCHANTMENT).getId(libSlot.ench.value());
            if (Screen.hasShiftDown()) id |= 0x80000000;
            this.menu.onButtonClick(id);
            PacketDistributor.sendToServer(new ButtonClickPayload(id));
            this.minecraft.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.UI_STONECUTTER_SELECT_RECIPE, 1.0F));
            return true;
        }

        if (this.filter.isHovered() && pButton == GLFW.GLFW_MOUSE_BUTTON_RIGHT) {
            this.filter.setValue("");
            return true;
        }

        return super.mouseClicked(pMouseX, pMouseY, pButton);
    }

    @Override
    public boolean mouseDragged(double pMouseX, double pMouseY, int pButton, double pDragX, double pDragY) {
        if (this.scrolling && this.isScrollBarActive()) {
            int barTop = this.topPos + 14;
            int barBot = barTop + 103;
            this.scrollOffs = ((float) pMouseY - barTop - 6F) / (barBot - barTop - 12F) - 0.12F;
            this.scrollOffs = Mth.clamp(this.scrollOffs, 0.0F, 1.0F);
            this.startIndex = (int) (this.scrollOffs * this.getOffscreenRows() + 0.5D);
            return true;
        }
        else {
            return super.mouseDragged(pMouseX, pMouseY, pButton, pDragX, pDragY);
        }
    }

    @Override
    public boolean mouseScrolled(double pMouseX, double pMouseY, double pScrollX, double pScrollY) {
        if (this.isScrollBarActive()) {
            int i = this.getOffscreenRows();
            this.scrollOffs = (float) (this.scrollOffs - pScrollY / i);
            this.scrollOffs = Mth.clamp(this.scrollOffs, 0.0F, 1.0F);
            this.startIndex = (int) (this.scrollOffs * i + 0.5D);
        }
        return true;
    }

    private boolean isScrollBarActive() {
        return this.data.size() > MAX_ENTRIES;
    }

    protected int getOffscreenRows() {
        return this.data.size() - MAX_ENTRIES;
    }

    private void containerChanged() {
        this.data.clear();
        List<Entry<Holder<Enchantment>>> entries = this.filter(this.menu.getPointsForDisplay());
        for (Entry<Holder<Enchantment>> e : entries) {
            this.data.add(new LibrarySlot(e.getKey(), e.getIntValue(), this.menu.getMaxLevel(e.getKey())));
        }

        if (!this.isScrollBarActive()) {
            this.scrollOffs = 0.0F;
            this.startIndex = 0;
        }
        Collections.sort(this.data, Comparator.comparing(slot -> slot.ench.value().description().getString()));
    }

    private List<Entry<Holder<Enchantment>>> filter(List<Entry<Holder<Enchantment>>> list) {
        return list.stream().filter(this::isAllowedByItem).filter(this::isAllowedBySearch).toList();
    }

    private boolean isAllowedByItem(Entry<Holder<Enchantment>> e) {
        ItemStack stack = this.menu.ioInv.getItem(2);
        return stack.isEmpty() || stack.supportsEnchantment(e.getKey());
    }

    private boolean isAllowedBySearch(Entry<Holder<Enchantment>> e) {
        String name = e.getKey().value().description().getString().toLowerCase(Locale.ROOT);
        String search = this.filter == null ? "" : this.filter.getValue().trim().toLowerCase(Locale.ROOT);
        return Strings.isNullOrEmpty(search) || ChatFormatting.stripFormatting(name).contains(search);
    }

    @Nullable
    public LibrarySlot getHoveredSlot(int mouseX, int mouseY) {
        for (int i = 0; i < MAX_ENTRIES; i++) {
            if (this.startIndex + i < this.data.size()) {
                if (this.isHovering(21, 31 + i * ENTRY_HEIGHT, ENTRY_WIDTH, ENTRY_HEIGHT - 2, mouseX, mouseY)) {
                    return this.data.get(this.startIndex + i);
                }
            }
        }
        return null;
    }

    @Override
    protected void renderLabels(GuiGraphics pGuiGraphics, int pMouseX, int pMouseY) {}

    @Override
    public int getSlotColor(int index) {
        return 0x40FFFFFF;
    }

    private static record LibrarySlot(Holder<Enchantment> ench, int points, int maxLvl) {}

    private static DecimalFormat f = new DecimalFormat("##.#");

    private static String format(int n) {
        int log = (int) StrictMath.log10(n);
        if (log <= 3) return String.valueOf(n);
        else if (log <= 6) return f.format(n / 1000D) + "K";
        else if (log <= 8) return f.format(n / 1000000D) + "M";
        else return f.format(n / 1000000000D) + "B";
    }

}
