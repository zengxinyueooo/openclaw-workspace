---
name: catpaw-skill-installer
description: Discover and install skills for CatPaw. Use when a user wants to find skills, search for capabilities, install a skill, or asks "is there a skill for X". Supports project-level and global installation.
metadata:
  short-description: Search and install skills from public sources and the CatPaw Skill Market
---

# CatPaw Skill Installer

Find and install skills from the public ecosystem and the CatPaw Skill Market.

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where a skill likely exists
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is specialized
- Wants tools, templates, or workflows
- Wants to install a skill from a repo, URL, or the CatPaw Skill Market
- Mentions they want help in a specific domain (design, testing, deployment, etc.)

## What to Run

- **Search skills** when the user asks what exists, wants a skill for a task, or invokes this skill without specifics
- **Install skills** when the user provides a skill name, repo path, URL, or market ID

## Communication

### When Searching

> **Tip:** Use short, single-word keywords for best search results (e.g., "ppt" instead of "powerpoint presentation maker").

Run (example for macOS ARM64):

```bash
scripts/bin/find-skills-darwin-arm64 "<query>" --text
```

If results are found, respond with a **concise table** (only Name, Source, Description):

```
I found the following skills related to "<query>":

| # | Name               | Source       | Description          |
|---|--------------------|--------------|----------------------|
| 1 | canvas-design      | [美团 Skill 市场](https://friday.sankuai.com/mcp/skills-market) | Design canvas skills |
| 2 | react-best-practices| [skills.sh](https://skills.sh) | React coding patterns|

---

❗ Please tell me:
1. **Skill number(s) or name(s)** to install
2. **Installation scope:** Project (default, `.catpaw/skills`) or Global (`~/.catpaw/skills`)

> 💡 Not satisfied? Try a more specific keyword, browse [美团 Skill 市场](https://friday.sankuai.com/mcp/skills-market) / [skills.sh](https://skills.sh), or provide a GitHub repo / local Skill path!
```

**Important:**
- Only show the "💡 Not satisfied?" tip on the **first** search in a conversation. Omit it on subsequent searches or when the user is doing consecutive installs.
- **If AskQuestion tool is available, use it to ask the user**; otherwise display the text

### When No Skills Are Found

1. Acknowledge no matches
2. Offer to help directly
3. Suggest creating a skill

Example:

```
I searched for skills related to "<query>" but didn't find any matches.

I can still help you with this task directly. Would you like me to proceed?

Alternatively, if this is something you do often, you could create your own skill using:
 npx skills init my-skill
```

### When Installing

> **Tip:** If the source is unclear (market vs public repo), run `find-skills` first to verify. Avoid direct installs when unsure.

**⚠️ CRITICAL:** Ask for installation scope and wait for the user's response. Do **not** install without confirmation.

Before installing, confirm:

- **Scope:** Project (`.catpaw/skills`) or global (`~/.catpaw/skills`)?
  - Use `-g` for global installation
  - Use `-d <path>` or `--target <path>` to install to a specific project directory
  - **Default:** If the user says "either is fine" or similar, choose project-level.
  - **Note:** `-g` and `--target` are mutually exclusive
- **Which skill(s):** If a source has multiple skills, ask which ones

After success, inform the user:

```
Successfully installed <skill-name> to <scope> scope.

Path: <installation-path>
```

## Execution Flow

### Step 1: Resolve Binary Path

Binaries live under `scripts/bin/` relative to the skill directory. Search in the following order (first found wins):

1. **Skill installation path (highest priority):** The `scripts/bin/` directory relative to where this SKILL.md file is located
2. **Project scope:** `<project>/.catpaw/skills/catpaw-skill-installer/scripts/bin/`
3. **Global scope:** `~/.catpaw/skills/catpaw-skill-installer/scripts/bin/`

> **Note:** If this skill is read from a custom path (e.g., copied or symlinked), use the binary from that same path first.

### Step 2: Execute Binary

Choose the correct binary based on the current system:

