package com.example.bizarremod.client;

import com.google.gson.Gson;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraftforge.fml.loading.FMLPaths;
import org.apache.logging.log4j.LogManager;

/** No Inventory HUD dependency or modification of its settings. Coordinates use free-screen fractions. */
public class HudLayout {
    public double x = 0.02, y = 0.62, scale = 1.0;
    public boolean visible = true;
    private static final Path FILE = FMLPaths.CONFIGDIR.get().resolve("bizarremod-hud.json");
    private static final Gson GSON = new Gson();
    private static HudLayout instance;
    public static HudLayout get() {
        if (instance == null) {
            instance = new HudLayout();
            if (Files.exists(FILE)) {
                try {
                    HudLayout loaded = GSON.fromJson(new String(Files.readAllBytes(FILE), StandardCharsets.UTF_8), HudLayout.class);
                    if (loaded != null) instance = loaded;
                } catch (Exception e) { LogManager.getLogger("bizarremod").warn("Cannot read HUD settings; using defaults", e); }
            }
            instance.clamp();
        }
        return instance;
    }
    public void clamp() {
        x = Double.isFinite(x) ? Math.max(0, Math.min(1, x)) : 0.02;
        y = Double.isFinite(y) ? Math.max(0, Math.min(1, y)) : 0.62;
        scale = Double.isFinite(scale) ? Math.max(0.6, Math.min(1.5, scale)) : 1;
    }
    public void save() {
        clamp();
        try {
            Files.createDirectories(FILE.getParent());
            Files.write(FILE, GSON.toJson(this).getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) { LogManager.getLogger("bizarremod").error("Cannot save HUD settings", e); }
    }
    public void reset() { x = 0.02; y = 0.62; scale = 1; visible = true; }
    public double effectiveScale(int w, int h) { return Math.min(scale, Math.min((double)w / 236, (double)h / 124)); }
    public int left(int w, int h) { return (int)Math.round(x * Math.max(0, w - 236 * effectiveScale(w, h))); }
    public int top(int w, int h) { return (int)Math.round(y * Math.max(0, h - 124 * effectiveScale(w, h))); }
    public void position(double px, double py, int w, int h) {
        double s = effectiveScale(w, h);
        x = px / Math.max(1, w - 236 * s); y = py / Math.max(1, h - 124 * s); clamp();
    }
}
