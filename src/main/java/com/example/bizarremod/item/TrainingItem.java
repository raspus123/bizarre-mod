package com.example.bizarremod.item;

import com.example.bizarremod.data.FightStyle;
import com.example.bizarremod.data.JojoData;
import com.example.bizarremod.registry.ModItems;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.client.util.ITooltipFlag;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.text.ITextComponent;
import net.minecraft.util.text.TranslationTextComponent;
import net.minecraft.world.World;

/** Pergamene monouso o guanti permanenti. Lo stile appreso non richiede di tenere la pergamena. */
public class TrainingItem extends Item {
    private final FightStyle style;
    private final boolean consumable;
    private final String tooltip;

    public TrainingItem(Properties properties, FightStyle style, boolean consumable, String tooltip) {
        super(properties);
        this.style = style;
        this.consumable = consumable;
        this.tooltip = tooltip;
    }

    @Override
    public ActionResult<ItemStack> onItemRightClick(World world, PlayerEntity player, Hand hand) {
        ItemStack stack = player.getHeldItem(hand);
        if (world.isRemote) return ActionResult.resultSuccess(stack);
        if (player.isSpectator()) return ActionResult.resultFail(stack);
        JojoData data = JojoData.get(player);
        if (data.style == style) {
            player.sendStatusMessage(new TranslationTextComponent("message.bizarremod.style_known"), true);
            return ActionResult.resultFail(stack);
        }
        if (style == FightStyle.BOXING && !ModItems.hasBoxingGloves(player)) {
            player.sendStatusMessage(new TranslationTextComponent("message.bizarremod.gloves_required"), true);
            return ActionResult.resultFail(stack);
        }
        data.style = style;
        data.selectedStyleMove = 0;
        JojoData.save(player);
        player.sendStatusMessage(new TranslationTextComponent("message.bizarremod.style_learned", style.displayName()), false);
        player.sendStatusMessage(new TranslationTextComponent("message.bizarremod.style_controls"), true);
        if (consumable && !player.abilities.isCreativeMode) stack.shrink(1);
        return ActionResult.resultSuccess(stack);
    }

    @Override
    public void addInformation(ItemStack stack, @Nullable World world, List<ITextComponent> lines, ITooltipFlag flag) {
        lines.add(new TranslationTextComponent(tooltip));
        lines.add(new TranslationTextComponent("tooltip.bizarremod.training_controls"));
    }
}
