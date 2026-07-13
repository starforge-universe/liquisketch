# Template Merging Process

Follow these steps to merge updates from the template remote into your repository.

For the agent workflow, see `.cursor/skills/merge-template/SKILL.md`.

## Prerequisites

Confirm the `template` remote exists (`git remote get-url template`). If missing, add it per the **Add Template Remote** section in `README.md`.

1. **Update your local main branch**
   Switch to the main branch and pull the latest changes.

2. **Fetch all remotes**
   Fetch all remotes to get the latest changes from all remotes.

3. **Create a feature branch for the template update**
   Create a new branch for the template update.

4. **Merge changes from the template remote's main branch**
   - Merge changes from the template remote's main branch into the current branch.
   - Resolve merge conflicts according to the following aspects.
      - You must keep dependencies of origin but version numbers must be taken from the template.
      - Ask for help in all other cases to resolve merge conflicts.
      - Use git add command to add the changed files.
   - Read `./.github/workflows/__call__checks.yaml` and run equivalent local validation for your project.

5. **Push the feature branch and open a pull request**
   Push the changes to the remote repository and open a pull request.

6. **Switch back to main and clean up the feature branch locally**
   Switch back to the main branch and force-delete the local feature branch (`git branch -D feature/template-update`). The remote branch remains for the open PR.
