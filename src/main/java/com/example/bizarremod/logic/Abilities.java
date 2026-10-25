package com.example.bizarremod.logic;

import com.example.bizarremod.data.FightStyle;
import com.example.bizarremod.data.JojoData;
import com.example.bizarremod.data.Race;
import com.example.bizarremod.data.StandType;
import com.example.bizarremod.entity.StandEntity;
import com.example.bizarremod.registry.ModEntities;
import com.example.bizarremod.registry.ModItems;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;
import net.minecraft.block.Blocks;
import net.minecraft.entity.CreatureAttribute;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.monster.IMob;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.ServerPlayerEntity;
import net.minecraft.entity.projectile.ProjectileHelper;
import net.minecraft.item.BoneMealItem;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.particles.IParticleData;
import net.minecraft.particles.ParticleTypes;
import net.minecraft.potion.Effect;
import net.minecraft.potion.EffectInstance;
import net.minecraft.potion.Effects;
import net.minecraft.util.DamageSource;
import net.minecraft.util.SoundCategory;
import net.minecraft.util.SoundEvent;
import net.minecraft.util.SoundEvents;
import net.minecraft.util.math.AxisAlignedBB;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.EntityRayTraceResult;
import net.minecraft.util.math.RayTraceResult;
import net.minecraft.util.math.vector.Vector3d;
import net.minecraft.util.text.StringTextComponent;
import net.minecraft.util.text.TranslationTextComponent;
import net.minecraft.world.Explosion;
import net.minecraft.world.server.ServerWorld;

/**
 * Tutta la logica delle abilita' (eseguita SOLO lato server).
 * Ogni stand ha 4 mosse: 0 = raffica, 1-3 = abilita'. Un tasto cambia la mossa selezionata, un altro la esegue.
 * Slot dei cooldown: 0-3 mosse dello stand, 4 stile, 5 razza.
 */
public final class Abilities {
    public static final int SUMMON = 0, CYCLE = 1, USE = 2, STYLE = 3, RACE = 4, STYLE_CYCLE = 5;

    private Abilities() {}

    public static void perform(ServerPlayerEntity p, int action) {
        if (!p.isAlive() || p.isSpectator()) return;
        JojoData d = JojoData.get(p);
        switch (action) {
            case SUMMON: toggleStand(p, d); break;
            case CYCLE: cycleMove(p, d); break;
            case USE: standMove(p, d, d.selectedMove); break;
            case STYLE: styleMove(p, d); break;
            case RACE: raceMove(p, d); break;
            case STYLE_CYCLE: cycleStyle(p, d); break;
            default: break;
        }
    }

    // ================================================================== STAND

    private static void toggleStand(ServerPlayerEntity p, JojoData d) {
        if (d.stand == StandType.NONE) { msg(p, "message.bizarremod.no_stand"); return; }
        if (d.standActive) {
            d.standActive = false;
            d.activeStandId = null;
            p.sendStatusMessage(new TranslationTextComponent("message.bizarremod.stand_off", d.stand.displayName()), true);
            return;
        }
        StandEntity entity = ModEntities.STAND.get().create(p.getServerWorld());
        if (entity == null) { msg(p, "message.bizarremod.summon_failed"); return; }
        entity.setOwner(p);
        entity.setStandType(d.stand);
        entity.setLocationAndAngles(p.getPosX(), p.getPosY(), p.getPosZ(), p.rotationYaw, 0f);
        if (!p.getServerWorld().addEntity(entity)) {
            entity.remove();
            d.activeStandId = null;
            msg(p, "message.bizarremod.summon_failed");
            return;
        }
        // Imposta lo stato solo dopo lo spawn riuscito; nessuna protezione gratuita se fallisce.
        d.activeStandId = entity.getUniqueID();
        d.standActive = true;
        p.sendStatusMessage(new TranslationTextComponent("message.bizarremod.stand_on", d.stand.displayName()), true);
    }

    /** Passa alla mossa successiva dello stand (raffica -> abilita' 1 -> 2 -> 3 -> raffica). */
    private static void cycleMove(ServerPlayerEntity p, JojoData d) {
        if (d.stand == StandType.NONE) { msg(p, "message.bizarremod.no_stand"); return; }
        d.selectedMove = (d.selectedMove + 1) % 4;
        Move m = move(d.stand, d.selectedMove);
        if (m == null) return;
        say(p, "[" + (d.selectedMove + 1) + "/4] " + m.name + " - " + (int) m.cost + " energia");
        sound(p, SoundEvents.ENTITY_EXPERIENCE_ORB_PICKUP);
    }

    /** Nome della mossa selezionata (per la barra di stato). */
    public static String moveName(StandType s, int n) {
        Move m = move(s, n);
        return m == null ? "-" : m.name;
    }

    private static void standMove(ServerPlayerEntity p, JojoData d, int n) {
        if (d.stand == StandType.NONE) { msg(p, "message.bizarremod.no_stand"); return; }
        Move m = move(d.stand, n);
        if (m == null) return;
        if (!ready(p, d, n, m.cost, true)) return;
        if (m.action.test(p)) commit(p, d, n, m.cost, m.cooldown);
    }

    /** Una mossa: nome, costo in energia, ricarica in tick e azione (true = riuscita). */
    private static final class Move {
        final String name;
        final float cost;
        final int cooldown;
        final Predicate<ServerPlayerEntity> action;

        Move(String name, float cost, int cooldown, Predicate<ServerPlayerEntity> action) {
            this.name = name;
            this.cost = cost;
            this.cooldown = cooldown;
            this.action = action;
        }
    }

    private static Move m(String name, float cost, int cooldown, Predicate<ServerPlayerEntity> action) {
        return new Move(name, cost, cooldown, action);
    }

    private static Move move(StandType s, int n) {
        Move[] list = MOVES.get(s);
        return (list == null || n < 0 || n >= list.length) ? null : list[n];
    }

    /** Il moveset di ogni stand: indice 0 = raffica, 1-3 = abilita'. */
    private static final Map<StandType, Move[]> MOVES = new EnumMap<StandType, Move[]>(StandType.class);

