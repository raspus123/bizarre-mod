package com.example.bizarremod.registry;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.entity.StandEntity;
import com.example.bizarremod.entity.StandShotEntity;
import com.example.bizarremod.entity.SteelBallEntity;
import net.minecraft.entity.EntityClassification;
import net.minecraft.entity.EntityType;
import net.minecraftforge.fml.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;

public class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.ENTITIES, BizarreMod.MOD_ID);

    public static final RegistryObject<EntityType<StandEntity>> STAND = ENTITIES.register("stand",
            () -> EntityType.Builder.<StandEntity>create(StandEntity::new, EntityClassification.MISC)
                    .size(0.6f, 1.8f)
                    .immuneToFire()
                    .disableSerialization()
                    .build("stand"));

    /**
     * Sfera d'acciaio dello Spin: si muove ogni tick (orbita e ritorno), quindi la posizione viene
     * inviata ai client a ogni tick per un movimento fluido.
     */
    public static final RegistryObject<EntityType<SteelBallEntity>> STEEL_BALL = ENTITIES.register("steel_ball",
            () -> EntityType.Builder.<SteelBallEntity>create(SteelBallEntity::new, EntityClassification.MISC)
                    .size(0.25f, 0.25f)
                    .disableSerialization()
                    .setTrackingRange(8)
                    .setUpdateInterval(1)
                    .build("steel_ball"));

    /** Proiettile generico delle mosse a distanza degli Stand (smeraldi, coltelli, monete...). */
    public static final RegistryObject<EntityType<StandShotEntity>> STAND_SHOT = ENTITIES.register("stand_shot",
            () -> EntityType.Builder.<StandShotEntity>create(StandShotEntity::new, EntityClassification.MISC)
                    .size(0.25f, 0.25f)
                    .disableSerialization()
                    .setTrackingRange(8)
                    .setUpdateInterval(2)
                    .build("stand_shot"));
}
