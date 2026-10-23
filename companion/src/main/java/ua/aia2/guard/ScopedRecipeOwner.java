package ua.aia2.guard;

import java.util.function.Supplier;

/** A narrow operation scope, restored even when an underlying native recipe throws. */
public final class ScopedRecipeOwner<T> {
    private final ThreadLocal<T> current = new ThreadLocal<>();

    public T current() { return current.get(); }

    public <R> R call(T owner, Supplier<R> action) {
        if (owner == null) throw new IllegalArgumentException("Recipe owner must not be null");
        T previous = current.get();
        current.set(owner);
        try { return action.get(); }
        finally {
            if (previous == null) current.remove(); else current.set(previous);
        }
    }

    public void clear() { current.remove(); }
}
