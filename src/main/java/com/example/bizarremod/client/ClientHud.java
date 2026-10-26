package com.example.bizarremod.client;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.network.HudStatePacket;
import com.mojang.blaze3d.matrix.MatrixStack;
import com.mojang.blaze3d.systems.RenderSystem;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.AbstractGui;
import net.minecraft.client.resources.I18n;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * HUD di combattimento in stile Minecraft: slot grigi come la hotbar, cornice bianca sulla tecnica
 * selezionata, etichetta azzurra con il tasto tra parentesi, barra dell'energia come quella dell'esperienza.
 */
@Mod.EventBusSubscriber(modid = BizarreMod.MOD_ID, value = Dist.CLIENT)
public class ClientHud extends AbstractGui {
    public static final int GOLD = 0xFFE1BD69, PURPLE = 0xFFAA70EB;
    /** Dimensioni dell'HUD a scala 100% (in pixel GUI): servono a HudLayout e all'editor. */
    public static final int W = 140, H = 96;
    private static final int AQUA = 0xFF55FFFF, GRAY = 0xFFAAAAAA, RED = 0xFFFF5555, XP_GREEN = 0xFF80FF20;
    private static final int SLOT = 22, FIRST_SLOT_X = 28, SLOT_STEP = 24;

    public static HudStatePacket state;
    private static long received;
    private static final Map<String, ResourceLocation> TEXTURES = new HashMap<String, ResourceLocation>();

    public static void accept(HudStatePacket packet) { state = packet; received = System.nanoTime(); }
    public static void clear() { state = null; }
    public static int ticks(int i) {
        return state == null ? 0 : Math.max(0, state.remaining[i] - (int)((System.nanoTime() - received) / 50000000L));
    }
    public static String seconds(int ticks) { return String.format(Locale.ROOT, "%.1fs", ticks / 20.0); }
    public static int styleColor() {
        if (state == null) return PURPLE;
        if ("hamon".equals(state.styleId)) return GOLD;
        if ("spin".equals(state.styleId)) return 0xFF64D9AA;
        return 0xFFF47F8D;
    }
    public static String tr(String key, Object... args) { return I18n.format("gui.bizarremod." + key, args); }

    /** Nome dello Stand tradotto sul client (il server non conosce le traduzioni della mod). */
    public static String standName() {
        if (state == null) return "";
        return state.hasStand ? I18n.format("stand.bizarremod." + state.standId) : tr("no_stand");
    }
    /** Nome dello stile tradotto sul client. */
    public static String styleName() {
        if (state == null) return "";
        return state.hasStyle ? I18n.format("style.bizarremod." + state.styleId) : tr("no_style");
    }

    public static String requirement() {
        if (state == null || !state.hasStyle) return tr("no_style");
        if (state.equipped) return tr("equipped");
        return tr("spin".equals(state.styleId) ? "need_ball" : "need_gloves");
    }
    public static void panel(MatrixStack m, int x, int y, int w, int h, int accent) {
        fill(m, x, y, x+w, y+h, 0xE9141021);
        fill(m, x, y, x+w, y+1, accent); fill(m, x, y+h-1, x+w, y+h, accent);
        fill(m, x, y, x+1, y+h, accent); fill(m, x+w-1, y, x+w, y+h, accent);
        fill(m, x+2, y+2, x+5, y+h-2, 0xFF4A2B67);
    }
    public static void text(MatrixStack m, String text, int x, int y, int color, int maxWidth) {
        Minecraft mc = Minecraft.getInstance();
        mc.fontRenderer.drawString(m, mc.fontRenderer.trimStringToWidth(text, Math.max(0, maxWidth)), x, y, color);
    }
    /** Testo con ombra, come nell'interfaccia di Minecraft. */
    private static void shadow(MatrixStack m, String text, int x, int y, int color, int maxWidth) {
        Minecraft mc = Minecraft.getInstance();
        mc.fontRenderer.drawStringWithShadow(m, mc.fontRenderer.trimStringToWidth(text, Math.max(0, maxWidth)), x, y, color);
    }

