package com.example.bizarremod.entity;

import com.example.bizarremod.logic.Abilities;
import com.example.bizarremod.registry.ModEntities;
import com.example.bizarremod.registry.ModItems;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.entity.projectile.ProjectileItemEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.network.IPacket;
import net.minecraft.particles.IParticleData;
import net.minecraft.particles.ParticleTypes;
import net.minecraft.potion.EffectInstance;
import net.minecraft.util.math.EntityRayTraceResult;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.vector.Vector3d;
import net.minecraft.world.Explosion;
import net.minecraft.world.World;
import net.minecraft.world.server.ServerWorld;
import net.minecraftforge.fml.network.NetworkHooks;

/**
 * Proiettile generico delle mosse a distanza degli Stand: smeraldi, coltelli, Star Finger, palle di fuoco,
 * monete esplosive, fili e cerniere. L'aspetto e' lo sprite dell'oggetto passato alla creazione.
 * I parametri (danno, effetti, esplosione, inseguimento) sono impostati solo lato server e non vengono salvati.
 */
public class StandShotEntity extends ProjectileItemEntity {
    private UUID ownerId;
    private UUID homingId;
    private float damage;
    private double knockback;
    private int fireSeconds;
    private boolean pull;
    private float explosionPower;
    private Explosion.Mode explosionMode = Explosion.Mode.NONE;
    private int lifetime = 20;
    private IParticleData trail = ParticleTypes.CRIT;
    private final List<EffectInstance> effects = new ArrayList<EffectInstance>();

    public StandShotEntity(EntityType<? extends StandShotEntity> type, World world) {
        super(type, world);
        this.setNoGravity(true);
    }

    public StandShotEntity(World world, ServerPlayerEntity owner, ItemStack icon) {
        super(ModEntities.STAND_SHOT.get(), owner, world);
        this.ownerId = owner.getUniqueID();
        this.setItem(icon);
        this.setNoGravity(true);
    }

    // ---- configurazione (metodi concatenabili)
    public StandShotEntity damage(float amount, double knockbackStrength) {
        this.damage = amount;
        this.knockback = knockbackStrength;
        return this;
    }
    public StandShotEntity fire(int seconds) { this.fireSeconds = seconds; return this; }
    public StandShotEntity pull() { this.pull = true; return this; }
    public StandShotEntity effect(EffectInstance effect) { this.effects.add(effect); return this; }
    public StandShotEntity explosion(float power, Explosion.Mode mode) {
        this.explosionPower = power;
        this.explosionMode = mode;
        return this;
    }
    public StandShotEntity homing(UUID target) { this.homingId = target; return this; }
    public StandShotEntity lifetime(int ticks) { this.lifetime = ticks; return this; }
    public StandShotEntity trail(IParticleData particle) { this.trail = particle; return this; }

    @Override
    protected Item getDefaultItem() {
        return ModItems.PROJECTILE_STAR.get();
    }

    @Override
    public IPacket<?> createSpawnPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }

    @Override
    public void tick() {
        if (this.world.isRemote) {
            super.tick();
            return;
        }
        if (this.ticksExisted > lifetime) {
            this.remove();
            return;
        }
        if (homingId != null) {
            Entity target = ((ServerWorld) this.world).getEntityByUuid(homingId);
            if (target != null && target.isAlive()) {
                Vector3d to = new Vector3d(target.getPosX(), target.getPosYHeight(0.5), target.getPosZ())
                        .subtract(this.getPositionVec());
                Vector3d motion = this.getMotion().scale(0.75).add(to.normalize().scale(0.55));
                double speed = motion.length();
                if (speed > 1.5) motion = motion.scale(1.5 / speed);
                this.setMotion(motion);
            }
        }
        super.tick();
        if (this.isAlive()) {
            ((ServerWorld) this.world).spawnParticle(trail, this.getPosX(), this.getPosY(), this.getPosZ(),
                    1, 0.02, 0.02, 0.02, 0.0);
        }
    }

    @Override
    protected void onImpact(RayTraceResult result) {
        if (this.world.isRemote) return;
        PlayerEntity owner = ownerId == null ? null : this.world.getPlayerByUuid(ownerId);
        if (result.getType() == RayTraceResult.Type.ENTITY && owner instanceof ServerPlayerEntity) {
            Entity hit = ((EntityRayTraceResult) result).getEntity();
            if (hit instanceof LivingEntity) {
                Abilities.projectileHit((ServerPlayerEntity) owner, (LivingEntity) hit, damage, knockback,
                        fireSeconds, pull, effects);
            }
        }
        if (explosionPower > 0 && owner != null) {
            this.world.createExplosion(owner, this.getPosX(), this.getPosY(), this.getPosZ(),
                    explosionPower, explosionMode);
        }
        ((ServerWorld) this.world).spawnParticle(trail, this.getPosX(), this.getPosY(), this.getPosZ(),
                10, 0.15, 0.15, 0.15, 0.1);
        this.remove();
    }
}
