---
type: guide
status: reference
tags:
  - technical
  - sync
  - git
updated: 2026-11-16
---

# GitHub Sync Guide

The vault lives at `obsidian/` in the GitHub repository. Git is the sync layer for both devices.

> [!warning] Privacy
> Keep the repository **private**. Never commit tokens or passwords. Device-specific Obsidian files are already git-ignored.

## iPhone: Working Copy (recommended)
Working Copy is an iOS git client. Its Files integration lets Obsidian read the cloned repository.

1. Install **Obsidian** and **Working Copy** from the App Store.
2. In Working Copy: **+ → Clone repository**, sign in to GitHub, pick `Minecraft-Addon-Studio`.
3. Switch to the branch that holds the vault (for example `claude/obsidian-vault-setup`, or `main` once merged).
4. In Obsidian: create a new, empty vault stored **On My iPhone** (not iCloud). Name it, for example, `Minecraft-Addon-Studio`.
5. In Working Copy, open the repository, then **⋯ → Link Repository → To Folder**, and pick the Obsidian vault folder from step 4.
6. Reopen Obsidian. The repository files appear. Your notes are in the `obsidian/` folder inside the vault. Open `obsidian/Home.md`.
7. Daily use: in Working Copy, **Pull** before editing and **Commit + Push** after.

Because Working Copy links the whole repository, the vault also shows `BP/` and `RP/`. Obsidian ignores the JSON files by default. The `.obsidian` settings folder inside `obsidian/` only applies if you open `obsidian/` itself as the vault, which is easiest on a computer.

Working Copy's push feature may need its paid upgrade. Check the app's current pricing.

## Computer: plain git
1. `git clone https://github.com/zannuredige849-lang/Minecraft-Addon-Studio.git`
2. `git checkout claude/obsidian-vault-setup` (or `main` once merged).
3. In Obsidian: **Open folder as vault** and pick the `obsidian/` folder.
4. Before editing: `git pull`. After: `git add obsidian && git commit -m "docs: ..." && git push`.

## Computer: Obsidian Git plugin (optional)
1. Obsidian → **Settings → Community plugins → Turn on community plugins**.
2. **Browse**, search **Git** (by Vinzent / Denis Olehov), **Install**, **Enable**.
3. The vault is a subfolder of the repository. The plugin finds the repository above it. If it does not, set **Settings → Git → Custom base path** so it points at the repository root.
4. Use the command palette: **Git: Pull**, **Git: Commit-and-sync**. Optionally turn on auto-pull on startup and auto commit-and-sync every few minutes.

The plugin also has a mobile mode, but it is slower and less reliable on large repositories. Working Copy is more dependable on iPhone.

## Avoiding conflicts
- Pull before you start, push when you stop.
- Do not edit the same note on both devices before syncing.
- If a conflict happens, Working Copy and git both show the two versions. Keep the right lines, commit, push.

## Ignored files
`workspace.json`, `workspace-mobile.json`, `workspaces.json`, `.obsidian/cache`, plugin `data.json` files and `.trash/` are ignored. They hold layout and per-device settings, not notes.


---
Back to [[Home]] · [[Dashboard]]
