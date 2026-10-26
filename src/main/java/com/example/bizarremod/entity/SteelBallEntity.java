package com.example.bizarremod.entity;

import com.example.bizarremod.logic.Abilities;
import com.example.bizarremod.registry.ModEntities;
import com.example.bizarremod.registry.ModItems;
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
import net.minecraft.util.math.EntityRayTraceResult;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.world.World;
import net.minecraft.world.server.ServerWorld;
import net.minecraftforge.fml.network.NetworkHooks;

/**
 * Sfera d'acciaio lanciata dallo Spin: proiettile rettilineo e veloce.
 * Non viene consumata: l'oggetto resta nella mano del giocatore, la sfera lanciata "ritorna" sparendo.
 */
public class SteelBallEntity extends ProjectileItemEntity {
    private static final int MAX_AGE = 40;
    private UUID ownerId;

    public SteelBallEntity(EntityType<? extends SteelBallEntity> type, World world) {
        super(type, world);
        this.setNoGravity(true);
    }

    public SteelBallEntity(World world, ServerPlayerEntity owner) {
        super(ModEntities.STEEL_BALL.get(), owner, world);
        this.ownerId = owner.getUniqueID();
        this.setNoGravity(true);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.STEEL_BALL.get();
    }

    @Override
    public IPacket<?> createSpawnPacket() {
        return NetworkHooks.getEntitySpawningPacket(this);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.world.isRemote) return;
        if (this.ticksExisted > MAX_AGE) {
            this.remove();
            return;
        }
        ((ServerWorld) this.world).spawnParticle(ParticleTypes.CRIT,
                this.getPosX(), this.getPosY(), this.getPosZ(), 2, 0.05, 0.05, 0.05, 0.0);
    }

    @Override
    protected void onImpact(RayTraceResult result) {
        if (this.world.isRemote) return;
        if (result.getType() == RayTraceResult.Type.ENTITY) {
            Entity hit = ((EntityRayTraceResult) result).getEntity();
            PlayerEntity owner = ownerId == null ? null : this.world.getPlayerByUuid(ownerId);
            if (owner instanceof ServerPlayerEntity && hit instanceof LivingEntity) {
                Abilities.steelBallHit((ServerPlayerEntity) owner, (LivingEntity) hit);
            }
        }
        ((ServerWorld) this.world).spawnParticle(ParticleTypes.CRIT,
                this.getPosX(), this.getPosY(), this.getPosZ(), 12, 0.2, 0.2, 0.2, 0.15);
        this.remove();
    }
}
