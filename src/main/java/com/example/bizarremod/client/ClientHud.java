package com.example.bizarremod.client;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.network.HudStatePacket;
import com.mojang.blaze3d.matrix.MatrixStack;
import java.util.Locale;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.AbstractGui;
import net.minecraft.client.resources.I18n;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = BizarreMod.MOD_ID, value = Dist.CLIENT)
public class ClientHud extends AbstractGui {
    public static final int GOLD = 0xFFE1BD69, PURPLE = 0xFFAA70EB;
    public static HudStatePacket state;
    private static long received;
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
        panel(m, 0, 0, 236, 124, editing ? 0xFFFFFFFF : GOLD);
        text(m, "BIZARRE / " + tr("combat"), 10, 7, GOLD, 218);
        int energy = state == null ? 100 : Math.round(state.energy);
        fill(m, 10, 21, 226, 26, 0xFF32253D);
        fill(m, 10, 21, 10 + (int)(216 * energy / 100.0), 26, PURPLE);
        text(m, tr("energy", energy), 10, 29, 0xFFDFD5EA, 216);
        row(m, 42, false); row(m, 72, true);
        text(m, state == null ? tr("waiting") : requirement(), 10, 104,
                state != null && !state.equipped ? 0xFFF47F8D : GOLD, 216);
        m.pop();
    }
    private static void row(MatrixStack m, int y, boolean style) {
        int color = style ? styleColor() : PURPLE;
        String name = state == null ? (style ? "SPIN" : "STAR PLATINUM") : (style ? state.style : state.stand);
        text(m, name, 10, y, color, 120);
        boolean exists = state != null && (style ? state.hasStyle : state.hasStand);
        if (!exists && state != null) return;
        int selected = state == null ? 0 : (style ? state.selectedStyle : state.selectedStand);
        for (int j = 0; j < 4; j++) {
            int x = 132 + j*24, i = j + (style ? 4 : 0);
            panel(m, x, y-1, 22, 24, j == selected ? GOLD : 0xFF503D69);
            int cd = ticks(i);
            if (cd > 0) {
                int total = state == null ? 1 : Math.max(state.duration[i], 8);
                int height = (int)(21 * Math.min(1.0, (double)cd / total));
                fill(m, x+1, y+22-height, x+21, y+22, 0xAA05030B);
            }
            text(m, cd > 0 ? String.valueOf((cd+19)/20) : String.valueOf(j+1), x+6, y+6,
                    cd > 0 ? 0xFFBBB0C6 : color, 16);
        }
        if (state != null) {
            String line = state.names[selected + (style ? 4 : 0)];
            if (!style && !state.active) line = tr("stand_off");
            text(m, line, 10, y+12, 0xFFD0C7DA, 116);
        }
    }
}
