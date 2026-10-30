package ua.aia2.guard.mixin;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.GuardedStationTemplate;
import ua.aia2.guard.StationConstructionAccess;
@Mixin(StructureTemplate.class)
public abstract class StationTemplateMixin implements GuardedStationTemplate {
 @Inject(method="placeInWorld(Lnet/minecraft/world/level/ServerLevelAccessor;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructurePlaceSettings;Lnet/minecraft/util/RandomSource;I)Z",at=@At("HEAD"),require=1)
 private void aia2$beforeStation(ServerLevelAccessor l,BlockPos o,BlockPos p,StructurePlaceSettings s,RandomSource r,int f,CallbackInfoReturnable<Boolean> c){StationConstructionAccess.beforePlacement((StructureTemplate)(Object)this,l,o,p,s,f);}
 @Redirect(method="placeInWorld(Lnet/minecraft/world/level/ServerLevelAccessor;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructurePlaceSettings;Lnet/minecraft/util/RandomSource;I)Z",at=@At(value="INVOKE",target="Lnet/minecraft/world/level/ServerLevelAccessor;setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;I)Z",ordinal=1),require=1,allow=1)
 private boolean aia2$primaryStationWrite(ServerLevelAccessor l,BlockPos p,BlockState s,int f){return StationConstructionAccess.writePrimary(l,p,s,f);}
 @Inject(method="placeInWorld(Lnet/minecraft/world/level/ServerLevelAccessor;Lnet/minecraft/core/BlockPos;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/levelgen/structure/templatesystem/StructurePlaceSettings;Lnet/minecraft/util/RandomSource;I)Z",at=@At("RETURN"),require=1)
 private void aia2$afterStation(ServerLevelAccessor l,BlockPos o,BlockPos p,StructurePlaceSettings s,RandomSource r,int f,CallbackInfoReturnable<Boolean> c){StationConstructionAccess.afterPlacement((StructureTemplate)(Object)this,Boolean.TRUE.equals(c.getReturnValue()));}
}