    static {
        MOVES.put(StandType.STAR_PLATINUM, new Move[] {
            m("Raffica ORA", 25, 40, p -> barrage(p, 4.5, 7, 3.0F, "ORA ORA ORA ORA ORA!", 0)),
            m("Star Finger", 30, 120, p -> ranged(p, 12, 10F, 0.4, ParticleTypes.END_ROD, "STAR FINGER!")),
            m("Inala", 35, 200, p -> inhale(p)),
            m("Time Stop", 50, 400, p -> timeStop(p, 40, "STAR PLATINUM: THE WORLD!"))
        });
        MOVES.put(StandType.THE_WORLD, new Move[] {
            m("Raffica MUDA", 25, 40, p -> barrage(p, 4.5, 8, 3.5F, "MUDA MUDA MUDA MUDA!", 0)),
            m("Coltelli", 30, 100, p -> ranged(p, 20, 8F, 0.3, ParticleTypes.CRIT, "THE WORLD: COLTELLI!",
                    fx(Effects.WITHER, 40, 0))),
            m("Road Roller", 45, 250, p -> blast(p, 5, 12F, 1.5, 0, ParticleTypes.POOF, 60,
                    "ROAD ROLLER DA!", true, fx(Effects.SLOWNESS, 60, 2))),
            m("Time Stop", 70, 700, p -> timeStop(p, 100, "ZA WARUDO! TOKI WO TOMARE!"))
        });
        MOVES.put(StandType.CRAZY_DIAMOND, new Move[] {
            m("Raffica DORA", 25, 40, p -> barrage(p, 4.5, 6, 2.5F, "DORARARARARA!", 0)),
            m("Restore", 40, 300, p -> restore(p)),
            m("Onda curativa", 45, 400, p -> healingWave(p)),
            m("Guardia", 30, 300, p -> buff(p, "CRAZY DIAMOND: GUARDIA!", SoundEvents.ENTITY_PLAYER_LEVELUP,
                    fx(Effects.ABSORPTION, 200, 4), fx(Effects.RESISTANCE, 200, 1)))
        });
        MOVES.put(StandType.KILLER_QUEEN, new Move[] {
            m("Kill Barrage", 25, 40, p -> barrage(p, 4.5, 5, 3.0F, "KILLER QUEEN: KILL BARRAGE!", 0)),
            m("Bomba su entità", 25, 100, p -> bombEntity(p)),
            m("Bomba su blocco", 45, 200, p -> bombBlock(p)),
            m("Sheer Heart Attack", 60, 500, p -> sheerHeartAttack(p))
        });
        MOVES.put(StandType.GOLD_EXPERIENCE, new Move[] {
            m("Raffica MUDA", 25, 40, p -> barrage(p, 4.5, 6, 2.8F, "MUDA MUDA MUDA MUDA!", 0)),
            m("Life Giver", 45, 200, p -> goldLife(p)),
            m("Dolore amplificato", 35, 160, p -> ranged(p, 5, 6F, 0.4, ParticleTypes.CRIT,
                    "GOLD EXPERIENCE: DOLORE AMPLIFICATO!",
                    fx(Effects.NAUSEA, 200, 0), fx(Effects.WEAKNESS, 200, 1), fx(Effects.SLOWNESS, 200, 2))),
            m("Senso della vita", 25, 300, p -> lifeSense(p))
        });
        MOVES.put(StandType.SILVER_CHARIOT, new Move[] {
            m("Stoccate", 25, 40, p -> barrage(p, 6.0, 8, 2.5F, "SILVER CHARIOT!", 0)),
            m("Armor Off", 40, 400, p -> buff(p, "SILVER CHARIOT: ARMOR OFF!", SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP,
                    fx(Effects.SPEED, 200, 3), fx(Effects.STRENGTH, 200, 1))),
            m("Scatto con lo stocco", 30, 120, p -> rapierDash(p)),
            m("Parata", 30, 200, p -> buff(p, "SILVER CHARIOT: PARATA!", SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP,
                    fx(Effects.RESISTANCE, 60, 3), fx(Effects.SPEED, 60, 1)))
        });
        MOVES.put(StandType.MAGICIANS_RED, new Move[] {
            m("Pugni di fuoco", 25, 40, p -> barrage(p, 4.5, 5, 2.5F, "MAGICIAN'S RED: PUGNI DI FUOCO!", 8)),
            m("Crossfire Hurricane", 30, 80, p -> crossfire(p)),
            m("Red Bind", 50, 300, p -> fireRing(p)),
            m("Muro di fuoco", 40, 250, p -> fireWall(p))
        });
        MOVES.put(StandType.HIEROPHANT_GREEN, new Move[] {
            m("Emerald Splash", 25, 40, p -> rangedBarrage(p, 25, 5, 2.5F, "HIEROPHANT GREEN: EMERALD SPLASH!",
                    ParticleTypes.HAPPY_VILLAGER)),
            m("Tentacoli", 35, 200, p -> pullTarget(p)),
            m("Rete di tentacoli", 40, 300, p -> blast(p, 8, 3F, 0.0, 0, ParticleTypes.HAPPY_VILLAGER, 80,
                    "HIEROPHANT GREEN: RETE DI TENTACOLI!", true, fx(Effects.SLOWNESS, 120, 4))),
            m("Infiltrazione", 35, 250, p -> ranged(p, 15, 5F, 0.0, ParticleTypes.HAPPY_VILLAGER,
                    "HIEROPHANT GREEN: INFILTRAZIONE!", fx(Effects.POISON, 200, 1), fx(Effects.NAUSEA, 200, 0)))
        });
        MOVES.put(StandType.KING_CRIMSON, new Move[] {
            m("Death Chop", 25, 40, p -> barrage(p, 4.5, 5, 3.5F, "KING CRIMSON: DEATH CHOP!", 0)),
            m("Donut", 40, 200, p -> donut(p)),
            m("Erase Time", 60, 600, p -> eraseTime(p)),
            m("Salto nel tempo", 45, 300, p -> timeSkip(p))
        });
        MOVES.put(StandType.STICKY_FINGERS, new Move[] {
            m("Raffica ARI", 25, 40, p -> barrage(p, 4.5, 6, 2.8F, "ARI ARI ARI ARI ARRIVEDERCI!", 0)),
            m("Zipper", 35, 200, p -> zipperEscape(p)),
            m("Braccio zippato", 30, 160, p -> ranged(p, 10, 8F, 0.0, ParticleTypes.CLOUD,
                    "STICKY FINGERS: BRACCIO ZIPPATO!", fx(Effects.WEAKNESS, 200, 2), fx(Effects.SLOWNESS, 100, 1))),
            m("Onda zip", 40, 250, p -> blast(p, 4, 7F, 0.0, 0.7, ParticleTypes.CLOUD, 40,
                    "STICKY FINGERS: ONDA ZIP!", true))
        });
        MOVES.put(StandType.STONE_FREE, new Move[] {
            m("Raffica ORA", 25, 40, p -> barrage(p, 4.5, 6, 2.5F, "STONE FREE: ORA ORA ORA!", 0)),
            m("Fili", 30, 160, p -> ranged(p, 12, 4F, 0.0, ParticleTypes.CRIT, "STONE FREE: FILI!",
                    fx(Effects.SLOWNESS, 100, 5), fx(Effects.WEAKNESS, 100, 1))),
            m("Ali di filo", 30, 300, p -> buff(p, "STONE FREE: ALI DI FILO!", SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP,
                    fx(Effects.SLOW_FALLING, 300, 0), fx(Effects.JUMP_BOOST, 300, 3), fx(Effects.SPEED, 300, 1))),
            m("Rampino di filo", 20, 100, p -> grapple(p))
        });
    }

