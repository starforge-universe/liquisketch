---
name: update-local-repository
disable-model-invocation: true
description: >-
  Updates the local repository before template merges or other sync tasks:
  switch to main, pull latest, and fetch all remotes. Use when refreshing
  main, syncing with origin, or as the first step before merge-template
  (e.g. "refresh", "pull latest", "sync remotes").
---

# Update Local Repository

Execute the following steps.

1. **Update your local main branch**
   Switch to the main branch and pull the latest changes.

2. **Fetch all remotes**
   Fetch all remotes to get the latest changes from the remote repositories.

Run git commands outside the sandbox (see `.cursor/rules/git-guidelines.mdc`).
