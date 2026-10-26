#!/usr/bin/env python3
"""Source/resource regression checks, NOT a Forge compile or a Minecraft test."""
import unittest, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'src/main/java/com/example/bizarremod'
def read(path): return (JAVA/path).read_text(encoding='utf-8')
class HudChecks(unittest.TestCase):
    def test_spin_gate_before_resources(self):
        t=read('logic/Abilities.java'); t=t[t.index('private static void styleMove('):]
        a=t.index('data.style == FightStyle.SPIN && !ModItems.hasSteelBall(p)')
        self.assertLess(a,t.index('int index = data.selectedStyleMove'))
        self.assertIn('return;',t[a:t.index('int index = data.selectedStyleMove')])
        item=read('registry/ModItems.java'); item=item[item.index('public static boolean hasSteelBall'):]
        body=item[:item.index('\n    }')]
        self.assertIn('getHeldItemMainhand()',body); self.assertIn('getHeldItemOffhand()',body)
        self.assertNotIn('inventory',body)
    def test_snapshot_is_owner_only_and_authoritative(self):
        t=read('logic/GameEvents.java')
        self.assertIn('p.ticksExisted % 5 == 0',t)
        self.assertIn('PacketDistributor.PLAYER.with(() -> p)',t)
        self.assertIn('new com.example.bizarremod.network.HudStatePacket(p, d)',t)
        packet=read('network/HudStatePacket.java')
        self.assertIn('Math.max(d.styleCooldowns[j], d.cooldowns[4])',packet)
        self.assertIn('PLAY_TO_CLIENT',read('network/ModNetwork.java'))
        self.assertIn('PLAY_TO_SERVER',read('network/ModNetwork.java'))
        self.assertNotIn('JojoData.get',read('client/ClientHud.java'))
    def test_selection_is_bounded(self):
        t=read('network/SelectMovePacket.java')
        self.assertIn('p.index < 0 || p.index > 3',t)
        self.assertIn('getSender()',t)
        self.assertNotIn('d.energy =',t)
        self.assertNotIn('styleCooldowns[',t)
    def test_hud_does_not_cancel_other_overlays(self):
        t=read('client/ClientHud.java')
        self.assertIn('RenderGameOverlayEvent.Post',t)
        self.assertNotIn('setCanceled',t)
        self.assertIn('hideGUI',t)
        layout=read('client/HudLayout.java')
        self.assertIn('bizarremod-hud.json',layout)
        self.assertIn('Double.isFinite',layout)
        self.assertIn('Math.max(0.6, Math.min(1.5, scale))',layout)
        self.assertNotIn('inventoryhud',layout.lower())
    def test_controls_and_persistence(self):
        t=read('client/HudEditorScreen.java')
        for name in ['mouseClicked','mouseDragged','mouseReleased','mouseScrolled','keyPressed','onClose']:
            self.assertIn(name+'(',t)
        self.assertIn('HudLayout.get().save()',t)
        keys=read('client/ClientKeys.java')
        self.assertIn('GLFW_KEY_J',keys); self.assertIn('GLFW_KEY_K',keys)
        for name in ['MENU','EDIT_HUD']:
            self.assertIn('registerKeyBinding(ClientKeys.'+name+')',read('client/ClientSetup.java'))
    def test_all_gui_keys_translated(self):
        import re
        keys=set()
        for path in (JAVA/'client').glob('*.java'):
            keys.update(re.findall(r'(?:ClientHud\.)?tr\("([a-z_]+)"\s*[,)]',path.read_text(encoding='utf-8')))
        keys.update(['hide','show','need_ball','need_gloves'])
        for lang in ['it_it','en_us']:
            t=json.loads((ROOT/('src/main/resources/assets/bizarremod/lang/'+lang+'.json')).read_text(encoding='utf-8'))
            self.assertFalse({'gui.bizarremod.'+k for k in keys}-set(t))
    def test_layout_math_screen_bounds(self):
        # Mirror the explicit layout equations across resolutions and scales.
        import re
        m = re.search(r'public static final int W = (\d+), H = (\d+);', read('client/ClientHud.java'))
        self.assertIsNotNone(m)
        hud_w, hud_h = int(m.group(1)), int(m.group(2))
        for w,h in [(160,120),(320,240),(854,480),(1920,1080),(3440,1440)]:
            for scale in [0.6,1.0,1.5]:
                s=min(scale,w/hud_w,h/hud_h)
                for fraction in [0,0.02,0.62,1]:
                    left=round(fraction*max(0,w-hud_w*s));top=round(fraction*max(0,h-hud_h*s))
                    self.assertGreaterEqual(left,0);self.assertGreaterEqual(top,0)
                    self.assertLessEqual(left+hud_w*s,w+0.51)
                    self.assertLessEqual(top+hud_h*s,h+0.51)
    def test_hud_icons_exist_for_every_row(self):
        import re
        hud = read('client/ClientHud.java')
        self.assertIn('"move_" + j', hud)
        self.assertIn('(style ? "style_" : "stand_") + id', hud)
        self.assertNotIn('JojoData.get', hud)
if __name__=='__main__': unittest.main(verbosity=2)
