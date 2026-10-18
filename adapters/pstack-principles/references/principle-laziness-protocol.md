# Laziness Protocol

Bias toward deletion and the smallest change that solves the problem. Before adding abstractions, layers, or threading a signal through several interfaces, check for a direct design that preserves the required behavior.

- **Consolidate decisions.** Do not repeat the same choice in several places. Put it behind one source of truth and pass the result as a simple flag.
- **Minimize the diff.** Make the smallest change that solves the problem. Fewer lines beat "elegant" boilerplate.
