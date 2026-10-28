package com.example.bizarremod.entity;

import com.example.bizarremod.data.JojoData;
import com.example.bizarremod.data.StandType;
import com.example.bizarremod.logic.Abilities;
import java.util.UUID;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.MobEntity;
import net.minecraft.entity.ai.attributes.AttributeModifierMap;
import net.minecraft.entity.ai.attributes.Attributes;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.network.IPacket;
import net.minecraft.network.datasync.DataParameter;
import net.minecraft.network.datasync.DataSerializers;
import net.minecraft.network.datasync.EntityDataManager;
import net.minecraft.util.DamageSource;
import net.minecraft.util.Hand;
import net.minecraft.world.World;
import net.minecraftforge.fml.network.NetworkHooks;

/** Entita' temporanea, controllata dal proprietario e replicata con lo spawn Forge. */
public class StandEntity extends MobEntity {
    private static final DataParameter<String> STAND_ID =
            EntityDataManager.createKey(StandEntity.class, DataSerializers.STRING);
    private UUID ownerId;
    // raffica di pugni in corso: un'ondata ogni 2 tick, lo Stand muove il braccio a ogni ondata
    private int pulsesLeft;
    private int pulseTimer;
    private double barrageRange;
    private float barrageDamage;
    private int barrageFire;

    public StandEntity(EntityType<? extends StandEntity> type, World world) {
        super(type, world);
        this.noClip = true;
        this.setNoGravity(true);
        this.setNoAI(true);
        this.enablePersistence();
    }

    /**
     * func_233666_p_ e' il builder base di MobEntity in MCP 20210309-1.16.5.
     * Eredita anche SWIM_SPEED, NAMETAG_DISTANCE e ENTITY_GRAVITY da Forge.
     * Un builder vuoto causa attributi null nel tick/render dello Stand.
     */
    public static AttributeModifierMap createAttributes() {
        return MobEntity.func_233666_p_()
                .createMutableAttribute(Attributes.MAX_HEALTH, 20.0D)
                .createMutableAttribute(Attributes.MOVEMENT_SPEED, 0.25D)
                .createMutableAttribute(Attributes.KNOCKBACK_RESISTANCE, 1.0D)
                .createMutableAttribute(Attributes.FOLLOW_RANGE, 16.0D)
                .createMutableAttribute(Attributes.ATTACK_DAMAGE, 1.0D)
                .createMutableAttribute(Attributes.ATTACK_KNOCKBACK, 0.0D)
                .create();
    }

    @Override
    public IPacket<?> createSpawnPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }

    @Override
    protected void registerData() {
        super.registerData();
        this.dataManager.register(STAND_ID, StandType.STAR_PLATINUM.id);
    }

    public void setOwner(PlayerEntity player) { this.ownerId = player.getUniqueID(); }
    public void setStandType(StandType type) { this.dataManager.set(STAND_ID, type.id); }
    public StandType getStandType() { return StandType.byId(this.dataManager.get(STAND_ID)); }

    /** Avvia una raffica: "pulses" ondate di pugni, una ogni 2 tick. */
    public void startBarrage(int pulses, double range, float damage, int fireSeconds) {
        this.pulsesLeft = pulses;
        this.pulseTimer = 0;
        this.barrageRange = range;
        this.barrageDamage = damage;
        this.barrageFire = fireSeconds;
    }

    @Override
    public void tick() {
        super.tick();
        if (this.world.isRemote) return;
        PlayerEntity owner = ownerId == null ? null : this.world.getPlayerByUuid(ownerId);
        if (owner == null || !owner.isAlive()) {
            this.remove();
            return;
        }
        JojoData data = JojoData.get(owner);
        // Un solo Stand per giocatore: elimina anche vecchie evocazioni e cambi di tipo.
        if (!data.standActive || !this.getUniqueID().equals(data.activeStandId)
                || data.stand != this.getStandType()) {
            this.remove();
            return;
        }
        double yaw = Math.toRadians(owner.rotationYaw);
        double offX = 0.9 * (-Math.cos(yaw) + Math.sin(yaw));
        double offZ = 0.9 * (-Math.sin(yaw) - Math.cos(yaw));
        this.setLocationAndAngles(owner.getPosX() + offX, owner.getPosY() + 0.2,
                owner.getPosZ() + offZ, owner.rotationYaw, owner.rotationPitch);
        this.setRotationYawHead(owner.rotationYawHead);
        this.renderYawOffset = owner.renderYawOffset;
        this.fallDistance = 0;
        if (owner.isSwingInProgress && !this.isSwingInProgress) this.swingArm(Hand.MAIN_HAND);
        if (pulsesLeft > 0 && owner instanceof ServerPlayerEntity && --pulseTimer <= 0) {
            pulseTimer = 2;
            pulsesLeft--;
            this.swingArm(Hand.MAIN_HAND);
            Abilities.barragePulse((ServerPlayerEntity) owner, barrageRange, barrageDamage, barrageFire, pulsesLeft == 0);
        }
    }

    @Override
    public boolean attackEntityFrom(DamageSource source, float amount) { return false; }
}
