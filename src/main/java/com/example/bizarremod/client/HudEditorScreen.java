package com.example.bizarremod.client;

import com.mojang.blaze3d.matrix.MatrixStack;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.util.text.StringTextComponent;
import org.lwjgl.glfw.GLFW;

public class HudEditorScreen extends Screen {
    private boolean dragging;
    private double offsetX,offsetY;
    public HudEditorScreen(){super(new StringTextComponent("Bizarre / HUD editor"));}
    @Override protected void init(){
        int w=Math.min(106,(width-24)/3),x=(width-(w*3+8))/2;
        addButton(new GoldButton(x,height-28,w,22,()->ClientHud.tr("reset"),()->"",()->false,b->HudLayout.get().reset()));
        addButton(new GoldButton(x+w+4,height-28,w,22,
            ()->ClientHud.tr(HudLayout.get().visible?"hide":"show"),()->"",()->false,
            b->HudLayout.get().visible=!HudLayout.get().visible));
        addButton(new GoldButton(x+2*w+8,height-28,w,22,()->ClientHud.tr("save"),()->"",()->false,b->onClose()));
    }
    @Override public void render(MatrixStack m,int x,int y,float partial){
        // Deliberately do not dim the game, so other HUDs remain easy to position around.
        ClientHud.draw(m,width,height,true);
        ClientHud.text(m,ClientHud.tr("editor_hint"),8,8,ClientHud.GOLD,width-16);
        ClientHud.text(m,ClientHud.tr("editor_keys"),8,20,0xFFEEE7F5,width-16);
        super.render(m,x,y,partial);
    }
    @Override public boolean mouseClicked(double x,double y,int button){
        if(super.mouseClicked(x,y,button))return true;
        HudLayout l=HudLayout.get(); double s=l.effectiveScale(width,height);
        int left=l.left(width,height),top=l.top(width,height);
        if(button==0&&x>=left&&x<=left+236*s&&y>=top&&y<=top+124*s){
            dragging=true;offsetX=x-left;offsetY=y-top;return true;
        }
        return false;
    }
    @Override public boolean mouseDragged(double x,double y,int button,double dx,double dy){
        if(dragging&&button==0){HudLayout.get().position(x-offsetX,y-offsetY,width,height);return true;}
        return super.mouseDragged(x,y,button,dx,dy);
    }
    @Override public boolean mouseReleased(double x,double y,int button){
        if(button==0&&dragging){dragging=false;HudLayout.get().save();return true;}
        return super.mouseReleased(x,y,button);
    }
    @Override public boolean mouseScrolled(double x,double y,double amount){
        HudLayout l=HudLayout.get();l.scale+=amount*0.05;l.clamp();return true;
    }
    @Override public boolean keyPressed(int key,int scan,int mods){
        HudLayout l=HudLayout.get();int dx=0,dy=0;
        if(key==GLFW.GLFW_KEY_LEFT)dx=-1;if(key==GLFW.GLFW_KEY_RIGHT)dx=1;
        if(key==GLFW.GLFW_KEY_UP)dy=-1;if(key==GLFW.GLFW_KEY_DOWN)dy=1;
        if(dx!=0||dy!=0){int step=hasShiftDown()?10:1;l.position(l.left(width,height)+dx*step,l.top(width,height)+dy*step,width,height);return true;}
        if(key==GLFW.GLFW_KEY_R){l.reset();return true;}
        return super.keyPressed(key,scan,mods);
    }
    @Override public void onClose(){HudLayout.get().save();super.onClose();}
    @Override public boolean isPauseScreen(){return false;}
}
