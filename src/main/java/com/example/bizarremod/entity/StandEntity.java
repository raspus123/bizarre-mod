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
import net.minecraft.util.math.vector.Vector3d;
import net.minecraft.world.World;
import net.minecraftforge.fml.network.NetworkHooks;

/** Entita' temporanea, controllata dal proprietario e replicata con lo spawn Forge. */
public class StandEntity extends MobEntity {
    private static final DataParameter<String> STAND_ID =
            EntityDataManager.createKey(StandEntity.class, DataSerializers.STRING);
    /** Posa/azione dello Stand, sincronizzata con i client per l'animazione. */
    public static final int ANIM_NONE = 0, ANIM_PUNCH = 1, ANIM_SHOOT = 2, ANIM_POWER = 3;
    private static final DataParameter<Integer> ANIM =
            EntityDataManager.createKey(StandEntity.class, DataSerializers.VARINT);
    private UUID ownerId;
    private int animTicks;
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
        this.dataManager.register(ANIM, ANIM_NONE);
    }

    public void setOwner(PlayerEntity player) { this.ownerId = player.getUniqueID(); }
    public void setStandType(StandType type) { this.dataManager.set(STAND_ID, type.id); }
    public StandType getStandType() { return StandType.byId(this.dataManager.get(STAND_ID)); }

    public int getAnimation() { return this.dataManager.get(ANIM); }

    /**
     * Fa eseguire allo Stand un'azione per "ticks" tick: PUNCH (davanti a te, pugni), SHOOT (un passo avanti,
     * braccia tese) o POWER (braccia alzate). Le azioni d'attacco sostituiscono sempre quella in corso.
     */
    public void animate(int type, int ticks) {
        if (type != ANIM_POWER || ticks >= this.animTicks) {
            this.animTicks = ticks;
            this.dataManager.set(ANIM, type);
        }
    }

    /** Dove si mette lo Stand (ai piedi) rispetto al proprietario durante le varie azioni. */
    public static Vector3d actionPosition(PlayerEntity owner, int anim) {
        double yaw = Math.toRadians(owner.rotationYaw);
        Vector3d forward = new Vector3d(-Math.sin(yaw), 0.0D, Math.cos(yaw));
        Vector3d right = new Vector3d(-Math.cos(yaw), 0.0D, -Math.sin(yaw));
        double ahead = -0.9D;      // a riposo: dietro e a destra
        double side = 0.9D;
        if (anim == ANIM_PUNCH) {          // davanti a te, tra te e il bersaglio
            ahead = 1.7D;
            side = 0.0D;
        } else if (anim == ANIM_SHOOT) {   // un passo avanti con le braccia tese
            ahead = 1.0D;
            side = 0.5D;
        } else if (anim == ANIM_POWER) {   // piu' vicino a te, braccia alzate
            ahead = -0.3D;
        }
        return new Vector3d(owner.getPosX(), owner.getPosY() + 0.2D, owner.getPosZ())
                .add(forward.scale(ahead)).add(right.scale(side));
    }

    /** Avvia una raffica: "pulses" ondate di pugni, una ogni 2 tick. */
    public void startBarrage(int pulses, double range, float damage, int fireSeconds) {
        this.pulsesLeft = pulses;
        this.pulseTimer = 0;
        this.barrageRange = range;
        this.barrageDamage = damage;
        this.barrageFire = fireSeconds;
        this.animate(ANIM_PUNCH, pulses * 2 + 6);
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
        if (animTicks > 0 && --animTicks == 0) this.dataManager.set(ANIM, ANIM_NONE);
        Vector3d spot = actionPosition(owner, this.getAnimation());
        this.setLocationAndAngles(spot.x, spot.y, spot.z, owner.rotationYaw, owner.rotationPitch);
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
