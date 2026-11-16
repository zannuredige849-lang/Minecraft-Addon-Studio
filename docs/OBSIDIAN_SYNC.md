# Obsidian knowledge base: sync options and decision

Status: **decision recorded, nothing installed.** Each option below must be tested on your iPhone before you rely on it.

## Constraints
- One repository only: `zannuredige849-lang/Minecraft-Addon-Studio`. No second repo.
- The vault lives in the nested folder `knowledge/`.
- No secrets in repo files. Tokens live only on the device that needs them.
- No untested plugins installed. No paid services (Obsidian Sync is paid, so it is not used).
- Existing code is not moved or deleted.

## What was checked
1. **Nested vault layout.** The obsidian-git documentation describes putting the Git repository one level above the vault, so a vault at `knowledge/` inside the repo is the documented layout. Source: [obsidian-git Getting Started](https://publish.obsidian.md/git-doc/Getting%20Started). What is **not** confirmed: the exact behaviour of the "custom base path" setting on iOS. Search results did not settle it.
2. **Mobile reliability of obsidian-git.** The official docs say the mobile Git implementation is **very unstable** and recommend other sync services. Mobile uses isomorphic-git, so there is no SSH, memory limits apply, and rebase merges are unsupported. Source: [obsidian-git Getting Started](https://publish.obsidian.md/git-doc/Getting%20Started), and the mobile notes in the [obsidian-git forum thread](https://forum.obsidian.md/t/obsidian-git-sync-on-your-ios-without-any-extra-app/60639).
3. **GitHub authentication on mobile.** HTTPS with a fine-grained personal access token limited to this one repository, with Contents read and write. The token is stored in the plugin's device settings, not in the repo.
4. **GitHub REST alternatives.** Plugins such as Vault Sync (REST), UltiSync and Git Pad sync through the GitHub API instead of the git protocol. Their behaviour with `knowledge/` is **not verified**; treat them as candidates, not choices.

## Options

| # | Option | Nested `knowledge/` | iOS | Security | Status |
|---|---|---|---|---|---|
| A | **obsidian-git** on iPhone, vault = `knowledge/`, repo root above it | documented layout | experimental, may fail on large vaults | fine-grained PAT on device only | **recommended to test first** |
| B | **Phone as read + GitHub web editing** (no plugin): read in the GitHub app or browser, edit on a feature branch via github.com | works (it is just files) | no install | no token on phone beyond GitHub login | **fallback, always available** |
| C | **REST sync plugin** (Vault Sync (REST), Git Pad or similar) | unverified | unverified | fine-grained PAT on device | candidate, untested, not installed |
| D | Obsidian Sync (official) | works | yes | Obsidian account | rejected: paid subscription |
| E | iCloud Drive vault + manual copy to repo | works | yes | no repo token | rejected: two sources of truth, conflicts |

## Recommended architecture (no change to project structure)

```
GitHub repo (single)
├── knowledge/            ← Obsidian vault (open this folder in Obsidian)
│   ├── .obsidian/        shared settings only (per-device files git-ignored)
│   └── …notes…
├── agents/ skills/ templates/ validators/ …   ← unchanged
└── docs/OBSIDIAN_SYNC.md ← this decision
```

Flow:
1. **Claude** reads and writes `knowledge/` on a `feature/*` branch and pushes there (never `main`).
2. **You, on the iPhone**, either edit with obsidian-git (option A) or, if it fails, edit through GitHub (option B).
3. **Review** on GitHub, then merge yourself.

Rules that keep this safe:
- Commit small and often. Pull before you edit on the phone.
- Work on a feature branch on the phone, never on `main`.
- If the plugin reports a merge conflict, stop, copy your edit into a new note, and resolve on desktop or GitHub web.
- Keep the vault's `.obsidian/workspace*.json` out of git (already in `.gitignore`).

## Token handling (required)
- Create a **fine-grained** personal access token at GitHub → Settings → Developer settings → Personal access tokens. Limit it to **only** this repository, with **Contents: read and write**. Set a short expiry.
- Paste it only into the obsidian-git (or REST plugin) settings on the phone. Never into a note, a repo file, a commit message, or a chat with Claude.
- If a token is ever pasted into the repo or chat by mistake, revoke it immediately in GitHub settings and create a new one. Then tell Claude so the secret scan can be re-run.
- `tests/knowledge.test.mjs` scans `knowledge/`, `docs/`, `CLAUDE.md` and `.mcp.json` for token-like strings. This is a backstop, not a substitute for revoking.

## Test plan before relying on option A
1. Create a throwaway branch `feature/obsidian-sync-test`.
2. On the iPhone: install Obsidian from the App Store (your account), open the repo folder as a vault, or create a vault and point obsidian-git at `knowledge/`.
3. Install obsidian-git from Community plugins. Set the repository path, the branch, and the PAT as above.
4. Edit a note, run "Commit and push". Check the commit on GitHub.
5. Pull from another device or the GitHub web view and confirm the change.
6. Record each result in `knowledge/Development Journal/`. If anything fails, record it under `knowledge/Errors & Solutions/`, switch to option B, and tell Claude.

## What is **not** verified
- The obsidian-git "custom base path" behaviour on iOS.
- Option C plugins: their support for nested folders and their stability.
- Any sync of a large vault.
