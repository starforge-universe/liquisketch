---
name: merge-template
disable-model-invocation: true
description: >-
  Merges changes from the template remote into this repository: feature branch,
  merge template/main, resolve conflicts (keep origin dependencies, use template
  version numbers), run workflow checks locally, push, and open a PR. Use when
  merging or syncing from the template remote (e.g. "merge template",
  "merge template remote").
---

# Merge Template

Canonical human-readable steps: [`.github/merge-instructions.md`](../../../.github/merge-instructions.md).

## Prerequisites

Confirm the `template` remote exists (`git remote get-url template`). If missing, stop and point the user to the **Add Template Remote** section in `README.md`.

Read and follow `.cursor/skills/update-local-repository/SKILL.md` first.

Execute the following steps.

1. **Create a feature branch for the template update**
   Create a new branch for the template update, called `feature/template-update`.

2. **Merge changes from the template remote's main branch**
   - Merge changes from the template remote's main branch into the current branch.

   - Resolve merge conflicts according to the following aspects.
      - You must keep dependencies of origin but version numbers must be taken from the template.
      - Ask for help in all other cases to resolve merge conflicts.
      - Use `git add` command to add the changed files.
   - Read `./.github/workflows/__call__checks.yaml` and run equivalent local validation for this project. If the workflow only defines CI steps with no local equivalent yet, note that and skip until project checks exist.

3. **Push the feature branch and open a pull request**
   Push the changes to the remote repository and open a pull request.

   Do not use GitHub CLI. Provide the user with the GitHub PR creation URL after push.

4. **Switch back to main and clean up the feature branch locally**
   Switch back to the main branch and force-delete the local feature branch (`git branch -D feature/template-update`). The branch is not merged into `main` yet; the remote branch remains for the open PR.

## Git constraints

Run git commands outside the sandbox (see `.cursor/rules/git-guidelines.mdc`). All commits (including merge commits) must be GPG-signed; never use `--no-gpg-sign`. If signing is not possible in the current environment, stop and give the user exact commands to run locally.
