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
        self.assertEqual(9, len(names))
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
        self.assertIn('private static final String PROTOCOL = "3"', read('network/ModNetwork.java'))
        self.assertIn('msg.action <= Abilities.STYLE_CYCLE', read('network/ActionPacket.java'))

    def test_style_target_rules(self):
        abilities = read('logic/Abilities.java')
        self.assertIn('!p.canEntityBeSeen(target)', abilities)
        self.assertIn('p.canAttackPlayer((PlayerEntity) target)', abilities)
        self.assertIn('target.isOnSameTeam(p)', abilities)
        self.assertIn('targets.removeIf(target -> !validStyleTarget(p, target))', abilities)

    def test_release_version(self):
        self.assertIn("version = '1.2.0'", (ROOT/'build.gradle').read_text(encoding='utf-8'))
        self.assertIn('version="1.2.0"', (RESOURCES/'META-INF/mods.toml').read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