    @SubscribeEvent
    public static void overlay(RenderGameOverlayEvent.Post e) {
        Minecraft mc = Minecraft.getInstance();
        if (e.getType() != RenderGameOverlayEvent.ElementType.ALL || mc.player == null
                || mc.gameSettings.hideGUI || mc.currentScreen != null || !HudLayout.get().visible
                || state == null || (!state.hasStand && !state.hasStyle)) return;
        draw(e.getMatrixStack(), mc.getMainWindow().getScaledWidth(), mc.getMainWindow().getScaledHeight(), false);
    }

    public static void draw(MatrixStack m, int w, int h, boolean editing) {
        HudLayout layout = HudLayout.get();
        m.push();
        m.translate(layout.left(w,h), layout.top(w,h), 0);
        float scale = (float)layout.effectiveScale(w,h); m.scale(scale, scale, 1);
        if (editing) {  // contorno bianco: serve a trascinare l'HUD nell'editor
            fill(m, -2, -2, W + 2, -1, 0xFFFFFFFF); fill(m, -2, H + 1, W + 2, H + 2, 0xFFFFFFFF);
            fill(m, -2, -2, -1, H + 2, 0xFFFFFFFF); fill(m, W + 1, -2, W + 2, H + 2, 0xFFFFFFFF);
        }
        row(m, 0, false);
        row(m, 38, true);
        energyBar(m, 77);
        if (state != null && state.hasStyle && !state.equipped) {
            shadow(m, requirement(), 0, 87, RED, W);
        }
        m.pop();
    }

    // ---------------------------------------------------------------- disegno

    /** Una riga: casella dell'icona (Stand o stile) + 4 slot per le tecniche + etichetta della tecnica scelta. */
    private static void row(MatrixStack m, int y, boolean style) {
        boolean exists = state == null || (style ? state.hasStyle : state.hasStand);
        String id = state == null ? (style ? "spin" : "star_platinum") : (style ? state.styleId : state.standId);
        int color = style ? styleColor() : standColor(id);

        slotBox(m, 0, y, false, !exists);
        if (exists) icon(m, (style ? "style_" : "stand_") + id, 3, y + 3, 0xFFFFFFFF, 1f);

        int selected = state == null ? 0 : (style ? state.selectedStyle : state.selectedStand);
        boolean usableGroup = state == null || (style ? state.equipped : state.active);
        for (int j = 0; j < 4; j++) {
            int x = FIRST_SLOT_X + j * SLOT_STEP, i = j + (style ? 4 : 0);
            boolean chosen = exists && j == selected;
            slotBox(m, x, y, chosen, !exists);
            if (!exists) continue;
            int cd = ticks(i);
            boolean usable = cd == 0 && usableGroup && (state == null || state.energy >= state.costs[i]);
            icon(m, "move_" + j, x + 3, y + 3, color, usable ? 1f : 0.4f);
            if (cd > 0) {  // ricarica: velo bianco che scende, come per gli oggetti di Minecraft
                int total = state == null ? 1 : Math.max(state.duration[i], 8);
                int height = (int) Math.ceil(16 * Math.min(1.0, (double) cd / total));
                fill(m, x + 3, y + 19 - height, x + 19, y + 19, 0x80FFFFFF);
                String sec = String.valueOf((cd + 19) / 20);
                shadow(m, sec, x + 11 - Minecraft.getInstance().fontRenderer.getStringWidth(sec) / 2, y + 7, 0xFFFFFFFF, 20);
            } else {       // numero dello slot in basso a destra, come il numero di oggetti
                String n = String.valueOf(j + 1);
                shadow(m, n, x + 19 - Minecraft.getInstance().fontRenderer.getStringWidth(n), y + 12, 0xFFFFFFFF, 20);
            }
        }

        // etichetta sotto la riga: "[V] Nome tecnica" in azzurro
        if (state == null) return;
        if (!exists) {
            shadow(m, style ? tr("no_style") : tr("no_stand"), 0, y + 25, GRAY, W);
        } else if (!style && !state.active) {
            shadow(m, "[R] " + tr("stand_off"), 0, y + 25, GRAY, W);
        } else {
            String name = state.names[selected + (style ? 4 : 0)];
            shadow(m, "[" + (style ? "C" : "V") + "] " + name, 0, y + 25, AQUA, W);
        }
    }

