---
name: merge-template
disable-model-invocation: true
description: >-
  Ask whether to merge the template remote, then run the full template-merge
  workflow when the user says yes. Use when the user wants to merge template,
  sync from template, update from template, or start a template merge session.
---

# Merge Template (optional)

## Step 1 — Ask the user

Use the **AskQuestion** tool before any git work.

**Question:** `Do you want to merge template/main into this repository?`

**Options:**
- `Yes` — run the template merge workflow
- `No` — do nothing

If the user picks **No**, or answers no in plain text, acknowledge and **stop**. Do not fetch, merge, or change branches.

If the user picks **Yes**, continue to Step 2.

## Step 2 — Merge template

Read and follow `.cursor/skills/template-merging/SKILL.md` in full (includes refreshing the local repository).

## Git constraints

Follow `.cursor/rules/git-guidelines.mdc`:

- Do not use GitHub CLI.
- Run git outside the sandbox so GPG signing works.
- All commits must be GPG-signed; never use `--no-gpg-sign`. If signing is not possible in the current environment, stop and give the user exact commands to run locally.

## If the user only wanted the prompt

When the user invokes this skill without having said “merge template” explicitly, still run Step 1 first. Only proceed when they answer **Yes**.
