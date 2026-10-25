package com.example.bizarremod.client;

import com.example.bizarremod.logic.Abilities;
import com.example.bizarremod.network.*;
import com.mojang.blaze3d.matrix.MatrixStack;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.util.text.StringTextComponent;

/** Selection only; all casts go through the existing server ability validation. */
public class AbilityScreen extends Screen {
    private boolean style = true;
    private int left, top, panelWidth;
    public AbilityScreen() { super(new StringTextComponent("Bizarre / Abilities")); }
    @Override protected void init() {
        panelWidth = Math.min(420, width-16); left=(width-panelWidth)/2; top=Math.max(4,(height-230)/2);
        addButton(new GoldButton(left+8,top+25,(panelWidth-20)/2,22,()->ClientHud.tr("stand"),()->"",()->!style,b->style=false));
        addButton(new GoldButton(left+12+(panelWidth-20)/2,top+25,(panelWidth-20)/2,22,()->ClientHud.tr("style"),()->"",()->style,b->style=true));
        for(int j=0;j<4;j++) {
            final int index=j;
            addButton(new GoldButton(left+8,top+65+j*33,panelWidth-16,31,
                ()->title(index),()->detail(index),()->ClientHud.state!=null
                    && (style?ClientHud.state.selectedStyle:ClientHud.state.selectedStand)==index,
                b->ModNetwork.CHANNEL.sendToServer(new SelectMovePacket(style,index))));
        }
        int bw=(panelWidth-24)/3;
        addButton(new GoldButton(left+8,top+199,bw,22,()->ClientHud.tr("use"),()->"",()->false,
            b->ModNetwork.CHANNEL.sendToServer(new ActionPacket(style?Abilities.STYLE:Abilities.USE))));
        addButton(new GoldButton(left+12+bw,top+199,bw,22,()->ClientHud.tr("move_hud"),()->"",()->false,
            b->minecraft.displayGuiScreen(new HudEditorScreen())));
        addButton(new GoldButton(left+16+bw*2,top+199,bw,22,()->ClientHud.tr("close"),()->"",()->false,b->onClose()));
    }
    private String title(int index) {
        HudStatePacket s=ClientHud.state;
        return (index+1)+" / "+(s==null?ClientHud.tr("waiting"):s.names[index+(style?4:0)]);
    }
    private String detail(int index) {
        HudStatePacket s=ClientHud.state; if(s==null)return "...";
        int i=index+(style?4:0), cd=ClientHud.ticks(i);
        String status;
        if(style&&!s.equipped)status=ClientHud.requirement();
        else if(!style&&!s.active)status=ClientHud.tr("stand_off");
        else if(cd>0)status=ClientHud.seconds(cd);
        else if(s.energy<s.costs[i])status=ClientHud.tr("low_energy");
        else status=ClientHud.tr("ready");
        return ClientHud.tr("cost",(int)s.costs[i])+" | CD "+ClientHud.seconds(s.duration[i])+" | "+status;
    }
    @Override public void render(MatrixStack m,int mx,int my,float partial) {
        renderBackground(m);
        ClientHud.panel(m,left,top,panelWidth,230,ClientHud.GOLD);
        ClientHud.text(m,"BIZARRE / "+ClientHud.tr("abilities"),left+12,top+9,ClientHud.GOLD,panelWidth-24);
        HudStatePacket s=ClientHud.state;
        String header=s==null?ClientHud.tr("waiting"):(style?s.style:s.stand)+" / "+ClientHud.tr("energy",Math.round(s.energy));
        ClientHud.text(m,header,left+12,top+52,style?ClientHud.styleColor():ClientHud.PURPLE,panelWidth-24);
        super.render(m,mx,my,partial);
    }
    @Override public boolean isPauseScreen(){return false;}
}
