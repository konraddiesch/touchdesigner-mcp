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
