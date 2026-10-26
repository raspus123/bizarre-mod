package com.example.bizarremod.client;

import com.mojang.blaze3d.matrix.MatrixStack;
import java.util.function.BooleanSupplier;
import java.util.function.Supplier;
import net.minecraft.client.gui.widget.button.Button;
import net.minecraft.util.text.StringTextComponent;

public class GoldButton extends Button {
    private final Supplier<String> label, detail;
    private final BooleanSupplier selected;
    public GoldButton(int x, int y, int w, int h, Supplier<String> label, Supplier<String> detail,
            BooleanSupplier selected, IPressable action) {
        super(x,y,w,h,new StringTextComponent(label.get()),action);
        this.label=label; this.detail=detail; this.selected=selected;
    }
    @Override public void render(MatrixStack m, int mouseX, int mouseY, float partial) {
        String title = label.get();
        if (!getMessage().getString().equals(title)) setMessage(new StringTextComponent(title));
        // Keep inherited widget behavior, then paint the custom skin over the default button.
        super.render(m, mouseX, mouseY, partial);
        boolean hovered = isHovered();
        ClientHud.panel(m,x,y,width,height, selected.getAsBoolean() ? ClientHud.GOLD
                : (hovered ? ClientHud.PURPLE : 0xFF514064));
        if (hovered) fill(m,x+6,y+2,x+width-2,y+height-2,0x443F2255);
        int color = active ? 0xFFEEE7F5 : 0xFF82788C;
        ClientHud.text(m,title,x+10,y+(height>=30 ? 5 : 6),color,width-20);
        if (height>=30) ClientHud.text(m,detail.get(),x+10,y+18,0xFFBFB1CC,width-20);
    }
}
