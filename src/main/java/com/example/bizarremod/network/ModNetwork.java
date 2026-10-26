package com.example.bizarremod.network;

import com.example.bizarremod.BizarreMod;
import net.minecraft.util.ResourceLocation;
import net.minecraftforge.fml.network.NetworkRegistry;
import net.minecraftforge.fml.network.simple.SimpleChannel;

public class ModNetwork {
    private static final String PROTOCOL = "4";

    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(BizarreMod.MOD_ID, "main"),
            () -> PROTOCOL, PROTOCOL::equals, PROTOCOL::equals);

    public static void register() {
        CHANNEL.registerMessage(0, ActionPacket.class, ActionPacket::encode, ActionPacket::decode, ActionPacket::handle);
        CHANNEL.registerMessage(1, HudStatePacket.class, HudStatePacket::encode, HudStatePacket::decode,
                HudStatePacket::handle, java.util.Optional.of(net.minecraftforge.fml.network.NetworkDirection.PLAY_TO_CLIENT));
        CHANNEL.registerMessage(2, SelectMovePacket.class, SelectMovePacket::encode, SelectMovePacket::decode,
                SelectMovePacket::handle, java.util.Optional.of(net.minecraftforge.fml.network.NetworkDirection.PLAY_TO_SERVER));
    }
}
