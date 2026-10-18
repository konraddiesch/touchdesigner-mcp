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

## Runtime wiring (one directory, no extract copy)

TouchDesigner loads the component `/mcp_webserver_base` with `externaltox` =
`/Users/konraddiesch/TouchDesigner/td-dc-visuals/../touchdesigner-mcp/mcp_webserver_base.tox`,
and `td/import_modules.py` derives the module path from it
(`os.path.dirname(externaltox) + "/modules"`). `~/TouchDesigner/touchdesigner-mcp` is
therefore a **symlink** to this repository's `td/` — the checked-out source *is* the
running server, with no second copy to keep in sync. The stored path is unchanged, so no
TD re-import or `.toe` save was needed for the swap.

```
~/TouchDesigner/touchdesigner-mcp -> ~/Code/touchdesigner-mcp/td
```

Two consequences:

- Editing a module here changes what a **fresh** import loads, but a running TD keeps the
  already-imported modules in `sys.modules` — re-import Python (or restart TD) to pick the
  change up, exactly as before. Conversely, `git checkout` of another branch does not
  silently change the running server.
- Build artifacts required at runtime are gitignored and must exist locally:
  `td/modules/td_server/openapi_server/openapi/openapi.yaml` (bundled spec — copied from the
  `v2.1.0` release, or `npm run gen:openapi` with full `npm ci`) and
  `td/modules/mcp/controllers/generated_handlers.py` (`node td/genHandlers.js`, needs the
  `yaml` + `mustache` packages).
