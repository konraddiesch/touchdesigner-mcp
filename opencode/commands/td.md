---
description: TouchDesigner MCP task — preflight + safe golden-loop workflow in the td agent
agent: td
---

TouchDesigner MCP task: $ARGUMENTS

Steps:
1. Load the `touchdesigner-mcp` skill.
2. Preflight: `touchdesigner_get_td_info` (detailLevel minimal), then confirm the right project is open.
3. Execute the task following the skill's golden loop: locate → read → edit → verify → persist. Ask before any delete, overwrite, or save.
4. Report what changed (node paths, parameters, verification result) and whether anything still needs to be persisted.
