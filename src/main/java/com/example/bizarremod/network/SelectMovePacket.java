package com.example.bizarremod.network;

import com.example.bizarremod.data.JojoData;
import java.util.function.Supplier;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.network.PacketBuffer;
import net.minecraftforge.fml.network.NetworkEvent;

/** Only selection is client-provided; energy, equipment and cooldowns remain server-owned. */
public class SelectMovePacket {
    private final boolean style;
    private final int index;
    public SelectMovePacket(boolean style, int index) { this.style = style; this.index = index; }
    public static void encode(SelectMovePacket p, PacketBuffer b) { b.writeBoolean(p.style); b.writeVarInt(p.index); }
    public static SelectMovePacket decode(PacketBuffer b) { return new SelectMovePacket(b.readBoolean(), b.readVarInt()); }
    public static void handle(SelectMovePacket p, Supplier<NetworkEvent.Context> ctx) {
        ctx.get().enqueueWork(() -> {
            ServerPlayerEntity player = ctx.get().getSender();
            if (player == null || p.index < 0 || p.index > 3) return;
            JojoData d = JojoData.get(player);
            if (p.style) d.selectedStyleMove = p.index; else d.selectedMove = p.index;
            JojoData.save(player);
            ModNetwork.CHANNEL.send(net.minecraftforge.fml.network.PacketDistributor.PLAYER.with(() -> player),
                    new HudStatePacket(player, d));
        });
        ctx.get().setPacketHandled(true);
    }
}
