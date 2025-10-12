# ValueVerse GitHub Actions Workflows

This directory contains all the GitHub Actions workflows for the ValueVerse platform. These workflows automate our CI/CD pipeline, security scanning, and project management tasks.

## Workflow Overview

| Workflow | File | Trigger | Description |
|---|---|---|---|
| **Continuous Integration** | `ci.yml` | `push`, `pull_request` | Runs linting, formatting, and tests for both frontend and backend on every push and pull request. |
| **Security Scan** | `security.yml` | `push`, `pull_request`, `schedule` | Performs static analysis (CodeQL), dependency scanning (Trivy), and container image scanning (Trivy) to identify security vulnerabilities. |
| **Continuous Deployment** | `cd.yml` | `push` to `main` | Deploys the application to the production environment on every push to the `main` branch. |
| **Issue Management** | `issue-management.yml` | `issues` | Automatically labels new issues based on their content and assigns them to the project board. |

## Getting Started

These workflows are designed to run automatically based on the triggers defined in each file. No manual intervention is required.

### Secrets

The `cd.yml` workflow requires the following secrets to be configured in your GitHub repository settings:

- `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.

### Labeler Configuration

The `issue-management.yml` workflow uses the `.github/labeler.yml` file to determine which labels to apply to new issues. You can customize this file to add or change the labeling rules.

## Best Practices

- **Keep workflows modular:** Each workflow should have a single, well-defined purpose.
- **Use official actions:** Whenever possible, use official actions from GitHub and trusted vendors.
- **Pin action versions:** Pin actions to a specific version to avoid unexpected changes.
- **Use environments:** Use GitHub environments to protect your production environment and manage secrets.
- **Monitor workflow runs:** Regularly check the Actions tab in your repository to ensure workflows are running successfully.

