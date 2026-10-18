---
name: touchdesigner-mcp
description: Use when driving a running TouchDesigner instance through the touchdesigner MCP server — inspecting nodes, reading and setting parameters, wiring chains, checking errors, capturing TOP output, or persisting .tox/.toe files. Covers the live-session tools (touchdesigner_*) and the operator documentation tools (touchdesigner-wiki_*).
version: 0.1.0
---

# TouchDesigner MCP playbook

A general playbook for controlling a **running** TouchDesigner instance through the `touchdesigner` MCP server (WebServer DAT on port 9981 by default). The TD GUI and the agent share one live state. Nothing is persisted unless explicitly saved via script.

## Tool namespaces — never mix them

| Need | Prefix | Example |
|---|---|---|
| Live TD session (nodes, params, errors, screenshots) | `touchdesigner_*` | `touchdesigner_get_td_nodes` |
| Operator documentation | `touchdesigner-wiki_*` | `touchdesigner-wiki_get_operator` |

Some projects register additional TD-related MCP servers (e.g. `chan-tools_*` for `.chan` recordings). Check the available tool list and never mix namespaces.

If tool parameters are unclear, call `touchdesigner_describe_td_tools` — it returns a self-describing manifest of all TD tools.

## Cheatsheet

| Task | Tool | Key inputs |
|---|---|---|
| Connection check | `get_td_info` | `detailLevel: "minimal"` |
| List / find nodes | `get_td_nodes` | `parentPath`, `pattern` (name glob), `limit`, `includeProperties: false` |
| Read parameters | `get_td_node_parameters` | `nodePath`, `detailLevel: "summary"` |
| Set parameters | `update_td_node_parameters` | `nodePath`, `properties` (exact par names!) |
| Create node | `create_td_node` | `parentPath`, `nodeType` (e.g. `noiseTOP`), `nodeName` |
| Delete node | `delete_td_node` | `nodePath` — confirm with user first |
| Call Python method on a node | `exec_node_method` | `nodePath`, `method` (e.g. `save`), `args` |
| Run Python in TD | `execute_python_script` | `script` — keep short, needs user approval |
| Errors + warnings (recursive) | `get_td_node_errors` | `nodePath` (use the parent COMP) |
| Visual check | `get_top_image` | `nodePath`, `maxSize: 512` |
| Python class help | `get_td_classes`, `get_td_class_details`, `get_td_module_help` | `className` |

Node types always carry the family suffix: `noiseTOP`, `constantCHOP`, `textDAT`, `containerCOMP`, `blurTOP`. Before building with an unfamiliar operator, check `touchdesigner-wiki_get_operator`. Read-only tools are cheap — prefer one more read over one guess.

## Golden loop (every change)

1. **Locate** — `get_td_nodes` on the parent path. NEVER guess node paths or names.
2. **Read** — `get_td_node_parameters` before updating; reuse the exact parameter names returned.
3. **Edit** — one logical change at a time (`create_td_node` / `update_td_node_parameters` / `execute_python_script`).
4. **Verify** — `get_td_node_errors` on the parent COMP; `get_top_image` (`maxSize: 512`) only when the visual result matters.
5. **Persist** — only if the change should survive a TD restart (see Persistence). Ask the user first.

## Workflows

### 1. Preflight & connection troubleshooting

