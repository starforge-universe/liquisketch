---
name: purge-orphan-branches
disable-model-invocation: true
description: >-
  Removes merged local branches whose remote tracking branch is gone or missing.
  Fetches and prunes remotes first, then deletes safe candidates. Use when
  purging orphan branches, cleaning up after merged PRs, or pruning stale local
  branches (e.g. "purge orphan branches", "clean up branches").
---

# Purge Orphan Branches

An **orphan branch** is a local branch (other than `main`) that is fully merged
into `main` and whose upstream is missing or marked `gone` after `git fetch
--all --prune`.

Execute the following steps.

1. **Fetch and prune remotes**
   Fetch all remotes and prune stale remote-tracking references.

2. **Identify orphan candidates**
   List local branches with `git branch -vv`. A candidate is a branch that:
   - is not `main`
   - is merged into `main` (`git branch --merged main`)
   - has no upstream, or shows `[origin/…: gone]` in `git branch -vv`

   Do **not** delete branches that are not merged into `main`, even if the
   upstream is gone. Report those to the user instead.

3. **Delete merged orphan branches**
   Delete each candidate with `git branch -d`. Use `-d` only (never `-D`)
   unless the user explicitly asks to force-delete unmerged branches.

4. **Summarize**
   Report which branches were deleted and which were skipped (with reason).

Run git commands outside the sandbox (see `.cursor/rules/git-guidelines.mdc`).
