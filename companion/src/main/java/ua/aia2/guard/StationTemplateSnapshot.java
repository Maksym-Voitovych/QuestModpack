package ua.aia2.guard;

import java.lang.reflect.Field;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/**
 * Bounded immutable definition of the native single-palette, entity-free station template.
 * Any block NBT is unsupported and rejected before serialization or copying. The shipped
 * Ad Astra station has no block NBT; snapshots include explicit air cells as well as solids.
 */
public record StationTemplateSnapshot(BlockPos size, Map<BlockPos, BlockState> allBlocks) {
    public static final int MAX_AXIS = 64;
    public static final int MAX_VOLUME = 65536;
    public static final int MAX_BLOCKS = 65536;

    private record Fields(Field palettes, Field entities) {}
    private static final ClassValue<Fields> FIELDS = new ClassValue<>() {
        @Override protected Fields computeValue(Class<?> type) {
            try {
                Field palettes = type.getDeclaredField("palettes");
                Field entities = type.getDeclaredField("entityInfoList");
                palettes.setAccessible(true); entities.setAccessible(true);
                return new Fields(palettes, entities);
            } catch (ReflectiveOperationException failure) {
                throw new IllegalStateException("Unsupported native station template fields", failure);
            }
        }
    };

    public StationTemplateSnapshot {
        if (!validSize(size) || allBlocks == null || allBlocks.isEmpty() || allBlocks.size() > MAX_BLOCKS)
            throw new IllegalArgumentException("Unsupported station template bounds");
        size = new BlockPos(size.getX(), size.getY(), size.getZ());
        Map<BlockPos, BlockState> copied = new LinkedHashMap<>();
        boolean hasSolid = false;
        for (var entry : allBlocks.entrySet()) {
            BlockPos position = entry.getKey(); BlockState state = entry.getValue();
            if (!inside(position, size) || state == null)
                throw new IllegalArgumentException("Unsupported station template cell");
            BlockPos immutable = new BlockPos(position.getX(), position.getY(), position.getZ());
            if (copied.putIfAbsent(immutable, state) != null)
                throw new IllegalArgumentException("Duplicate station template cell");
            hasSolid |= !state.isAir();
        }
        if (!hasSolid) throw new IllegalArgumentException("Station template has no solid blocks");
        allBlocks = Map.copyOf(copied);
    }

    private static boolean validSize(Vec3i size) {
        return size != null && size.getX() > 0 && size.getX() <= MAX_AXIS
                && size.getY() > 0 && size.getY() <= MAX_AXIS
                && size.getZ() > 0 && size.getZ() <= MAX_AXIS
                && (long)size.getX() * size.getY() * size.getZ() <= MAX_VOLUME;
    }

    private static boolean inside(BlockPos position, Vec3i size) {
        return position != null && position.getX() >= 0 && position.getX() < size.getX()
                && position.getY() >= 0 && position.getY() < size.getY()
                && position.getZ() >= 0 && position.getZ() < size.getZ();
    }

    /**
     * Reads the actual MC1.21.1 fields without calling template.save or another codec.
     * Unknown subclasses, multiple palettes, entities, non-null block NBT, malformed
     * coordinates and oversized definitions return null without changing the template.
     */
    public static StationTemplateSnapshot read(StructureTemplate template) {
        if (template == null || template.getClass() != StructureTemplate.class) return null;
        try {
            Vec3i dimensions = template.getSize();
            if (!validSize(dimensions)) return null;
            BlockPos size = new BlockPos(dimensions.getX(), dimensions.getY(), dimensions.getZ());
            Fields fields = FIELDS.get(template.getClass());
            Object rawPalettes = fields.palettes().get(template), rawEntities = fields.entities().get(template);
            if (!(rawPalettes instanceof List<?> palettes) || palettes.size() != 1
                    || !(rawEntities instanceof List<?> entities) || !entities.isEmpty()
                    || !(palettes.getFirst() instanceof StructureTemplate.Palette palette)) return null;
            List<StructureTemplate.StructureBlockInfo> cells = palette.blocks();
            int count = cells.size();
            if (count == 0 || count > MAX_BLOCKS) return null;
            Map<BlockPos, BlockState> blocks = new LinkedHashMap<>();
            for (int index = 0; index < count; index++) {
                StructureTemplate.StructureBlockInfo cell = cells.get(index);
                if (cell == null || cell.nbt() != null || !inside(cell.pos(), size) || cell.state() == null) return null;
                BlockPos position = new BlockPos(cell.pos().getX(), cell.pos().getY(), cell.pos().getZ());
                if (blocks.putIfAbsent(position, cell.state()) != null) return null;
            }
            // Detect structural replacement while reading; no snapshot adopts entity/NBT data.
            if (fields.palettes().get(template) != rawPalettes || fields.entities().get(template) != rawEntities
                    || palettes.size() != 1 || palettes.getFirst() != palette || !entities.isEmpty()
                    || cells.size() != count || !size.equals(new BlockPos(template.getSize()))) return null;
            return new StationTemplateSnapshot(size, blocks);
        } catch (ReflectiveOperationException | RuntimeException unsupported) {
            return null;
        }
    }

    /** Immutable relative positions/states that must exist after native placement. */
    public Map<BlockPos, BlockState> nonAir() {
        Map<BlockPos, BlockState> result = new LinkedHashMap<>();
        allBlocks.forEach((position, state) -> { if (!state.isAir()) result.put(position, state); });
        return Map.copyOf(result);
    }
}
