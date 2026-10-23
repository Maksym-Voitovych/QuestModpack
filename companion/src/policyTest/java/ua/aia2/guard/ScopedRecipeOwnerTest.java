package ua.aia2.guard;

/** Exercises exception cleanup, nested scopes and separation between native tick threads. */
public final class ScopedRecipeOwnerTest {
    private static int assertions;
    private static void expect(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] arguments) throws Exception {
        var scope = new ScopedRecipeOwner<String>();
        expect(scope.current() == null, "No ambient owner");
        String result = scope.call("team-a", () -> {
            expect("team-a".equals(scope.current()), "Outer owner visible");
            String nested = scope.call("team-b", () -> {
                expect("team-b".equals(scope.current()), "Nested scope replaces owner");
                return "nested";
            });
            expect("nested".equals(nested), "Native return value retained");
            expect("team-a".equals(scope.current()), "Nested scope restores parent");
            try {
                scope.call("team-c", () -> { throw new IllegalStateException("native failure"); });
                throw new AssertionError("Native exception must escape scope");
            } catch (IllegalStateException expected) {
                expect("team-a".equals(scope.current()), "Exception restores parent");
            }
            final Throwable[] failure = {null};
            Thread other = new Thread(() -> {
                try {
                    expect(scope.current() == null, "Entity and block tick thread scopes do not leak");
                    scope.call("thread-b", () -> {
                        expect("thread-b".equals(scope.current()), "Other thread owns its operation");
                        return null;
                    });
                    expect(scope.current() == null, "Other thread cleaned");
                } catch (Throwable error) { failure[0] = error; }
            });
            other.start();
            try { other.join(); } catch (InterruptedException error) { throw new AssertionError(error); }
            if (failure[0] != null) throw new AssertionError(failure[0]);
            expect("team-a".equals(scope.current()), "Main owner unaffected by parallel operation");
            return "done";
        });
        expect("done".equals(result), "Operation result retained");
        expect(scope.current() == null, "Finished native operation clears owner");
        try {
            scope.call("broken", () -> { throw new IllegalArgumentException("outer"); });
            throw new AssertionError("Native exception must escape");
        } catch (IllegalArgumentException expected) { expect(scope.current() == null, "Outermost failure clears owner"); }
        try { scope.call(null, () -> null); throw new AssertionError("Null owner accepted"); }
        catch (IllegalArgumentException expected) { expect(scope.current() == null, "Null owner is denied without scope mutation"); }
        System.out.println("ScopedRecipeOwnerTest: " + assertions + " assertions passed (pure Java; real Mekanism not launched)");
    }
}
