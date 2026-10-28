package com.example.bizarremod.entity;

import com.example.bizarremod.logic.Abilities;
import com.example.bizarremod.registry.ModEntities;
import com.example.bizarremod.registry.ModItems;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.entity.projectile.ProjectileItemEntity;
import net.minecraft.item.Item;
import net.minecraft.network.IPacket;
import net.minecraft.particles.ParticleTypes;
import net.minecraft.potion.EffectInstance;
import net.minecraft.potion.Effects;
import net.minecraft.util.SoundCategory;
import net.minecraft.util.SoundEvents;
import net.minecraft.util.math.EntityRayTraceResult;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.vector.Vector3d;
import net.minecraft.world.World;
import net.minecraft.world.server.ServerWorld;
import net.minecraftforge.fml.network.NetworkHooks;

/**
 * Sfera d'acciaio dello Spin. Parte dal giocatore e poi TORNA SEMPRE da lui:
 * - rettilinea: vola in avanti, colpisce, poi rientra (colpendo di nuovo chi incontra al ritorno);
 * - orbitante: ruota intorno al giocatore per un po' e poi rientra.
 * L'oggetto Sfera d'acciaio in mano non viene consumato: quella lanciata e' solo un proiettile.
 */
public class SteelBallEntity extends ProjectileItemEntity {
    private static final int MAX_AGE = 200;

    private UUID ownerId;
    private boolean orbiting;
    private boolean returning;
    private float outDamage = 9f;
    private float backDamage = 5f;
    private double knockback = 0.6D;
    private int outTicks = 9;
    private int phaseTicks;
    private int returnTicks;
    private double orbitRadius = 4.0D;
    private double orbitAngle;
    private double orbitSpeed = 0.5D;
    private int orbitTicks = 50;
    private int hitCooldown = 8;
    private int slowTicks;
    private int witherTicks;
    private final Map<UUID, Integer> lastHit = new HashMap<UUID, Integer>();

    public SteelBallEntity(EntityType<? extends SteelBallEntity> type, World world) {
        super(type, world);
        this.setNoGravity(true);
    }

    public SteelBallEntity(World world, ServerPlayerEntity owner) {
        super(ModEntities.STEEL_BALL.get(), owner, world);
        this.ownerId = owner.getUniqueID();
        this.setNoGravity(true);
    }

    // ---- configurazione (metodi concatenabili)

    /** Volo rettilineo per outTicks tick (o fino all'impatto), poi ritorno. */
    public SteelBallEntity straight(float outgoingDamage, float returningDamage, int ticksOut) {
        this.orbiting = false;
        this.outDamage = outgoingDamage;
        this.backDamage = returningDamage;
        this.outTicks = ticksOut;
        return this;
    }

    /** Orbita intorno al giocatore per "ticks" tick, poi ritorno. */
    public SteelBallEntity orbit(double radius, double startAngle, int ticks, float damage) {
        this.orbiting = true;
        this.orbitRadius = radius;
        this.orbitAngle = startAngle;
        this.orbitTicks = ticks;
        this.outDamage = damage;
        this.backDamage = damage;
        return this;
    }

    public SteelBallEntity effects(int slowness, int wither) {
        this.slowTicks = slowness;
        this.witherTicks = wither;
        return this;
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.STEEL_BALL.get();
    }