    /** Barra dell'energia con l'aspetto della barra dell'esperienza. */
    private static void energyBar(MatrixStack m, int y) {
        int energy = state == null ? 100 : Math.max(0, Math.min(100, Math.round(state.energy)));
        int fillWidth = (int) (110 * energy / 100.0);
        fill(m, 0, y, 112, y + 5, 0xFF000000);
        fill(m, 1, y + 1, 111, y + 4, 0xFF3C3C3C);
        if (fillWidth > 0) {
            fill(m, 1, y + 1, 1 + fillWidth, y + 4, XP_GREEN);
            fill(m, 1, y + 1, 1 + fillWidth, y + 2, 0xFFC4FF8C);
        }
        shadow(m, String.valueOf(energy), 116, y - 2, XP_GREEN, 24);
    }

    /** Slot 22x22 con la cornice grigia della hotbar; selezionato: cornice bianca spessa. */
    private static void slotBox(MatrixStack m, int x, int y, boolean selected, boolean dim) {
        int light = selected ? 0xFFFFFFFF : 0xFFB8B8B8;
        int mid = selected ? 0xFFE6E6E6 : 0xFF8B8B8B;
        int shade = selected ? 0xFF9A9A9A : 0xFF555555;
        fill(m, x, y, x + SLOT, y + SLOT, 0xFF1B1B1B);                       // contorno scuro
        fill(m, x + 1, y + 1, x + SLOT - 1, y + SLOT - 1, mid);               // cornice
        fill(m, x + 1, y + 1, x + SLOT - 1, y + 2, light);                    // luce in alto/sinistra
        fill(m, x + 1, y + 1, x + 2, y + SLOT - 1, light);
        fill(m, x + 1, y + SLOT - 2, x + SLOT - 1, y + SLOT - 1, shade);      // ombra in basso/destra
        fill(m, x + SLOT - 2, y + 1, x + SLOT - 1, y + SLOT - 1, shade);
        fill(m, x + 3, y + 3, x + SLOT - 3, y + SLOT - 3, dim ? 0xE0000000 : 0xC0101010);  // interno scuro
        if (selected) {                                                       // cornice di selezione esterna
            fill(m, x - 2, y - 2, x + SLOT + 2, y - 1, 0xFFFFFFFF);
            fill(m, x - 2, y + SLOT + 1, x + SLOT + 2, y + SLOT + 2, 0xFFFFFFFF);
            fill(m, x - 2, y - 2, x - 1, y + SLOT + 2, 0xFFFFFFFF);
            fill(m, x + SLOT + 1, y - 2, x + SLOT + 2, y + SLOT + 2, 0xFFFFFFFF);
        }
    }

    private static ResourceLocation texture(String name) {
        ResourceLocation location = TEXTURES.get(name);
        if (location == null) {
            location = BizarreMod.id("textures/gui/hud/" + name + ".png");
            TEXTURES.put(name, location);
        }
        return location;
    }

    /** Icona 16x16, colorabile (le icone delle tecniche sono bianche e prendono il colore dello Stand/stile). */
    private static void icon(MatrixStack m, String name, int x, int y, int argb, float alpha) {
        float r = ((argb >> 16) & 255) / 255f, g = ((argb >> 8) & 255) / 255f, b = (argb & 255) / 255f;
        Minecraft.getInstance().getTextureManager().bindTexture(texture(name));
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.color4f(r, g, b, alpha);
        blit(m, x, y, 0f, 0f, 16, 16, 16, 16);
        RenderSystem.color4f(1f, 1f, 1f, 1f);
    }

    private static int standColor(String id) {
        switch (id) {
            case "star_platinum": return 0xFF8F78E8;
            case "the_world": return 0xFFF1D44A;
            case "crazy_diamond": return 0xFFFF7AB8;
            case "killer_queen": return 0xFFF2CFE0;
            case "gold_experience": return 0xFFF0B820;
            case "silver_chariot": return 0xFFD5DBE5;
            case "magicians_red": return 0xFFE5483A;
            case "hierophant_green": return 0xFF4FC26F;
            case "king_crimson": return 0xFFC83250;
            case "sticky_fingers": return 0xFF4F8FF0;
            case "stone_free": return 0xFF9CBEDF;
            default: return PURPLE;
        }
    }
}
