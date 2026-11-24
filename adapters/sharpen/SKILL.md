---
name: sharpen
description: "Sharpen a brief or prompt using primary evidence, expert methods, and independent verification. Preserve settled requirements and decisions the user owns."
---

Before starting, consider how a top expert would approach the task: the primary evidence they would read, the methods they would use, and an independent observation that could show the result is wrong. Identify the user's actual outcome and whether the current brief specifies too much or too little.

Improve the approach without expanding the assignment. Preserve explicit requirements, frozen baselines, and settled decisions. If changing a constraint would materially improve the outcome, explain the trade-off and leave that choice to the user; do not silently loosen it or add a new restriction.

For a standalone prompt-sharpening request, identify what an expert would add, the primary evidence, the actual methods or tools, and an independent check, then return a rewritten prompt. Have the prompt use the smallest experiment that can settle a factual design choice and ask for a recommendation supported by its result. Leave product and preference decisions with the user.

When sharpening is a step inside an authorized task, including orchestration setup, incorporate the improvements into the brief and continue the requested workflow. Keep the independent check and preserve approval gates for consequential choices. A standalone rewrite ends with the revised prompt.