1. Call `get_td_info` with `detailLevel: "minimal"` (reports TD version, API version).
2. Verify the RIGHT PROJECT is open: `get_td_nodes parentPath="/project1" limit=25` (adjust the root name if different). Confirm the expected top-level COMPs are present. If it looks like a scratch/default project or the wrong file, STOP and ask the user to open the intended project BEFORE any edit.
3. On `ECONNREFUSED` → report (in the user's language) that TouchDesigner must be running with `mcp_webserver_base.tox` imported and port 9981 reachable — the component ships with each `touchdesigner-mcp` release, and a checkout of this repository keeps it at `td/mcp_webserver_base.tox`. Then stop and wait. Do NOT retry in a loop (failed checks are cached ~60s).
4. `ETIMEDOUT` → TD is busy or its UI thread is blocked (possibly a long script). Ask the user before retrying.
5. If a response appends "Update Recommended" or an API-version error: the webserver component and MCP server have different API generations. Minor mismatch → inform the user, continue. Major mismatch → stop; the user must re-download `touchdesigner-mcp-td.zip` from the touchdesigner-mcp releases and re-import `mcp_webserver_base.tox`.

### 2. Explore a network safely

1. `get_td_nodes parentPath="/project1" limit=30` — note the names, then drill down only as far as needed.
2. Filter by name: `pattern="*audio*"` (matches node names only).
3. Find by operator type with a script snippet (see Recipes).
4. Set `includeProperties: true` only for the single node being edited.

### 3. Parameter edit loop

1. `get_td_node_parameters nodePath="/project1/..." detailLevel="summary"` — note exact par names and current values.
2. `update_td_node_parameters` with only the pars you intentionally change. Pulse-type pars are not booleans — trigger them via `exec_node_method` (`method: "press"` on the par) if needed.
3. `get_td_node_errors` on the parent. 4. Screenshot if visual. 5. Persist or state clearly that the change is session-only.

### 4. Build and wire a node chain

1. Ensure the parent COMP exists (`get_td_nodes`); create with `create_td_node nodeType="containerCOMP"` if not.
2. Create each node; TD may rename duplicates (`noise1` → `noise2`) — always use the names returned by `create_td_node`.
3. Wire only after all nodes exist:

```python
op('/project1/sandbox/noise1').outputConnectors[0].connect(op('/project1/sandbox/level1'))
```

4. Lay out for readability (`nodeX`, `nodeY`), then `get_td_node_errors` on the parent, then screenshot the terminal TOP.

### 5. Load and save components (.tox)

- Load into a parent COMP (ask the user first): `exec_node_method` on the target parent, `method="loadTox"`, `args=["<abs path>.tox"]` — API: `COMP.loadTox(filepath, unwired=False, pattern=None, password=None)`.
- Save a component: `exec_node_method` `nodePath="<comp>"`, `method="save"`, `args=["<abs path>.tox"]` (`OP.save(filepath)`; TOPs save images with the same method).
- Follow the project's own naming/location conventions (check the project's `AGENTS.md` / existing files).

### 6. Project persistence (CRITICAL)

The live session is RAM. Save explicitly, with the user's confirmation:

- Main project → `.toe` **with explicit path**: `project.save('/abs/path/to/project.toe')`
  - ⚠️ `project.save()` WITHOUT a path saves as an INCREMENTING numbered file (`project.36.toe`, ...). Never do this — numbered `.toe` files are TD's auto-versioning, not the working file.
  - If the project references external `.tox` files, `project.save(path, saveExternalToxs=True)` also writes those `.tox` files. Confirm with the user which variant is wanted.
- Only the main `.toe` is typically version-controlled; numbered `.toe` files, backups and crash autosaves are usually ignored — check the project's `.gitignore`.

### 7. Error triage

- `get_td_node_errors` checks errors AND warnings, recursively. Warnings = missing files, dangling references, shader failures — treat as broken.
- Red errors on the MCP webserver component (`mcp_webserver_base`) are the user's setup domain: report, don't touch.
- After 2 failed attempts at the same fix: stop and ask the user.

## Python recipes (keep them SHORT — they block the TD UI thread)

```python
# find nodes by operator type (recursive)
[(c.name, c.path) for c in op('/project1').findChildren(type='noiseTOP')]

# wire output 0 of A into first input of B
op('/project1/sandbox/noise1').outputConnectors[0].connect(op('/project1/sandbox/level1'))

# disconnect an input
op('/project1/sandbox/level1').inputConnectors[0].disconnect()

# batch parameter set, guarded
for c in op('/project1/sandbox').children:
    if 'opacity' in c.par:
        c.par.opacity = 0.5

# tidy network layout
n = op('/project1/sandbox/noise1'); n.nodeX, n.nodeY = 0, 0

# save component as .tox / save project with explicit path
op('/project1/sandbox').save('/abs/path/component.tox')
project.save('/abs/path/project.toe')
```

## Anti-patterns (do NOT)

Especially costly with fast/compact models — follow these strictly:

- ❌ Guess node paths, names, or parameter names → read first.
- ❌ Mix tool namespaces (`touchdesigner_*` vs `touchdesigner-wiki_*` vs project-local servers).
- ❌ Dump whole networks or raw verbose JSON → `detailLevel: "summary"`, `limit`, `pattern`.
- ❌ Retry failed connections in a loop.
- ❌ Long or blocking scripts (no `time.sleep` loops, no infinite loops, no heavy file I/O).
- ❌ Delete or overwrite nodes/files without explicit user confirmation.
- ❌ Batch many blind edits → one change, verify, then the next.
