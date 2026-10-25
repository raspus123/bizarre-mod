package com.example.bizarremod.network;

import com.example.bizarremod.client.ClientHud;
import com.example.bizarremod.data.*;
import com.example.bizarremod.logic.Abilities;
import com.example.bizarremod.registry.ModItems;
import java.util.function.Supplier;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.network.PacketBuffer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.network.NetworkEvent;

/** A small owner-only snapshot. Never reads the server JojoData cache on the client. */
public class HudStatePacket {
    public String stand = "", style = "", styleId = "none";
    public boolean active, equipped, hasStand, hasStyle;
    public float energy;
    public int selectedStand, selectedStyle;
    public final String[] names = new String[8];
    public final float[] costs = new float[8];
    public final int[] remaining = new int[8], duration = new int[8];
    private HudStatePacket() { }
    public HudStatePacket(ServerPlayerEntity p, JojoData d) {
        stand = d.stand.displayName().getString();
        style = d.style.displayName().getString();
        styleId = d.style.id;
        hasStand = d.stand != StandType.NONE;
        hasStyle = d.style != FightStyle.NONE;
        active = d.standActive;
        equipped = (d.style != FightStyle.SPIN || ModItems.hasSteelBall(p))
                && (d.style != FightStyle.BOXING || ModItems.hasBoxingGloves(p));
        energy = d.energy;
        selectedStand = d.selectedMove;
        selectedStyle = d.selectedStyleMove;
        long now = p.world.getGameTime();
        for (int i = 0; i < 8; i++) {
            boolean isStyle = i >= 4;
            int j = i % 4;
            names[i] = isStyle ? Abilities.styleMoveName(d.style, j) : Abilities.moveName(d.stand, j);
            costs[i] = Abilities.hudCost(isStyle, d, j);
            duration[i] = Abilities.hudDuration(isStyle, d, j);
            long until = isStyle ? Math.max(d.styleCooldowns[j], d.cooldowns[4]) : d.cooldowns[j];
            remaining[i] = (int) Math.min(72000, Math.max(0, until - now));
        }
    }
    public static void encode(HudStatePacket p, PacketBuffer b) {
        b.writeString(p.stand); b.writeString(p.style); b.writeString(p.styleId);
        b.writeBoolean(p.active); b.writeBoolean(p.equipped);
        b.writeBoolean(p.hasStand); b.writeBoolean(p.hasStyle);
        b.writeFloat(p.energy); b.writeVarInt(p.selectedStand); b.writeVarInt(p.selectedStyle);
        for (int i = 0; i < 8; i++) {
            b.writeString(p.names[i]); b.writeFloat(p.costs[i]);
            b.writeVarInt(p.remaining[i]); b.writeVarInt(p.duration[i]);
        }
    }
    public static HudStatePacket decode(PacketBuffer b) {
        HudStatePacket p = new HudStatePacket();
        p.stand = b.readString(128); p.style = b.readString(128); p.styleId = b.readString(32);
        p.active = b.readBoolean(); p.equipped = b.readBoolean();
        p.hasStand = b.readBoolean(); p.hasStyle = b.readBoolean();
        p.energy = Math.max(0, Math.min(100, b.readFloat()));
        p.selectedStand = Math.floorMod(b.readVarInt(), 4); p.selectedStyle = Math.floorMod(b.readVarInt(), 4);
        for (int i = 0; i < 8; i++) {
            p.names[i] = b.readString(128); p.costs[i] = b.readFloat();
            p.remaining[i] = Math.max(0, Math.min(72000, b.readVarInt()));
            p.duration[i] = Math.max(0, Math.min(72000, b.readVarInt()));
        }
        return p;
    }
    public static void handle(HudStatePacket p, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHud.accept(p)));
        ctx.get().setPacketHandled(true);
    }
}
