package fixture;

import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.launch.platform.container.ContainerHandleVirtual;
import org.spongepowered.asm.launch.platform.container.IContainerHandle;
import org.spongepowered.asm.service.*;

/** Test-only host for the real Sponge transformer; no Minecraft/NeoForge boot. */
public final class IsolatedMixinService extends MixinServiceAbstract implements IClassProvider,
        IClassBytecodeProvider, ITransformerProvider, IClassTracker, IMixinAuditTrail {
    public String getName() { return "AIA2 isolated release-source fixture"; }
    public boolean isValid() { return true; }
    public IClassProvider getClassProvider() { return this; }
    public IClassBytecodeProvider getBytecodeProvider() { return this; }
    public ITransformerProvider getTransformerProvider() { return this; }
    public IClassTracker getClassTracker() { return this; }
    public IMixinAuditTrail getAuditTrail() { return this; }
    public Collection<String> getPlatformAgents() { return List.of(); }
    public IContainerHandle getPrimaryContainer() { return new ContainerHandleVirtual("fixture"); }
    public InputStream getResourceAsStream(String name) { return getClass().getClassLoader().getResourceAsStream(name); }
    public URL[] getClassPath() { return new URL[0]; }
    public Class<?> findClass(String name) throws ClassNotFoundException { return findClass(name, false); }
    public Class<?> findClass(String name, boolean initialize) throws ClassNotFoundException { return Class.forName(name, initialize, getClass().getClassLoader()); }
    public Class<?> findAgentClass(String name, boolean initialize) throws ClassNotFoundException { return findClass(name, initialize); }
    public ClassNode getClassNode(String name) throws ClassNotFoundException, IOException { return getClassNode(name, false, 0); }
    public ClassNode getClassNode(String name, boolean transformers) throws ClassNotFoundException, IOException { return getClassNode(name, transformers, 0); }
    public ClassNode getClassNode(String name, boolean transformers, int flags) throws ClassNotFoundException, IOException {
        try (InputStream stream = getResourceAsStream(name.replace('.', '/') + ".class")) {
            if (stream == null) throw new ClassNotFoundException(name);
            ClassNode result = new ClassNode(); new ClassReader(stream).accept(result, flags); return result;
        }
    }
    public Collection<ITransformer> getTransformers() { return List.of(); }
    public Collection<ITransformer> getDelegatedTransformers() { return List.of(); }
    public void addTransformerExclusion(String name) {}
    public void registerInvalidClass(String name) {}
    public boolean isClassLoaded(String name) { return false; }
    public String getClassRestrictions(String name) { return ""; }
    public void onApply(String target, String mixin) {}
    public void onPostProcess(String target) {}
    public void onGenerate(String target, String generator) {}

    public static final class Properties implements IGlobalPropertyService {
        private record Key(String name) implements IPropertyKey {}
        private final Map<IPropertyKey, Object> values = new HashMap<>();
        public IPropertyKey resolveKey(String name) { return new Key(name); }
        @SuppressWarnings("unchecked") public <T> T getProperty(IPropertyKey key) { return (T) values.get(key); }
        public void setProperty(IPropertyKey key, Object value) { values.put(key, value); }
        @SuppressWarnings("unchecked") public <T> T getProperty(IPropertyKey key, T fallback) { return (T) values.getOrDefault(key, fallback); }
        public String getPropertyString(IPropertyKey key, String fallback) { return String.valueOf(values.getOrDefault(key, fallback)); }
    }
}
