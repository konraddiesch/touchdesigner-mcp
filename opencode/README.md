# opencode harness (local, not part of the shipped plugin)

Personal [opencode](https://opencode.ai) configuration for driving a live TouchDesigner
instance through this repository's MCP server. Nothing in here is packaged for Codex or
Claude — `npm run plugin:sync` copies only `plugin/touchdesigner/skills/`, and these files
use opencode frontmatter (`mode`, `temperature`, `permission`, `agent`) that no other
client understands. The directory exists so the harness has a versioned home next to the
skill it drives.

| File | Installed as |
|---|---|
| `agents/td.md` | `~/.config/opencode/agent/td.md` — primary agent, preflight + golden loop, `ask` on delete/script |
| `commands/td.md` | `~/.config/opencode/command/td.md` — `/td <task>`, runs in the `td` agent |

## Install (symlinks, so edits here take effect immediately)

```bash
ln -sfn "$PWD/opencode/agents/td.md"   ~/.config/opencode/agent/td.md
ln -sfn "$PWD/opencode/commands/td.md" ~/.config/opencode/command/td.md
```

The `touchdesigner-mcp` skill itself is packaged content and lives in the plugin source:
`plugin/touchdesigner/skills/touchdesigner-mcp/SKILL.md`, symlinked to
`~/.config/opencode/skills/touchdesigner-mcp/SKILL.md`.

opencode reads its configuration at startup, so a new or moved file needs a restart
(the skill text itself is re-read per session).

## Runtime wiring (one directory — this clone *is* the server)

TouchDesigner loads the component `/mcp_webserver_base`, whose `externaltox` par points at
`td/mcp_webserver_base.tox` **in this clone**:

```
externaltox = /Users/konraddiesch/Code/touchdesigner-mcp/td/mcp_webserver_base.tox
```

`td/import_modules.py` derives the module path from it
(`os.path.dirname(externaltox) + "/modules"`), so this checked-out source is the running
server — there is no extract copy and no symlink to keep in sync. The old
`~/TouchDesigner/touchdesigner-mcp` (a symlink to `td/` for one afternoon) and
`touchdesigner-mcp.extract-v2.1.0` were removed on 2026-10-18, and the par value was
persisted by saving the main `.toe` with an explicit path.

Two consequences:

- Editing a module here changes what a **fresh** import loads, but a running TD keeps the
  already-imported modules in `sys.modules`. Verified re-import recipe:

  ```python
  import sys
  base = op('/mcp_webserver_base')
  for k in list(sys.modules):
      if k.split('.')[0] in ('mcp', 'utils', 'import_modules'):
          del sys.modules[k]
  base.op('import_modules').module.setup()
  import mcp
  print(mcp.__file__)   # -> <clone>/td/modules/mcp/__init__.py
  ```

  Conversely, `git checkout` of another branch does not silently change the running server
  — the switch only becomes live after that re-import.

- Build artifacts required at runtime are gitignored and must exist locally:
  `td/modules/td_server/openapi_server/openapi/openapi.yaml` (bundled spec — copied from the
  `v2.1.0` release, or `npm run gen:openapi` with full `npm ci`) and
  `td/modules/mcp/controllers/generated_handlers.py` (`node td/genHandlers.js`, needs the
  `yaml` + `mustache` packages).
