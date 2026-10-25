package dev.shadowsoffire.apothic_enchanting;

import java.math.BigDecimal;

import dev.shadowsoffire.apothic_attributes.repack.evalex.Expression;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.Holder;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.enchantment.Enchantment;

/**
 * Simple int to int function, used for converting a level into a required enchanting power.
 */
public sealed interface PowerFunction {

    public static StreamCodec<RegistryFriendlyByteBuf, PowerFunction> STREAM_CODEC = new StreamCodec<>(){

        @Override
        public PowerFunction decode(RegistryFriendlyByteBuf buf) {
            Type type = Type.values()[buf.readByte()];
            return switch (type) {
                case DEFAULT_MIN -> DefaultMinPowerFunction.STREAM_CODEC.decode(buf);
                case DEFAULT_MAX -> DefaultMaxPowerFunction.INSTANCE;
                case EXPRESSION -> ExpressionPowerFunction.STREAM_CODEC.decode(buf);
            };
        }

        @Override
        public void encode(RegistryFriendlyByteBuf buf, PowerFunction value) {
            Type type = value.getType();
            buf.writeByte(type.ordinal());
            switch (type) {
                case DEFAULT_MIN:
                    DefaultMinPowerFunction.STREAM_CODEC.encode(buf, (DefaultMinPowerFunction) value);
                    break;
                case EXPRESSION:
                    ExpressionPowerFunction.STREAM_CODEC.encode(buf, (ExpressionPowerFunction) value);
                    break;
                default:
            }
        }

    };

    int getPower(int level);

    Type getType();

    public static enum Type {
        DEFAULT_MIN,
        DEFAULT_MAX,
        EXPRESSION;
    }

    /**
     * This is the default minimum power function.
     * If the level is equal to or below the default max level, we return the original value {@link Enchantment#getMinCost(int)}
     * If the level is above than the default max level, then we compute the following:
     * Let diff be the slope of {@link Enchantment#getMinCost(int)}, or 15, if the slope would be zero.
     * minPower = baseMinPower + diff * (level - baseMaxLevel) ^ 1.6
     */
    public static record DefaultMinPowerFunction(Holder<Enchantment> enchHolder) implements PowerFunction {

        public static final StreamCodec<RegistryFriendlyByteBuf, DefaultMinPowerFunction> STREAM_CODEC = Enchantment.STREAM_CODEC.map(DefaultMinPowerFunction::new, DefaultMinPowerFunction::enchHolder);

        @Override
        public int getPower(int level) {
            Enchantment ench = enchHolder.value();
            if (level > ench.definition().maxLevel() && level > 1) {
                int diff = ench.getMinCost(ench.getMaxLevel()) - ench.getMinCost(ench.getMaxLevel() - 1);
                if (diff == 0) diff = 15;
                return ench.getMinCost(level) + diff * (int) Math.pow(level - ench.getMaxLevel(), 1.6);
            }
            return ench.getMinCost(level);
        }

        @Override
        public Type getType() {
            return Type.DEFAULT_MIN;
        }

        public Holder<Enchantment> enchHolder() {
            return this.enchHolder;
        }

    }

    public static final class DefaultMaxPowerFunction implements PowerFunction {

        public static final DefaultMaxPowerFunction INSTANCE = new DefaultMaxPowerFunction();

        @Override
        public int getPower(int level) {
            return 200;
        }

        @Override
        public Type getType() {
            return Type.DEFAULT_MAX;
        }

    }

    public static final class ExpressionPowerFunction implements PowerFunction {

        public static final StreamCodec<ByteBuf, ExpressionPowerFunction> STREAM_CODEC = ByteBufCodecs.STRING_UTF8.map(ExpressionPowerFunction::new, ExpressionPowerFunction::exprString);

        private final String exprString;
        private transient final Expression ex;

        public ExpressionPowerFunction(String func) {
            this.exprString = func;
            this.ex = new Expression(func);
        }

        @Override
        public int getPower(int level) {
            return this.ex.setVariable("x", new BigDecimal(level)).eval().intValue();
        }

        @Override
        public Type getType() {
            return Type.EXPRESSION;
        }

        public String exprString() {
            return this.exprString;
        }

    }
}