| Platform | find-skills Binary | install-skills Binary |
|----------|-------------------|----------------------|
| macOS ARM64 (M1/M2/M3/M4, default) | `find-skills-darwin-arm64` | `install-skills-darwin-arm64` |
| macOS x64 (Intel) | `find-skills-darwin-amd64` | `install-skills-darwin-amd64` |
| Linux x64 (default) | `find-skills-linux-amd64` | `install-skills-linux-amd64` |
| Linux ARM64 | `find-skills-linux-arm64` | `install-skills-linux-arm64` |

Run with an absolute path:

```bash
/path/to/catpaw-skill-installer/scripts/bin/find-skills-darwin-arm64 "<query>" --text
```

## Scripts

### `find-skills` — Search

Searches both the public skills API (https://skills.sh) and the CatPaw Skill Market by default. JSON output includes `id` and `origin` for correct installs.

Replace `<binary>` with the platform-specific binary (e.g., `find-skills-darwin-arm64` for macOS ARM64):

```bash
# Text output (recommended for display)
scripts/bin/<binary> "<query>" --text

# JSON output (default)
scripts/bin/<binary> "<query>"

# Limit results
scripts/bin/<binary> "<query>" --limit 5

# Market or public only
scripts/bin/<binary> "<query>" --market-only
scripts/bin/<binary> "<query>" --public-only
```

### `install-skills` — Install

Replace `<binary>` with the platform-specific binary (e.g., `install-skills-darwin-arm64` for macOS ARM64):

```bash
# Project scope (requires --target)
scripts/bin/<binary> -d /path/to/project owner/repo@skill-name
scripts/bin/<binary> --target /path/to/project owner/repo@skill-name

# Global scope
scripts/bin/<binary> -g owner/repo@skill-name

# Full GitHub URL
scripts/bin/<binary> https://github.com/owner/repo/tree/main/skills/skill-name

# Specific skill(s) from a repo
scripts/bin/<binary> owner/repo --skill skill-name

# CatPaw Skill Market
scripts/bin/<binary> market:14

# Force source mode
scripts/bin/<binary> --source market market:14
scripts/bin/<binary> --source public owner/repo@skill-name

# JSON result
scripts/bin/<binary> owner/repo@skill-name --json
```

## Supported Sources

| Format                                             | Description                       |
| -------------------------------------------------- | --------------------------------- |
| `owner/repo@skill-name`                            | GitHub shorthand with skill name  |
| `owner/repo`                                       | GitHub repo (discovers all skills)|
| `https://github.com/owner/repo/tree/ref/path`      | Full GitHub URL with path         |
| `https://gitlab.com/owner/repo/-/tree/ref/path`    | GitLab URL                        |
| `https://example.com/path/to/SKILL.md`             | Direct SKILL.md URL               |
| `./local/path`                                     | Local directory or file path      |
| `https://example.com` (with well-known endpoint)   | Well-known skills discovery       |
| `market:<id>`                                      | CatPaw Skill Market download      |

## Behavior and Options

- **Project scope:** `-d/--target <path>` to `<path>/.catpaw/skills` (required for project installation)
- **Global scope:** `-g/--global` to `~/.catpaw/skills`
- **Mutual exclusion:** `-g` and `-d/--target` cannot be used together
- **Note:** Either `-g` or `-d/--target` must be specified
- **Existing skills:** Abort if destination already exists
- **Error handling:** Any error stops execution with non-zero exit code
- **Private repos:** Use existing git creds or `GITHUB_TOKEN`/`GH_TOKEN`
- **Market path:** `<scope>/.catpaw/skills/skills-market/<skill-name>`
- **Source mode:** `--source auto|market|public`

## Common Search Categories

| Category        | Example Queries                          |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing         | testing, jest, playwright, e2e           |
| DevOps          | deploy, docker, kubernetes, ci-cd        |
| Documentation   | docs, readme, changelog, api-docs        |
| Code Quality    | review, lint, refactor, best-practices   |
| Design          | ui, ux, design-system, accessibility     |
| Productivity    | workflow, automation, git                |
