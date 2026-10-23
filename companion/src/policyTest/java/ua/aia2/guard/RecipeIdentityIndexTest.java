package ua.aia2.guard;

import java.util.IdentityHashMap;
import java.util.Map;

/** Regression suite for native recipe caches; does not load Minecraft classes. */
public final class RecipeIdentityIndexTest {
    private static int assertions;

    private static void expect(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    /** Equality must never make an unrelated native recipe inherit access. */
    private record EqualRecipe(String name) {}

    /** A recipe's equality methods can be expensive or unsafe; never invoke them. */
    private static final class NoEqualityRecipe {
        @Override public boolean equals(Object ignored) {
            throw new AssertionError("Native recipe equality was called");
        }
        @Override public int hashCode() {
            throw new AssertionError("Native recipe hashCode was called");
        }
    }

    public static void main(String[] args) {
        RecipeIdentityIndex index = new RecipeIdentityIndex();
        Object generation = new String("recipes-v1");
        Object equalGeneration = new String("recipes-v1");
        Object unknown = new Object();
        expect(index.stage(unknown) == 100, "An index that has not loaded recipes must quarantine them");
        expect(index.stage(null) == 100, "A missing native recipe must not gain default access");
        expect(!index.isGeneration(generation), "An unloaded index is not the active recipe generation");

        EqualRecipe early = new EqualRecipe("same contents");
        EqualRecipe late = new EqualRecipe("same contents");
        EqualRecipe imported = new EqualRecipe("same contents");
        expect(early.equals(late), "The fixture must exercise equal objects with different identities");
        var entries = new IdentityHashMap<Object, Integer>();
        entries.put(early, 1);
        entries.put(late, 48);
        NoEqualityRecipe custom = new NoEqualityRecipe();
        entries.put(custom, 16);
        index.replace(generation, entries);
        expect(index.isGeneration(generation), "The installed generation is recognized");
        expect(!index.isGeneration(equalGeneration), "Equal generation tokens do not replace identity checks");
        expect(index.stage(early) == 1, "The early recipe retains its own stage");
        expect(index.stage(late) == 48, "An equal late recipe must not inherit the early recipe's access");
        expect(index.stage(imported) == 100, "An equal imported recipe is quarantined until indexed explicitly");
        expect(index.stage(custom) == 16, "Native recipe lookups must not use equals or hashCode");
        expect(index.stage(unknown) == 100, "Unknown dynamically synthesized recipes remain quarantined");

        entries.put(early, 0);
        entries.put(unknown, 0);
        entries.clear();
        expect(index.stage(early) == 1, "Mutating the caller's map must not alter the installed snapshot");
        expect(index.stage(unknown) == 100, "Mutating caller data must not grant an unknown recipe access");

        Object reloadedGeneration = new Object();
        Object reloadedRecipe = new Object();
        index.replace(reloadedGeneration, Map.of(reloadedRecipe, 22));
        expect(!index.isGeneration(generation), "Reload invalidates the old generation token");
        expect(index.isGeneration(reloadedGeneration), "Reload installs the new generation token");
        expect(index.stage(early) == 100, "A stale cached recipe cannot retain its old early permission after reload");
        expect(index.stage(late) == 100, "Every stale native identity is removed on generation replacement");
        expect(index.stage(reloadedRecipe) == 22, "The reloaded native recipe gains only its specified stage");

        Object emptyGeneration = new Object();
        index.replace(emptyGeneration, Map.of());
        expect(index.isGeneration(emptyGeneration), "An empty recipe reload is still a real generation");
        expect(index.stage(reloadedRecipe) == 100, "An empty reload must not retain previously allowed recipes");
        index.replace(reloadedGeneration, Map.of(reloadedRecipe, 22));
        index.reset();
        expect(!index.isGeneration(reloadedGeneration), "A server reset invalidates the old recipe generation");
        expect(index.stage(reloadedRecipe) == 100, "A new server cannot inherit recipe permissions from an old world");
        expect(index.stage(custom) == 100, "A server reset clears custom recipe identities too");

        // The policy matrix checks the exact API now used by cached machine recipes.
        GuardPolicy policy = new GuardPolicy();
        expect(!policy.mayUseStage(-1, "team"), "Negative stage must be denied, including before readiness");
        expect(!policy.mayUseStage(Integer.MIN_VALUE, "team"), "Integer underflow cannot create an early stage");
        expect(!policy.mayUseStage(101, "team"), "Out-of-range stages must be denied");
        expect(!policy.mayUseStage(Integer.MAX_VALUE, "team"), "Integer overflow cannot create access");
        for (int stage = 0; stage <= 100; stage++) {
            expect(policy.mayUseStage(stage, null) == (stage <= 1),
                    "Before initialization only free/epoch-one recipes are available: " + stage);
        }
        policy.setRules(Map.of("aia2:test_recipe", 1));
        policy.setReady();
        for (int completed = 0; completed <= 48; completed++) {
            policy.setTeamProgress("team", completed);
            for (int stage = 0; stage <= 100; stage++) {
                boolean expected = stage <= 1 || stage <= 48 && stage <= completed + 1
                        || stage == 99 && completed == 48;
                expect(policy.mayUseStage(stage, "team") == expected,
                        "Cached recipe stage boundary: completed=" + completed + ", required=" + stage);
            }
        }
        for (String owner : new String[] {null, "", " ", "absent-team"}) {
            expect(policy.mayUseStage(1, owner), "Unowned early recipes remain intentionally available");
            expect(!policy.mayUseStage(2, owner), "Unowned staged recipes cannot inherit any team's progress");
            expect(!policy.mayUseStage(99, owner), "Unowned final-completion recipes must remain locked");
            expect(!policy.mayUseStage(100, owner), "Quarantined recipes never unlock");
        }
        policy.clear();
        expect(!policy.mayUseStage(48, "team"), "Clear immediately closes a previously unlocked cached recipe");
        expect(!policy.mayUseStage(99, "team"), "Clear immediately closes final-completion recipes");
        System.out.println("RecipeIdentityIndexTest: " + assertions
                + " assertions passed (identity, reload, quarantine, complete stage matrix; Minecraft not launched)");
    }
}
