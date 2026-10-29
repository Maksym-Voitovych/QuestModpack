package fixture;

import java.lang.reflect.InvocationTargetException;
import java.util.Arrays;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.spongepowered.asm.launch.MixinBootstrap;
import org.spongepowered.asm.mixin.MixinEnvironment;
import org.spongepowered.asm.mixin.Mixins;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;

/** Real Mixin apply on compiled exact source with dependency stubs, never a client claim. */
public final class IsolatedMixinMain {
    public static void main(String[] args) throws Exception {
        boolean bad = args.length == 1 && args[0].equals("bad");
        MixinBootstrap.init();
        Mixins.addConfiguration("release-fixture.mixins.json");
        var phase = MixinEnvironment.class.getDeclaredMethod("gotoPhase", MixinEnvironment.Phase.class);
        phase.setAccessible(true); phase.invoke(null, MixinEnvironment.Phase.DEFAULT);
        var transformerType = Class.forName("org.spongepowered.asm.mixin.transformer.MixinTransformer");
        var constructor = transformerType.getDeclaredConstructor(); constructor.setAccessible(true);
        IMixinTransformer transformer = (IMixinTransformer) constructor.newInstance();
        String name = "moze_intel.projecte.gameObjs.items.TransmutationTablet";
        byte[] input;
        try (var stream = IsolatedMixinMain.class.getClassLoader().getResourceAsStream(name.replace('.', '/') + ".class")) {
            if (stream == null) throw new AssertionError("Missing exact release-source compiled fixture");
            input = stream.readAllBytes();
        }
        byte[] output;
        try { output = transformer.transformClassBytes(name, name, input); }
        catch (Throwable failure) {
            if (!bad) throw failure;
            boolean injection = false, methods = false;
            for (Throwable cause = failure; cause != null; cause = cause.getCause()) {
                injection |= cause.getClass().getName().endsWith("InvalidInjectionException");
                methods |= String.valueOf(cause.getMessage()).contains("openContainer");
            }
            if (!injection || !methods) throw new AssertionError("Wrong failure while reproducing old selector", failure);
            System.out.println("REAL_SPONGE_INVALID_INJECTION_REPRODUCED: missing release openContainer, require1 retained; modeled dependencies only");
            return;
        }
        if (bad) throw new AssertionError("Old selectors unexpectedly transformed the released class");
        if (Arrays.equals(input, output)) throw new AssertionError("Transformer silently left the target untouched");
        ClassNode node = new ClassNode(); new ClassReader(output).accept(node, 0);
        int delegates = 0, redirects = 0, uncheckedMenuCalls = 0;
        for (var method : node.methods) for (var instruction : method.instructions) {
            if (!(instruction instanceof MethodInsnNode call)) continue;
            if (call.owner.equals("ua/aia2/guard/ProjectEPassiveAccess") && call.name.equals("openTablet")) delegates++;
            if (method.name.equals("use") && call.name.contains("aia2$tabletOrigin")) redirects++;
            if (method.name.equals("use") && call.owner.equals("net/minecraft/world/entity/player/Player") && call.name.equals("openMenu")) uncheckedMenuCalls++;
        }
        if (delegates != 1 || redirects != 1 || uncheckedMenuCalls != 0)
            throw new AssertionError("Guard delegation was not installed: " + delegates + "/" + redirects + "/" + uncheckedMenuCalls);
        System.out.println("REAL_SPONGE_FIXED_REDIRECT_APPLIED: exact use descriptor, one guarded menu call, no original unchecked use openMenu; modeled dependencies only");
    }
}