    // ---------------------------------------------------------- mosse generiche

    /** Raffica di colpi davanti a te. fireSeconds > 0 da' fuoco ai bersagli. */
    private static boolean barrage(ServerPlayerEntity p, double range, int hits, float dmg, String shout, int fireSeconds) {
        List<LivingEntity> targets = targetsInFront(p, range);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity t : targets) {
            for (int i = 0; i < hits; i++) {
                hit(p, t, dmg, i == hits - 1 ? 0.8 : 0.0);
            }
            if (fireSeconds > 0) t.setFire(fireSeconds);
            particles(p, ParticleTypes.CRIT, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(), 25, 0.4, 0.4, 0.4, 0.2);
        }
        say(p, shout);
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_STRONG);
        return true;
    }

    /** Colpo singolo a distanza sull'entita' che guardi, con effetti opzionali. */
    private static boolean ranged(ServerPlayerEntity p, double range, float dmg, double kb, IParticleData particle,
                                  String shout, EffectInstance... effects) {
        LivingEntity t = lookedAt(p, range);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        hit(p, t, dmg, kb);
        give(t, effects);
        beam(p, new Vector3d(t.getPosX(), t.getPosYHeight(0.5), t.getPosZ()), particle);
        say(p, shout);
        return true;
    }

    /** Raffica a distanza sull'entita' che guardi. */
    private static boolean rangedBarrage(ServerPlayerEntity p, double range, int hits, float dmg, String shout,
                                         IParticleData particle) {
        LivingEntity t = lookedAt(p, range);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        for (int i = 0; i < hits; i++) hit(p, t, dmg, i == hits - 1 ? 0.5 : 0.0);
        beam(p, new Vector3d(t.getPosX(), t.getPosYHeight(0.5), t.getPosZ()), particle);
        say(p, shout);
        return true;
    }

    /** Onda d'urto intorno a te: danno, spinta, lancio verso l'alto (lift) ed effetti. */
    private static boolean blast(ServerPlayerEntity p, double radius, float dmg, double kb, double lift,
                                 IParticleData particle, int count, String shout, boolean requireTarget,
                                 EffectInstance... effects) {
        List<LivingEntity> targets = around(p, radius);
        if (requireTarget && targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity t : targets) {
            hit(p, t, dmg, kb);
            if (lift > 0) {
                Vector3d mo = t.getMotion();
                t.setMotion(mo.x, lift, mo.z);
                t.velocityChanged = true;
            }
            give(t, effects);
        }
        particles(p, particle, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), count, radius / 2, 0.5, radius / 2, 0.05);
        say(p, shout);
        return true;
    }

    /** Potenziamento su te stesso. */
    private static boolean buff(ServerPlayerEntity p, String shout, SoundEvent snd, EffectInstance... effects) {
        give(p, effects);
        particles(p, ParticleTypes.CRIT, p.getPosX(), p.getPosYHeight(1.0), p.getPosZ(), 30, 0.5, 0.8, 0.5, 0.2);
        say(p, shout);
        sound(p, snd);
        return true;
    }

    // ---------------------------------------------------------- Star Platinum / The World

    // Star Platinum: inala e trascina verso di te chi hai davanti
    private static boolean inhale(ServerPlayerEntity p) {
        List<LivingEntity> targets = targetsInFront(p, 8);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity t : targets) {
            Vector3d v = p.getPositionVec().subtract(t.getPositionVec()).normalize().scale(1.2);
            t.setMotion(v.x, 0.2, v.z);
            t.velocityChanged = true;
            give(t, fx(Effects.SLOWNESS, 40, 3));
        }
        say(p, "STAR PLATINUM: INALA!");
        return true;
    }

    // Ferma il tempo: rallenta tutto nel raggio di 24 blocchi
    private static boolean timeStop(ServerPlayerEntity p, int ticks, String shout) {
        for (LivingEntity e : around(p, 24)) {
            give(e, fx(Effects.SLOWNESS, ticks, 9), fx(Effects.MINING_FATIGUE, ticks, 9), fx(Effects.WEAKNESS, ticks, 9));
        }
        give(p, fx(Effects.SPEED, ticks, 2), fx(Effects.STRENGTH, ticks, 1));
        say(p, shout);
        sound(p, SoundEvents.BLOCK_BEACON_ACTIVATE);
        return true;
    }

    // ---------------------------------------------------------- Crazy Diamond

    // Cura chi guardi (o te), toglie gli effetti negativi, ripara oggetti e armatura
    private static boolean restore(ServerPlayerEntity p) {
        LivingEntity t = lookedAt(p, 8);
        if (t == null) t = p;
        t.heal(10f);
        t.removePotionEffect(Effects.POISON);
        t.removePotionEffect(Effects.WITHER);
        t.removePotionEffect(Effects.NAUSEA);
        t.removePotionEffect(Effects.WEAKNESS);
        t.removePotionEffect(Effects.SLOWNESS);
        t.removePotionEffect(Effects.BLINDNESS);
        t.removePotionEffect(Effects.HUNGER);
        ItemStack held = p.getHeldItemMainhand();
        if (held.isDamaged()) held.setDamage(0);
        for (ItemStack armor : p.getArmorInventoryList()) {
            if (armor.isDamaged()) armor.setDamage(0);
        }
        particles(p, ParticleTypes.HEART, t.getPosX(), t.getPosYHeight(1.0), t.getPosZ(), 10, 0.4, 0.4, 0.4, 0.0);
        say(p, "CRAZY DIAMOND: RESTORE!");
        sound(p, SoundEvents.ENTITY_PLAYER_LEVELUP);
        return true;
    }

    // Cura tutti i giocatori nel raggio di 10 blocchi (te compreso)
    private static boolean healingWave(ServerPlayerEntity p) {
        List<PlayerEntity> players = p.world.getEntitiesWithinAABB(PlayerEntity.class, p.getBoundingBox().grow(10));
        for (PlayerEntity other : players) {
            other.heal(6f);
            particles(p, ParticleTypes.HEART, other.getPosX(), other.getPosYHeight(1.0), other.getPosZ(),
                    8, 0.4, 0.4, 0.4, 0.0);
        }
        say(p, "CRAZY DIAMOND: ONDA CURATIVA!");
        sound(p, SoundEvents.ENTITY_PLAYER_LEVELUP);
        return true;
    }

    // ---------------------------------------------------------- Killer Queen

    // Bomba sull'entita' che guardi (senza distruggere blocchi)
    private static boolean bombEntity(ServerPlayerEntity p) {
        LivingEntity t = lookedAt(p, 25);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        p.getServerWorld().createExplosion(p, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(), 3.0F, Explosion.Mode.NONE);
        say(p, "KILLER QUEEN: PRIMA BOMBA!");
        return true;
    }

    // Bomba sul blocco che guardi (distrugge blocchi!)
    private static boolean bombBlock(ServerPlayerEntity p) {
        RayTraceResult hr = p.pick(30.0D, 1.0F, false);
        if (hr.getType() != RayTraceResult.Type.BLOCK) { msg(p, "message.bizarremod.no_target"); return false; }
        Vector3d v = hr.getHitVec();
        p.getServerWorld().createExplosion(p, v.x, v.y, v.z, 3.5F, Explosion.Mode.BREAK);
        say(p, "KILLER QUEEN: BOMBA!");
        return true;
    }

    // Sheer Heart Attack: bombe automatiche sui 3 mostri ostili piu' vicini
    private static boolean sheerHeartAttack(final ServerPlayerEntity p) {
        List<LivingEntity> foes = p.world.getEntitiesWithinAABB(LivingEntity.class, p.getBoundingBox().grow(25),
                e -> e instanceof IMob && e.isAlive() && e != p);
        if (foes.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        foes.sort(Comparator.comparingDouble((LivingEntity e) -> e.getDistanceSq(p)));
        int count = Math.min(3, foes.size());
        for (int i = 0; i < count; i++) {
            LivingEntity t = foes.get(i);
            p.getServerWorld().createExplosion(p, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(), 2.0F, Explosion.Mode.NONE);
        }
        say(p, "KILLER QUEEN: SHEER HEART ATTACK!");
        return true;
    }

    // ---------------------------------------------------------- Gold Experience

    // Life Giver: fa crescere le piante intorno e ti rigenera
    private static boolean goldLife(ServerPlayerEntity p) {
        ServerWorld level = p.getServerWorld();
        BlockPos c = p.getPosition();
        BlockPos.getAllInBox(c.add(-6, -2, -6), c.add(6, 2, 6)).forEach(pos ->
                BoneMealItem.applyBonemeal(new ItemStack(Items.BONE_MEAL), level, pos.toImmutable()));
        give(p, fx(Effects.REGENERATION, 120, 1));
        p.heal(4f);
        particles(p, ParticleTypes.HAPPY_VILLAGER, p.getPosX(), p.getPosYHeight(1.0), p.getPosZ(), 40, 3, 1, 3, 0.0);
        say(p, "GOLD EXPERIENCE: LIFE GIVER!");
        return true;
    }

    // Percepisce la vita: fa brillare tutti gli esseri viventi nel raggio di 40 blocchi
    private static boolean lifeSense(final ServerPlayerEntity p) {
        List<LivingEntity> all = p.world.getEntitiesWithinAABB(LivingEntity.class, p.getBoundingBox().grow(40),
                e -> e != p && !(e instanceof StandEntity));
        for (LivingEntity e : all) give(e, fx(Effects.GLOWING, 200, 0));
        give(p, fx(Effects.NIGHT_VISION, 400, 0));
        say(p, "GOLD EXPERIENCE: SENSO DELLA VITA!");
        return true;
    }

    // ---------------------------------------------------------- Silver Chariot

    // Scatto con lo stocco: trafigge chi hai davanti
    private static boolean rapierDash(ServerPlayerEntity p) {
        List<LivingEntity> targets = targetsInFront(p, 6);
        Vector3d look = p.getLookVec();
        p.setMotion(look.x * 1.8, Math.max(0.15, look.y * 0.6), look.z * 1.8);
        p.velocityChanged = true;
        p.fallDistance = 0;
        for (LivingEntity t : targets) hit(p, t, 9f, 0.5);
        particles(p, ParticleTypes.SWEEP_ATTACK, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 5, 0.5, 0.3, 0.5, 0.0);
        say(p, "SILVER CHARIOT: SCATTO!");
        return true;
    }

    // ---------------------------------------------------------- Magician's Red

    // Crossfire Hurricane: colpisce a distanza e da' fuoco
    private static boolean crossfire(ServerPlayerEntity p) {
        LivingEntity t = lookedAt(p, 20);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        hit(p, t, 6f, 0.6);
        t.setFire(8);
        beam(p, new Vector3d(t.getPosX(), t.getPosYHeight(0.5), t.getPosZ()), ParticleTypes.FLAME);
        say(p, "MAGICIAN'S RED: CROSSFIRE HURRICANE!");
        return true;
    }

    // Red Bind: cerchio di fuoco intorno a te (tu sei immune al fuoco)
    private static boolean fireRing(ServerPlayerEntity p) {
        give(p, fx(Effects.FIRE_RESISTANCE, 200, 0));
        for (LivingEntity t : around(p, 6)) {
            hit(p, t, 5f, 0.8);
            t.setFire(8);
        }
        particles(p, ParticleTypes.FLAME, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 100, 3, 0.5, 3, 0.05);
        say(p, "MAGICIAN'S RED: RED BIND!");
        return true;
    }

    // Muro di fuoco davanti a te (attenzione: il fuoco puo' propagarsi al legno)
    private static boolean fireWall(ServerPlayerEntity p) {
        ServerWorld level = p.getServerWorld();
        Vector3d look = p.getLookVec();
        Vector3d flat = new Vector3d(look.x, 0, look.z);
        if (flat.lengthSquared() < 1.0E-4) { msg(p, "message.bizarremod.no_space"); return false; }
        flat = flat.normalize();
        Vector3d side = new Vector3d(-flat.z, 0, flat.x);
        int placed = 0;
        for (int dist = 2; dist <= 4; dist++) {
            for (int s = -3; s <= 3; s++) {
                BlockPos pos = new BlockPos(p.getPosX() + flat.x * dist + side.x * s, p.getPosY(),
                        p.getPosZ() + flat.z * dist + side.z * s);
                if (level.isAirBlock(pos) && Blocks.FIRE.getDefaultState().isValidPosition(level, pos)) {
                    level.setBlockState(pos, Blocks.FIRE.getDefaultState());
                    placed++;
                }
            }
        }
        if (placed == 0) { msg(p, "message.bizarremod.no_space"); return false; }
        say(p, "MAGICIAN'S RED: MURO DI FUOCO!");
        return true;
    }

    // ---------------------------------------------------------- Hierophant Green

    // I tentacoli trascinano il bersaglio verso di te
    private static boolean pullTarget(ServerPlayerEntity p) {
        LivingEntity t = lookedAt(p, 20);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        Vector3d v = p.getPositionVec().subtract(t.getPositionVec()).normalize().scale(1.5);
        hit(p, t, 4f, 0.0);
        t.setMotion(v.x, 0.4, v.z);
        t.velocityChanged = true;
        give(t, fx(Effects.SLOWNESS, 100, 2));
        beam(p, new Vector3d(t.getPosX(), t.getPosYHeight(0.5), t.getPosZ()), ParticleTypes.HAPPY_VILLAGER);
        say(p, "HIEROPHANT GREEN: TENTACOLI!");
        return true;
    }

    // ---------------------------------------------------------- King Crimson

    // Il Donut: un colpo devastante
    private static boolean donut(ServerPlayerEntity p) {
        List<LivingEntity> targets = targetsInFront(p, 3.5);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity t : targets) {
            hit(p, t, 20f, 1.0);
            particles(p, ParticleTypes.DAMAGE_INDICATOR, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(),
                    20, 0.4, 0.4, 0.4, 0.2);
        }
        say(p, "KING CRIMSON: DONUT!");
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_CRIT);
        return true;
    }

    // Cancella il tempo: 5 secondi di invisibilita', velocita' e resistenza quasi totale
    private static boolean eraseTime(ServerPlayerEntity p) {
        give(p, fx(Effects.INVISIBILITY, 100, 0), fx(Effects.SPEED, 100, 3), fx(Effects.RESISTANCE, 100, 4));
        say(p, "KING CRIMSON: EPITAPH... IL TEMPO E' CANCELLATO!");
        sound(p, SoundEvents.BLOCK_BEACON_DEACTIVATE);
        return true;
    }

    // Salto nel tempo: appari alle spalle del bersaglio e lo colpisci
    private static boolean timeSkip(ServerPlayerEntity p) {
        LivingEntity t = lookedAt(p, 15);
        if (t == null) { msg(p, "message.bizarremod.no_target"); return false; }
        Vector3d face = new Vector3d(t.getLookVec().x, 0, t.getLookVec().z);
        if (face.lengthSquared() < 1.0E-4) face = new Vector3d(p.getLookVec().x, 0, p.getLookVec().z);
        if (face.lengthSquared() < 1.0E-4) { msg(p, "message.bizarremod.no_space"); return false; }
        face = face.normalize();
        Vector3d dest = t.getPositionVec().subtract(face.scale(1.5));
        Vector3d delta = dest.subtract(p.getPositionVec());
        AxisAlignedBB moved = p.getBoundingBox().offset(delta.x, delta.y, delta.z);
        if (!p.world.hasNoCollisions(p, moved)) { msg(p, "message.bizarremod.no_space"); return false; }
        teleport(p, dest.x, dest.y, dest.z);
        hit(p, t, 15f, 0.5);
        particles(p, ParticleTypes.DAMAGE_INDICATOR, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(),
                15, 0.4, 0.4, 0.4, 0.2);
        say(p, "KING CRIMSON: SALTO NEL TEMPO!");
        return true;
    }

    // ---------------------------------------------------------- Sticky Fingers

    // Zipper: ti teletrasporta in avanti (anche oltre i muri)
    private static boolean zipperEscape(ServerPlayerEntity p) {
        Vector3d look = p.getLookVec();
        Vector3d flat = new Vector3d(look.x, 0, look.z);
        if (flat.lengthSquared() < 1.0E-4) { msg(p, "message.bizarremod.no_space"); return false; }
        flat = flat.normalize();
        for (int dist = 8; dist >= 2; dist--) {
            Vector3d off = flat.scale(dist);
            AxisAlignedBB moved = p.getBoundingBox().offset(off.x, 0, off.z);
            if (p.world.hasNoCollisions(p, moved)) {
                particles(p, ParticleTypes.CLOUD, p.getPosX(), p.getPosYHeight(1.0), p.getPosZ(), 20, 0.3, 0.6, 0.3, 0.05);
                teleport(p, p.getPosX() + off.x, p.getPosY(), p.getPosZ() + off.z);
                p.fallDistance = 0;
                particles(p, ParticleTypes.CLOUD, p.getPosX(), p.getPosYHeight(1.0), p.getPosZ(), 20, 0.3, 0.6, 0.3, 0.05);
                say(p, "STICKY FINGERS: ZIP!");
                return true;
            }
        }
        msg(p, "message.bizarremod.no_space");
        return false;
    }

    // ---------------------------------------------------------- Stone Free

    // Rampino di filo: ti lancia verso il blocco che guardi
    private static boolean grapple(ServerPlayerEntity p) {
        RayTraceResult hr = p.pick(30.0D, 1.0F, false);
        if (hr.getType() != RayTraceResult.Type.BLOCK) { msg(p, "message.bizarremod.no_target"); return false; }
        Vector3d target = hr.getHitVec();
        Vector3d dir = target.subtract(p.getEyePosition(1.0F)).normalize().scale(1.6);
        p.setMotion(dir.x, dir.y + 0.3, dir.z);
        p.velocityChanged = true;
        p.fallDistance = 0;
        beam(p, target, ParticleTypes.CRIT);
        say(p, "STONE FREE: RAMPINO DI FILO!");
        return true;
    }

    // ================================================================== STILI

    private static final Map<FightStyle, Move[]> STYLE_MOVES = new EnumMap<FightStyle, Move[]>(FightStyle.class);
    static {
        STYLE_MOVES.put(FightStyle.HAMON, new Move[] {
            m("Sunlight Yellow Overdrive", 30, 60, p -> hamon(p, JojoData.get(p))),
            m("Scarlet Overdrive", 25, 80, Abilities::scarletOverdrive),
            m("Respirazione Hamon", 20, 200, Abilities::hamonBreathing),
            m("Onda solare", 35, 120, Abilities::solarWave)
        });
        STYLE_MOVES.put(FightStyle.SPIN, new Move[] {
            m("Golden Spin", 30, 60, Abilities::spin),
            m("Steel Ball", 20, 60, Abilities::steelBall),
            m("Vortice rotante", 30, 120, Abilities::spinVortex),
            m("Rotazione difensiva", 25, 180, Abilities::spinGuard)
        });
        STYLE_MOVES.put(FightStyle.BOXING, new Move[] {
            m("Jab combinati", 20, 40, Abilities::boxing),
            m("Gancio pesante", 30, 90, Abilities::boxingHook),
            m("Montante", 25, 70, Abilities::boxingUppercut),
            m("Guardia del pugile", 20, 160, Abilities::boxingGuard)
        });
    }

    private static Move styleTechnique(FightStyle style, int index) {
        Move[] moves = STYLE_MOVES.get(style);
        return moves == null || index < 0 || index >= moves.length ? null : moves[index];
    }

    public static String styleMoveName(FightStyle style, int index) {
        Move technique = styleTechnique(style, index);
        return technique == null ? "-" : technique.name;
    }

    /** Read-only metadata for the authoritative server-to-client HUD snapshot. */
    public static float hudCost(boolean style, JojoData data, int index) {
        Move m = style ? styleTechnique(data.style, index) : move(data.stand, index);
        return m == null ? 0 : m.cost;
    }

    public static int hudDuration(boolean style, JojoData data, int index) {
        Move m = style ? styleTechnique(data.style, index) : move(data.stand, index);
        return m == null ? 0 : m.cooldown;
    }

    private static void cycleStyle(ServerPlayerEntity p, JojoData data) {
        if (data.style == FightStyle.NONE) { msg(p, "message.bizarremod.no_style"); return; }
        data.selectedStyleMove = (data.selectedStyleMove + 1) % 4;
        JojoData.save(p);
        Move technique = styleTechnique(data.style, data.selectedStyleMove);
        if (technique == null) return;
        p.sendStatusMessage(new TranslationTextComponent("message.bizarremod.style_selected",
                data.selectedStyleMove + 1, technique.name, (int) technique.cost, technique.cooldown / 20.0F), true);
        sound(p, SoundEvents.ENTITY_EXPERIENCE_ORB_PICKUP);
    }

    private static void styleMove(ServerPlayerEntity p, JojoData data) {
        if (data.style == FightStyle.NONE) { msg(p, "message.bizarremod.no_style"); return; }
        if (data.style == FightStyle.BOXING && !ModItems.hasBoxingGloves(p)) {
            msg(p, "message.bizarremod.gloves_required");
            return;
        }
        if (data.style == FightStyle.SPIN && !ModItems.hasSteelBall(p)) {
            msg(p, "message.bizarremod.steel_ball_required");
            return;
        }
        int index = data.selectedStyleMove;
        Move technique = styleTechnique(data.style, index);
        if (technique == null) return;
        if (p.world.getGameTime() < data.styleCooldowns[index]) {
            msg(p, "message.bizarremod.cooldown");
            return;
        }
        // Slot4 e' il breve blocco globale: cambiare tecnica non permette spam nello stesso tick.
        if (!ready(p, data, 4, technique.cost, false)) return;
        if (technique.action.test(p)) {
            commit(p, data, 4, technique.cost, 8);
            data.styleCooldowns[index] = p.world.getGameTime() + technique.cooldown;
            p.sendStatusMessage(new TranslationTextComponent("message.bizarremod.style_used", technique.name), true);
        }
    }

    private static boolean scarletOverdrive(ServerPlayerEntity p) {
        LivingEntity target = styleTarget(p, 4.5);
        if (target == null) return false;
        boolean undead = target.getCreatureAttribute() == CreatureAttribute.UNDEAD
                || (target instanceof PlayerEntity && JojoData.get((PlayerEntity) target).race != Race.HUMAN);
        hit(p, target, undead ? 14f : 8f, 0.7);
        target.setFire(6);
        particles(p, ParticleTypes.FLAME, target.getPosX(), target.getPosYHeight(0.5), target.getPosZ(), 24, 0.4, 0.5, 0.4, 0.03);
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_CRIT);
        return true;
    }

    private static boolean hamonBreathing(ServerPlayerEntity p) {
        if (JojoData.get(p).race != Race.HUMAN) {
            msg(p, "message.bizarremod.hamon_human_only");
            return false;
        }
        p.heal(4f);
        give(p, fx(Effects.REGENERATION, 100, 0), fx(Effects.RESISTANCE, 60, 0));
        particles(p, ParticleTypes.FIREWORK, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 25, 0.4, 0.6, 0.4, 0.02);
        return true;
    }

    private static boolean solarWave(ServerPlayerEntity p) {
        List<LivingEntity> targets = styleFront(p, 6);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity target : targets) {
            hit(p, target, 6f, 0.8);
            give(target, fx(Effects.SLOWNESS, 80, 1), fx(Effects.WEAKNESS, 60, 0));
            beam(p, target.getPositionVec().add(0, target.getHeight() * 0.5, 0), ParticleTypes.FIREWORK);
        }
        return true;
    }

    /** Colpo hitscan da 14 blocchi: richiede visuale libera e non crea entita' proiettile. */
    private static boolean steelBall(ServerPlayerEntity p) {
        LivingEntity target = styleTarget(p, 14);
        if (target == null) return false;
        beam(p, target.getPositionVec().add(0, target.getHeight() * 0.5, 0), ParticleTypes.CRIT);
        hit(p, target, 8f, 0.4);
        give(target, fx(Effects.SLOWNESS, 60, 1));
        return true;
    }

    private static boolean spinVortex(ServerPlayerEntity p) {
        List<LivingEntity> targets = around(p, 4);
        targets.removeIf(target -> !validStyleTarget(p, target) || p.getDistanceSq(target) > 16);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity target : targets) {
            hit(p, target, 6f, 1.2);
            give(target, fx(Effects.SLOWNESS, 60, 1));
        }
        particles(p, ParticleTypes.SWEEP_ATTACK, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 18, 2, 0.4, 2, 0);
        return true;
    }

    private static boolean spinGuard(ServerPlayerEntity p) {
        give(p, fx(Effects.RESISTANCE, 100, 1), fx(Effects.SPEED, 60, 0));
        particles(p, ParticleTypes.CRIT, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 25, 0.7, 0.7, 0.7, 0.03);
        return true;
    }

    private static boolean boxingHook(ServerPlayerEntity p) {
        LivingEntity target = styleTarget(p, 3);
        if (target == null) return false;
        hit(p, target, 10f, 1.3);
        give(target, fx(Effects.WEAKNESS, 60, 0));
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_STRONG);
        return true;
    }

    private static boolean boxingUppercut(ServerPlayerEntity p) {
        LivingEntity target = styleTarget(p, 3);
        if (target == null) return false;
        hit(p, target, 7f, 0.2);
        target.setMotion(target.getMotion().add(0, 0.65, 0));
        target.velocityChanged = true;
        give(target, fx(Effects.SLOWNESS, 40, 1));
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_CRIT);
        return true;
    }

    private static boolean boxingGuard(ServerPlayerEntity p) {
        give(p, fx(Effects.RESISTANCE, 80, 1), fx(Effects.SLOWNESS, 40, 0));
        sound(p, SoundEvents.ITEM_SHIELD_BLOCK);
        return true;
    }

    /** Evita alleati, spettatori, muri e PvP disabilitato per le tecniche degli stili. */
    private static boolean validStyleTarget(ServerPlayerEntity p, LivingEntity target) {
        if (!target.isAlive() || target == p || target instanceof StandEntity
                || target.isSpectator() || target.isOnSameTeam(p) || !p.canEntityBeSeen(target)) return false;
        return !(target instanceof PlayerEntity) || p.canAttackPlayer((PlayerEntity) target);
    }

    private static LivingEntity styleTarget(ServerPlayerEntity p, double range) {
        LivingEntity target = lookedAt(p, range);
        if (target == null || !validStyleTarget(p, target)) {
            msg(p, "message.bizarremod.no_target");
            return null;
        }
        return target;
    }

    private static List<LivingEntity> styleFront(ServerPlayerEntity p, double range) {
        List<LivingEntity> targets = targetsInFront(p, range);
        targets.removeIf(target -> !validStyleTarget(p, target));
        return targets;
    }

    // Hamon: onda d'energia solare. Devastante su non morti e su chi non e' umano.
    private static boolean hamon(ServerPlayerEntity p, JojoData d) {
        List<LivingEntity> targets = styleFront(p, 5);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        boolean hitUndead = false;
        for (LivingEntity t : targets) {
            boolean undead = t.getCreatureAttribute() == CreatureAttribute.UNDEAD
                    || (t instanceof PlayerEntity && JojoData.get((PlayerEntity) t).race != Race.HUMAN);
            float dmg = undead ? 14f : 5f;
            if (d.race == Race.HUMAN) dmg *= 1.25f;
            hit(p, t, dmg, 0.6);
            if (undead) { t.setFire(8); hitUndead = true; }
            particles(p, ParticleTypes.FIREWORK, t.getPosX(), t.getPosYHeight(0.5), t.getPosZ(), 30, 0.5, 0.5, 0.5, 0.1);
        }
        p.heal(hitUndead ? 6f : 2f);
        if (d.race != Race.HUMAN) p.attackEntityFrom(DamageSource.causeIndirectMagicDamage(p, p), 4f); // l'Hamon brucia i non umani
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_CRIT);
        say(p, "SUNLIGHT YELLOW OVERDRIVE!");
        return true;
    }

    // Spin: scatto rotante che ferisce e fa sanguinare
    private static boolean spin(ServerPlayerEntity p) {
        List<LivingEntity> targets = styleFront(p, 4);
        Vector3d look = p.getLookVec();
        p.setMotion(look.x * 1.6, Math.max(0.25, look.y * 0.8), look.z * 1.6);
        p.velocityChanged = true;
        p.fallDistance = 0;
        for (LivingEntity t : targets) {
            hit(p, t, 7f, 0.9);
            give(t, fx(Effects.WITHER, 60, 0));
        }
        particles(p, ParticleTypes.SWEEP_ATTACK, p.getPosX(), p.getPosYHeight(0.5), p.getPosZ(), 5, 0.5, 0.3, 0.5, 0.0);
        say(p, "GOLDEN SPIN!");
        return true;
    }

    // Pugilato: jab veloci e velocita'
    private static boolean boxing(ServerPlayerEntity p) {
        List<LivingEntity> targets = styleFront(p, 3);
        if (targets.isEmpty()) { msg(p, "message.bizarremod.no_target"); return false; }
        for (LivingEntity target : targets) {
            for (int jab = 0; jab < 4 && target.isAlive(); jab++) hit(p, target, 2f, 0.1);
        }
        give(p, fx(Effects.SPEED, 60, 0));
        sound(p, SoundEvents.ENTITY_PLAYER_ATTACK_SWEEP);
        return true;
    }

    // ================================================================== RAZZE

    private static void raceMove(ServerPlayerEntity p, JojoData d) {
        float cost = d.race == Race.PILLAR_MAN ? 60 : 40;
        int cooldown = d.race == Race.HUMAN ? 600 : (d.race == Race.VAMPIRE ? 160 : 300);
        if (!ready(p, d, 5, cost, false)) return;
        boolean ok = false;
        switch (d.race) {
            case HUMAN: ok = humanSpirit(p); break;
            case VAMPIRE: ok = ranged(p, 15, 12F, 0.5, ParticleTypes.END_ROD, "SPACE RIPPER STINGY EYES!"); break;
            case PILLAR_MAN: ok = blast(p, 6, 10F, 1.2, 0, ParticleTypes.CLOUD, 80, "DIVINE SANDSTORM!", true,
                    fx(Effects.BLINDNESS, 80, 0)); break;
            default: break;
        }
        if (ok) commit(p, d, 5, cost, cooldown);
    }

    // Umano: spirito indomito
    private static boolean humanSpirit(ServerPlayerEntity p) {
        p.heal(8f);
        give(p, fx(Effects.ABSORPTION, 400, 1));
        particles(p, ParticleTypes.HAPPY_VILLAGER, p.getPosX(), p.getPosYHeight(1.0), p.getPosZ(), 25, 0.5, 0.8, 0.5, 0.0);
        say(p, "SPIRITO INDOMITO!");
        sound(p, SoundEvents.ENTITY_PLAYER_LEVELUP);
        return true;
    }

    // ================================================================== UTILITA'

    private static void msg(ServerPlayerEntity p, String key) {
        p.sendStatusMessage(new TranslationTextComponent(key), true);
    }

    private static void say(ServerPlayerEntity p, String text) {
        p.sendStatusMessage(new StringTextComponent(text), true);
    }

    private static void sound(ServerPlayerEntity p, SoundEvent s) {
        p.world.playSound(null, p.getPosX(), p.getPosY(), p.getPosZ(), s, SoundCategory.PLAYERS, 1.0F, 1.0F);
    }

    private static void particles(ServerPlayerEntity p, IParticleData type, double x, double y, double z,
                                  int count, double dx, double dy, double dz, double speed) {
        p.getServerWorld().spawnParticle(type, x, y, z, count, dx, dy, dz, speed);
    }

    private static EffectInstance fx(Effect effect, int duration, int amplifier) {
        return new EffectInstance(effect, duration, amplifier);
    }

    /** Applica copie degli effetti (le istanze non vanno condivise fra entita'). */
    private static void give(LivingEntity e, EffectInstance... effects) {
        for (EffectInstance i : effects) e.addPotionEffect(new EffectInstance(i));
    }

    private static boolean ready(ServerPlayerEntity p, JojoData d, int slot, float cost, boolean needsStand) {
        if (needsStand) {
            if (d.stand == StandType.NONE) { msg(p, "message.bizarremod.no_stand"); return false; }
            if (!d.standActive) { msg(p, "message.bizarremod.not_summoned"); return false; }
        }
        if (p.world.getGameTime() < d.cooldowns[slot]) { msg(p, "message.bizarremod.cooldown"); return false; }
        if (d.energy < cost) { msg(p, "message.bizarremod.no_energy"); return false; }
        return true;
    }

    private static void commit(ServerPlayerEntity p, JojoData d, int slot, float cost, int cooldown) {
        d.energy -= cost;
        d.cooldowns[slot] = p.world.getGameTime() + cooldown;
    }

    /** Colpo "magico": ignora i frame di invulnerabilita', cosi' le raffiche funzionano. */
    private static void hit(ServerPlayerEntity p, LivingEntity t, float dmg, double knockback) {
        t.hurtResistantTime = 0;
        t.attackEntityFrom(DamageSource.causeIndirectMagicDamage(p, p), dmg);
        if (knockback > 0) t.applyKnockback((float) knockback, p.getPosX() - t.getPosX(), p.getPosZ() - t.getPosZ());
    }

    private static void teleport(ServerPlayerEntity p, double x, double y, double z) {
        p.connection.setPlayerLocation(x, y, z, p.rotationYaw, p.rotationPitch);
    }

    /** Raggio di particelle dal giocatore a un punto. */
    private static void beam(ServerPlayerEntity p, Vector3d to, IParticleData particle) {
        Vector3d from = p.getEyePosition(1.0F).add(0, -0.3, 0);
        Vector3d delta = to.subtract(from);
        for (int i = 0; i <= 20; i++) {
            Vector3d pos = from.add(delta.scale(i / 20.0));
            particles(p, particle, pos.x, pos.y, pos.z, 1, 0, 0, 0, 0);
        }
    }

    /** Tutte le entita' viventi nel raggio indicato (te e il tuo stand esclusi). */
    private static List<LivingEntity> around(final ServerPlayerEntity p, double radius) {
        return p.world.getEntitiesWithinAABB(LivingEntity.class, p.getBoundingBox().grow(radius),
                e -> e != p && e.isAlive() && !(e instanceof StandEntity) && !e.isOnSameTeam(p));
    }

    private static List<LivingEntity> targetsInFront(final ServerPlayerEntity p, final double range) {
        final Vector3d look = p.getLookVec();
        AxisAlignedBB box = p.getBoundingBox().expand(look.scale(range)).grow(1.0);
        return p.world.getEntitiesWithinAABB(LivingEntity.class, box, e -> {
            if (e == p || !e.isAlive() || e instanceof StandEntity || e.isOnSameTeam(p)) return false;
            Vector3d to = new Vector3d(e.getPosX(), e.getPosYHeight(0.5), e.getPosZ()).subtract(p.getEyePosition(1.0F));
            return to.length() <= range + 1 && to.normalize().dotProduct(look) > 0.4;
        });
    }

    private static LivingEntity lookedAt(final ServerPlayerEntity p, double range) {
        Vector3d eye = p.getEyePosition(1.0F);
        Vector3d look = p.getLookVec();
        Vector3d end = eye.add(look.scale(range));
        AxisAlignedBB box = p.getBoundingBox().expand(look.scale(range)).grow(1.0);
        EntityRayTraceResult r = ProjectileHelper.rayTraceEntities(p, eye, end, box,
                e -> e instanceof LivingEntity && e.isAlive() && !(e instanceof StandEntity) && e != p,
                range * range);
        return (r != null && r.getEntity() instanceof LivingEntity) ? (LivingEntity) r.getEntity() : null;
    }
}
