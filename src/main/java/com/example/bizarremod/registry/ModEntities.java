package com.example.bizarremod.registry;

import com.example.bizarremod.BizarreMod;
import com.example.bizarremod.entity.StandEntity;
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

    /** Sfera d'acciaio lanciata dallo Spin (proiettile non salvato nel mondo). */
    public static final RegistryObject<EntityType<SteelBallEntity>> STEEL_BALL = ENTITIES.register("steel_ball",
            () -> EntityType.Builder.<SteelBallEntity>create(SteelBallEntity::new, EntityClassification.MISC)
                    .size(0.25f, 0.25f)
                    .disableSerialization()
                    .build("steel_ball"));
}