    @Override
    public IPacket<?> createSpawnPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }

    private List<EffectInstance> effectList() {
        List<EffectInstance> list = new ArrayList<EffectInstance>();
        if (slowTicks > 0) list.add(new EffectInstance(Effects.SLOWNESS, slowTicks, 1));
        if (witherTicks > 0) list.add(new EffectInstance(Effects.WITHER, witherTicks, 0));
        return list;
    }

    // ---- movimento (solo lato server; il client segue le posizioni inviate dal server)

    @Override
    public void tick() {
        if (this.world.isRemote) {
            super.tick();
            return;
        }
        PlayerEntity found = ownerId == null ? null : this.world.getPlayerByUuid(ownerId);
        if (!(found instanceof ServerPlayerEntity) || !found.isAlive() || this.ticksExisted > MAX_AGE) {
            this.remove();
            return;
        }
        ServerPlayerEntity owner = (ServerPlayerEntity) found;
        if (returning) {
            returnStep(owner);
        } else if (orbiting) {
            orbitStep(owner);
        } else {
            super.tick();                                  // volo rettilineo con le collisioni di Minecraft
            if (!this.isAlive()) return;
            if (++phaseTicks >= outTicks) startReturn();
        }
        if (this.isAlive()) {
            ((ServerWorld) this.world).spawnParticle(ParticleTypes.CRIT, this.getPosX(), this.getPosY(), this.getPosZ(),
                    1, 0.03, 0.03, 0.03, 0.0);
        }
    }

    private void startReturn() {
        this.returning = true;
        this.returnTicks = 0;
    }

    private void orbitStep(ServerPlayerEntity owner) {
        orbitAngle += orbitSpeed;
        Vector3d center = owner.getPositionVec().add(0, owner.getHeight() * 0.6, 0);
        Vector3d next = center.add(Math.cos(orbitAngle) * orbitRadius, Math.sin(orbitAngle * 0.5) * 0.3,
                Math.sin(orbitAngle) * orbitRadius);
        Vector3d old = this.getPositionVec();
        this.setPosition(next.x, next.y, next.z);
        this.setMotion(next.subtract(old));
        hitNearby(owner, outDamage);
        if (++phaseTicks >= orbitTicks) startReturn();
    }

    private void returnStep(ServerPlayerEntity owner) {
        Vector3d target = owner.getPositionVec().add(0, owner.getHeight() * 0.65, 0);
        Vector3d to = target.subtract(this.getPositionVec());
        double distance = to.length();
        if (distance < 1.4D) {
            catchBall(owner);
            return;
        }
        double speed = Math.min(2.8D, 1.0D + returnTicks * 0.25D);
        returnTicks++;
        Vector3d step = to.normalize().scale(Math.min(speed, distance));
        this.setPosition(this.getPosX() + step.x, this.getPosY() + step.y, this.getPosZ() + step.z);
        this.setMotion(step);
        hitNearby(owner, backDamage);
    }

    /** Colpisce chi e' vicino alla sfera (usato in orbita e al ritorno), con una pausa per bersaglio. */
    private void hitNearby(final ServerPlayerEntity owner, float damage) {
        List<LivingEntity> near = this.world.getEntitiesWithinAABB(LivingEntity.class,
                this.getBoundingBox().grow(0.7D), e -> e != owner);
        for (LivingEntity target : near) {
            Integer last = lastHit.get(target.getUniqueID());
            if (last != null && this.ticksExisted - last < hitCooldown) continue;
            if (Abilities.projectileHit(owner, target, damage, knockback, 0, false, effectList())) {
                lastHit.put(target.getUniqueID(), this.ticksExisted);
            }
        }
    }

    /** La sfera e' tornata da te: suono, particelle e scompare (l'oggetto in mano non e' mai cambiato). */
    private void catchBall(ServerPlayerEntity owner) {
        this.world.playSound(null, owner.getPosX(), owner.getPosY(), owner.getPosZ(),
                SoundEvents.ENTITY_ITEM_PICKUP, SoundCategory.PLAYERS, 0.6F, 1.4F);
        ((ServerWorld) this.world).spawnParticle(ParticleTypes.CRIT, this.getPosX(), this.getPosY(), this.getPosZ(),
                8, 0.15, 0.15, 0.15, 0.1);
        this.remove();
    }

    /** Impatto durante il volo in avanti: colpisce, poi la sfera inizia a tornare. */
    @Override
    protected void onImpact(RayTraceResult result) {
        if (this.world.isRemote) return;
        if (result.getType() == RayTraceResult.Type.ENTITY) {
            Entity hit = ((EntityRayTraceResult) result).getEntity();
            PlayerEntity owner = ownerId == null ? null : this.world.getPlayerByUuid(ownerId);
            if (owner instanceof ServerPlayerEntity && hit instanceof LivingEntity) {
                if (Abilities.projectileHit((ServerPlayerEntity) owner, (LivingEntity) hit, outDamage, knockback,
                        0, false, effectList())) {
                    lastHit.put(hit.getUniqueID(), this.ticksExisted);
                }
            }
        }
        ((ServerWorld) this.world).spawnParticle(ParticleTypes.CRIT, this.getPosX(), this.getPosY(), this.getPosZ(),
                12, 0.2, 0.2, 0.2, 0.15);
        startReturn();
    }
}
