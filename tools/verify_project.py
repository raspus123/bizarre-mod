#!/usr/bin/env python3
"""Static regression checks. No Minecraft process is started by this script."""
import json
import re
import struct
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'src/main/java/com/example/bizarremod'
ASSETS = ROOT / 'src/main/resources/assets/bizarremod'
RESOURCES = ROOT / 'src/main/resources'

def read(name):
    return (JAVA / name).read_text(encoding='utf-8')

def png_size_and_crc(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    offset, size, ended = 8, None, False
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset+4])[0]
        tag = data[offset+4:offset+8]
        payload = data[offset+8:offset+8+length]
        crc = struct.unpack('>I', data[offset+8+length:offset+12+length])[0]
        assert zlib.crc32(tag + payload) & 0xffffffff == crc, path
        if tag == b'IHDR': size = struct.unpack('>II', payload[:8])
        if tag == b'IEND': ended = True
        offset += 12 + length
    assert ended and offset == len(data), path
    return size

class ProjectChecks(unittest.TestCase):
    def test_json_valid(self):
        paths = list((ROOT / 'src/main/resources').rglob('*.json'))
        self.assertGreater(len(paths), 10)
        for path in paths:
            with self.subTest(path=path):
                self.assertIsInstance(json.loads(path.read_text(encoding='utf-8')), dict)

    def test_translations(self):
        it = json.loads((ASSETS / 'lang/it_it.json').read_text(encoding='utf-8'))
        en = json.loads((ASSETS / 'lang/en_us.json').read_text(encoding='utf-8'))
        self.assertEqual(set(it), set(en))
        keys = set()
        for path in JAVA.rglob('*.java'):
            keys.update(re.findall(r'"((?:message|tooltip|key|item)\.bizarremod\.[a-z_]+)"', path.read_text(encoding='utf-8')))
        self.assertFalse(keys - set(it), 'Untranslated keys: %s' % sorted(keys-set(it)))
        for key in it:
            self.assertEqual(it[key].count('%s'), en[key].count('%s'), key)

    def test_item_resources(self):
        registry = read('registry/ModItems.java')
        names = re.findall(r'ITEMS\.register\("([a-z_]+)"', registry)
        self.assertEqual(12, len(names))   # 9 oggetti di gioco + 3 sprite dei proiettili
        for name in names:
            with self.subTest(item=name):
                model = json.loads((ASSETS / ('models/item/' + name + '.json')).read_text(encoding='utf-8'))
                texture = model['textures']['layer0']
                if texture.startswith('bizarremod:'):
                    image = ASSETS / ('textures/' + texture.split(':',1)[1] + '.png')
                    width, height = png_size_and_crc(image)
                    self.assertGreater(width, 0)
                    self.assertGreater(height, 0)
                    self.assertEqual(width, height)

    def test_recipe_unlocks(self):
        for name in ('hamon_scroll','spin_scroll','boxing_gloves','steel_ball'):
            recipe = json.loads((RESOURCES / ('data/bizarremod/recipes/' + name + '.json')).read_text(encoding='utf-8'))
            self.assertEqual('bizarremod:'+name, recipe['result']['item'])
            self.assertEqual(1, recipe['result']['count'])
            used = set(''.join(recipe['pattern'])) - {' '}
            self.assertEqual(used, set(recipe['key']))
            advancement = json.loads((RESOURCES / ('data/bizarremod/advancements/recipes/' + name + '.json')).read_text(encoding='utf-8'))
            self.assertIn('bizarremod:'+name, advancement['rewards']['recipes'])

    def test_stand_forge_attributes(self):
        entity = read('entity/StandEntity.java')
        self.assertIn('MobEntity.func_233666_p_()', entity)
        self.assertNotIn('AttributeModifierMap.createMutableAttribute()', entity)
        self.assertIn('NetworkHooks.getEntitySpawningPacket(this)', entity)
        self.assertIn('IPacket<?> createSpawnPacket()', entity)
        self.assertIn('this.setNoAI(true)', entity)
        self.assertIn('event.put(ModEntities.STAND.get(), StandEntity.createAttributes())', read('BizarreMod.java'))
        self.assertNotIn('GlobalEntityTypeAttributes.put', read('BizarreMod.java'))
        self.assertIn('.disableSerialization()', read('registry/ModEntities.java'))

    def test_stand_state_and_cleanup(self):
        abilities = read('logic/Abilities.java')
        toggle = abilities.split('private static void toggleStand(',1)[1].split('/** Passa alla mossa',1)[0]
        self.assertLess(toggle.index('addEntity(entity)'), toggle.index('d.standActive = true'))
        self.assertIn('d.activeStandId = entity.getUniqueID()', toggle)
        self.assertIn('equals(data.activeStandId)', read('entity/StandEntity.java'))
        for callback in ('onDimensionChange','onDeath','onLogout'):
            self.assertIn(callback, read('logic/GameEvents.java'))
        data = read('data/JojoData.java')
        self.assertNotIn('putUniqueId', data)  # Runtime stand id must not survive reload.
        self.assertNotIn('putBoolean("standActive"', data)

    def test_four_moves_each(self):
        abilities = read('logic/Abilities.java')
        for style in ('HAMON','SPIN','BOXING'):
            block = abilities.split('STYLE_MOVES.put(FightStyle.'+style+', new Move[] {',1)[1].split('});',1)[0]
            self.assertEqual(4, len(re.findall(r'\bm\("', block)), style)
        self.assertIn('new long[4]', read('data/JojoData.java'))
        self.assertIn('Math.floorMod(t.getInt("styleMove"), 4)', read('data/JojoData.java'))
        self.assertIn('data.styleCooldowns[index]', abilities)
        self.assertIn('commit(p, data, 4, technique.cost, 8)', abilities)
        move = abilities.split('private static void styleMove(',1)[1].split('private static boolean scarletOverdrive',1)[0]
        self.assertLess(move.index('technique.action.test(p)'), move.index('commit(p, data'))

    def test_boxing_equipment_guards(self):
        registry = read('registry/ModItems.java')
        self.assertIn('getHeldItemMainhand().getItem() == BOXING_GLOVES.get()', registry)
        self.assertIn('getHeldItemOffhand().getItem() == BOXING_GLOVES.get()', registry)
        self.assertIn('data.style == FightStyle.BOXING && !ModItems.hasBoxingGloves(p)', read('logic/Abilities.java'))
        events = read('logic/GameEvents.java')
        self.assertIn('d.style == FightStyle.BOXING && ModItems.hasBoxingGloves(p)', events)
        self.assertLess(events.index('ModifiableAttributeInstance speed ='), events.index('p.ticksExisted % 20 != 0'))
        self.assertIn('speed.removeModifier(BOXING_SPEED_ID)', events)
        self.assertIn('false, "tooltip.bizarremod.boxing_gloves"', registry)
        training = read('item/TrainingItem.java')
        self.assertIn('if (consumable && !player.abilities.isCreativeMode) stack.shrink(1)', training)
        self.assertLess(training.index('if (data.style == style)'), training.index('stack.shrink(1)'))

    def test_style_input_and_protocol(self):
        self.assertIn('GLFW.GLFW_KEY_B', read('client/ClientKeys.java'))
        self.assertIn('registerKeyBinding(ClientKeys.STYLE_CYCLE)', read('client/ClientSetup.java'))
        self.assertIn('poll(ClientKeys.STYLE_CYCLE, Abilities.STYLE_CYCLE)', read('client/ClientEvents.java'))
        self.assertIn('case STYLE_CYCLE: cycleStyle(p, d)', read('logic/Abilities.java'))
        self.assertIn('private static final String PROTOCOL = "4"', read('network/ModNetwork.java'))
        self.assertIn('msg.action <= Abilities.STYLE_CYCLE', read('network/ActionPacket.java'))

    def test_style_target_rules(self):
        abilities = read('logic/Abilities.java')
        self.assertIn('!p.canEntityBeSeen(target)', abilities)
        self.assertIn('p.canAttackPlayer((PlayerEntity) target)', abilities)
        self.assertIn('target.isOnSameTeam(p)', abilities)
        self.assertIn('targets.removeIf(target -> !validStyleTarget(p, target))', abilities)

    def test_release_version(self):
        self.assertIn("version = '1.5.0'", (ROOT/'build.gradle').read_text(encoding='utf-8'))
        self.assertIn('version="1.5.0"', (RESOURCES/'META-INF/mods.toml').read_text(encoding='utf-8'))

    def test_steel_ball_is_a_real_projectile(self):
        abilities = read('logic/Abilities.java')
        self.assertIn('m("Lancio della sfera", 20, 60, Abilities::throwSteelBall)', abilities)
        self.assertNotIn('Abilities::steelBall', abilities)
        body = abilities[abilities.index('private static boolean throwSteelBall'):abilities.index('private static boolean launchBall')]
        self.assertNotIn('shrink', body)            # la sfera in mano non viene consumata
        self.assertIn('new SteelBallEntity(p.world, p)', body)
        entity = read('entity/SteelBallEntity.java')
        self.assertIn('extends ProjectileItemEntity', entity)
        self.assertIn('NetworkHooks.getEntitySpawningPacket(this)', entity)
        self.assertIn('Abilities.projectileHit', entity)
        self.assertIn('MAX_AGE', entity)
        self.assertIn('STEEL_BALL = ENTITIES.register("steel_ball"', read('registry/ModEntities.java'))
        self.assertIn('new SpriteRenderer<SteelBallEntity>', read('client/ClientSetup.java'))
        # il blocco delle tecniche Spin senza sfera in mano resta prima di ogni risorsa
        self.assertIn('ModItems.hasSteelBall(p)', abilities)

    def test_stand_textures_and_hud_icons(self):
        stands = [i for i in re.findall(r'[A-Z_]+\("([a-z_]+)"', read('data/StandType.java')) if i != 'none']
        styles = [i for i in re.findall(r'[A-Z_]+\("([a-z_]+)"', read('data/FightStyle.java')) if i != 'none']
        self.assertEqual(len(stands), 11)
        self.assertEqual(len(styles), 3)
        for stand in stands:
            # modello "giocatore" di 1.16.5 con secondo strato: texture 64x64
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/entity/stand/{stand}.png'), (64, 64), stand)
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/gui/hud/stand_{stand}.png'), (16, 16), stand)
        for style in styles:
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/gui/hud/style_{style}.png'), (16, 16), style)
        for i in range(4):
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/gui/hud/move_{i}.png'), (16, 16), i)

    def test_hud_sends_stand_id_for_client_translation(self):
        packet = read('network/HudStatePacket.java')
        self.assertIn('standId = d.stand.id;', packet)
        self.assertIn('b.writeString(p.standId)', packet)
        self.assertIn('p.standId = b.readString(32)', packet)
        hud = read('client/ClientHud.java')
        self.assertIn('I18n.format("stand.bizarremod." + state.standId)', hud)
        self.assertIn('textures/gui/hud/', hud)

    def test_every_stand_opens_with_a_punch_barrage(self):
        abilities = read('logic/Abilities.java')
        blocks = re.findall(r'MOVES\.put\(StandType\.([A-Z_]+), new Move\[\] \{(.*?)\n        \}\);', abilities, re.S)
        self.assertEqual(11, len(blocks))
        for stand, body in blocks:
            first = re.search(r'm[ps]?\("[^"]+", [^\n]*', body).group(0)
            self.assertTrue(first.startswith('mp('), stand)        # posa dei pugni
            self.assertIn('p -> barrage(p, ', first, stand)        # la prima mossa e' sempre una raffica di pugni
            self.assertNotIn('shoot(', first, stand)
        stand_entity = read('entity/StandEntity.java')
        self.assertIn('stand.startBarrage(pulses, range, dmg, fireSeconds)', abilities)
        self.assertIn('public static void barragePulse(', abilities)
        self.assertIn('--pulseTimer <= 0', stand_entity)           # un'ondata ogni 2 tick
        self.assertIn('Abilities.barragePulse(', stand_entity)
        self.assertIn('this.swingArm(Hand.MAIN_HAND);', stand_entity)

    def test_far_moves_are_projectiles(self):
        abilities = read('logic/Abilities.java')
        last_block = abilities.index('MOVES.put(StandType.STONE_FREE')
        moves = abilities[abilities.index('MOVES.put(StandType.STAR_PLATINUM'):abilities.index('\n        });', last_block)]
        for call in ('starFinger(p)', 'throwKnives(p)', 'bombCoin(p, 3.0F', 'bombCoin(p, 3.5F', 'sheerHeartAttack(p)',
                     'crossfire(p)', 'emeraldSplash(p)', 'tentacle(p)', 'zipArm(p)', 'threads(p)'):
            self.assertIn(call, moves, call)
        self.assertNotIn('rangedBarrage(', moves)
        for name in ('starFinger', 'throwKnives', 'crossfire', 'emeraldSplash', 'tentacle', 'bombCoin', 'zipArm',
                     'threads', 'stingyEyes'):
            start = abilities.index('private static boolean %s(' % name)
            body = abilities[start:abilities.index('\n    }\n', start)]
            self.assertIn('shoot(', body, name)
        self.assertIn('Items.EMERALD', abilities)
        shot = read('entity/StandShotEntity.java')
        self.assertIn('extends ProjectileItemEntity', shot)
        self.assertIn('NetworkHooks.getEntitySpawningPacket(this)', shot)
        self.assertIn('Abilities.projectileHit(', shot)
        self.assertIn('STAND_SHOT = ENTITIES.register("stand_shot"', read('registry/ModEntities.java'))
        self.assertIn('new SpriteRenderer<StandShotEntity>', read('client/ClientSetup.java'))

    def test_spin_moves_throw_the_ball_and_it_returns(self):
        abilities = read('logic/Abilities.java')
        for name in ('throwSteelBall', 'bounceBall', 'spinVortex', 'spinGuard'):
            start = abilities.index('private static boolean %s(' % name)
            body = abilities[start:abilities.index('\n    }\n', start)]
            self.assertTrue('new SteelBallEntity(' in body or 'orbitBalls(' in body, name)
        start = abilities.index('private static boolean orbitBalls(')
        self.assertIn('new SteelBallEntity(p.world, p)', abilities[start:abilities.index('\n    }\n', start)])
        ball = read('entity/SteelBallEntity.java')
        for needle in ('private void returnStep(', 'private void startReturn()', 'private void orbitStep(',
                       'catchBall(owner);', 'if (++phaseTicks >= outTicks) startReturn();',
                       'if (++phaseTicks >= orbitTicks) startReturn();'):
            self.assertIn(needle, ball, needle)
        self.assertIn('.setUpdateInterval(1)', read('registry/ModEntities.java'))   # posizione inviata a ogni tick

    def test_new_item_art(self):
        for name in ('hamon_scroll', 'spin_scroll', 'boxing_manual', 'red_stone_of_aja',
                     'projectile_knife', 'projectile_star', 'projectile_zip'):
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/item/{name}.png'), (16, 16), name)
        for name in ('stand_arrow', 'stone_mask', 'steel_ball'):          # ridisegnati piu' dettagliati
            self.assertEqual(png_size_and_crc(ASSETS / f'textures/item/{name}.png'), (32, 32), name)

    def test_stands_perform_the_abilities(self):
        stand = read('entity/StandEntity.java')
        abilities = read('logic/Abilities.java')
        renderer = read('client/StandRenderer.java')
        self.assertIn('ANIM =\n            EntityDataManager.createKey(StandEntity.class, DataSerializers.VARINT)', stand)
        self.assertIn('this.dataManager.register(ANIM, ANIM_NONE);', stand)
        self.assertIn('public static Vector3d actionPosition(PlayerEntity owner, int anim)', stand)
        self.assertIn('public void animate(int type, int ticks)', stand)
        self.assertIn('Vector3d spot = actionPosition(owner, this.getAnimation());', stand)
        self.assertIn('new PlayerModel<StandEntity>(0.0F, false)', renderer)
        self.assertIn('BipedModel.ArmPose.BOW_AND_ARROW', renderer)
        self.assertIn('BipedModel.ArmPose.THROW_SPEAR', renderer)
        self.assertIn('animateStand(p, m.anim);', abilities)
        self.assertIn('StandEntity.actionPosition(p, StandEntity.ANIM_SHOOT).add(0, 1.3, 0)', abilities)
        self.assertIn('Vector3d origin = shotOrigin(p);', abilities)
        for name in ('Star Finger', 'Coltelli', 'Crossfire Hurricane', 'Emerald Splash', 'Tentacoli', 'Bomba su entità',
                     'Bomba su blocco', 'Sheer Heart Attack', 'Braccio zippato', 'Fili'):
            self.assertIn('ms("%s",' % name, abilities, name)      # i colpi a distanza usano la posa di tiro
        self.assertIn('if (stand != null) stand.animate(StandEntity.ANIM_POWER, ticks);', abilities)  # Time Stop

    def test_bouncing_ball_replaces_golden_spin(self):
        abilities = read('logic/Abilities.java')
        self.assertIn('m("Sfera rimbalzante", 30, 60, Abilities::bounceBall)', abilities)
        self.assertNotIn('Golden Spin', abilities)
        self.assertIn('.bouncing(3)', abilities)
        ball = read('entity/SteelBallEntity.java')
        self.assertIn('public SteelBallEntity bouncing(int count)', ball)
        self.assertIn('private boolean redirect(', ball)
        self.assertIn('hitSet.contains(hit.getUniqueID())', ball)
        self.assertIn('Abilities.canProjectileHit(owner, e)', ball)
        self.assertIn('public static boolean canProjectileHit(', abilities)

if __name__ == '__main__':
    unittest.main(verbosity=2)
