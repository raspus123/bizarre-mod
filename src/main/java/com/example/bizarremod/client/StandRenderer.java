package com.example.bizarremod.client;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.entity.StandEntity;
import com.mojang.blaze3d.matrix.MatrixStack;
import net.minecraft.client.renderer.IRenderTypeBuffer;
import net.minecraft.client.renderer.entity.EntityRendererManager;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.model.BipedModel;
import net.minecraft.client.renderer.entity.model.PlayerModel;
import net.minecraft.util.ResourceLocation;

/**
 * Disegna lo Stand con il modello "giocatore" (texture 64x64 con secondo strato per cinture, fasce e stivali)
 * e cambia la posa delle braccia a seconda dell'azione: braccia tese per i colpi a distanza,
 * braccia alzate per le mosse di potere; i pugni usano l'animazione di attacco.
 */
public class StandRenderer extends MobRenderer<StandEntity, PlayerModel<StandEntity>> {

    public StandRenderer(EntityRendererManager manager) {
        super(manager, new PlayerModel<StandEntity>(0.0F, false), 0.0F);
    }

    @Override
    public void render(StandEntity stand, float entityYaw, float partialTicks, MatrixStack matrix,
                       IRenderTypeBuffer buffer, int light) {
        PlayerModel<StandEntity> model = this.getEntityModel();
        int animation = stand.getAnimation();
        BipedModel.ArmPose pose = BipedModel.ArmPose.EMPTY;
        if (animation == StandEntity.ANIM_SHOOT) {
            pose = BipedModel.ArmPose.BOW_AND_ARROW;
        } else if (animation == StandEntity.ANIM_POWER) {
            pose = BipedModel.ArmPose.THROW_SPEAR;
        }
        model.rightArmPose = pose;
        model.leftArmPose = pose;
        super.render(stand, entityYaw, partialTicks, matrix, buffer, light);
    }

    @Override
    public ResourceLocation getEntityTexture(StandEntity stand) {
        return BizarreMod.id("textures/entity/stand/" + stand.getStandType().id + ".png");
    }
}
