package com.example.bizarremod.client;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.entity.StandShotEntity;
import com.example.bizarremod.entity.SteelBallEntity;
import com.example.bizarremod.registry.ModEntities;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.SpriteRenderer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.client.registry.ClientRegistry;
import net.minecraftforge.fml.client.registry.RenderingRegistry;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

@Mod.EventBusSubscriber(modid = BizarreMod.MOD_ID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public class ClientSetup {

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent e) {
        RenderingRegistry.registerEntityRenderingHandler(ModEntities.STAND.get(), StandRenderer::new);
        RenderingRegistry.registerEntityRenderingHandler(ModEntities.STEEL_BALL.get(),
                manager -> new SpriteRenderer<SteelBallEntity>(manager, Minecraft.getInstance().getItemRenderer()));
        RenderingRegistry.registerEntityRenderingHandler(ModEntities.STAND_SHOT.get(),
                manager -> new SpriteRenderer<StandShotEntity>(manager, Minecraft.getInstance().getItemRenderer()));
        ClientRegistry.registerKeyBinding(ClientKeys.SUMMON);
        ClientRegistry.registerKeyBinding(ClientKeys.CYCLE);
        ClientRegistry.registerKeyBinding(ClientKeys.USE);
        ClientRegistry.registerKeyBinding(ClientKeys.STYLE);
        ClientRegistry.registerKeyBinding(ClientKeys.STYLE_CYCLE);
        ClientRegistry.registerKeyBinding(ClientKeys.RACE);
        ClientRegistry.registerKeyBinding(ClientKeys.MENU);
        ClientRegistry.registerKeyBinding(ClientKeys.EDIT_HUD);
    }
}
