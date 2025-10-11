### Step 1: Plan, Repository, Governance & Project Scaffold

#### Objective

This initial step is the foundation for the entire project. The goal is to establish a robust structure, encompassing project planning, repository initialization, and the configuration of governance tools. This ensures consistency, code quality, and long-term maintainability from the very beginning.

---

### 1. Project Planning

A detailed plan helps to clearly define the scope, objectives, and required steps for execution.

- **Tooling:** I use Notion for drafting and tracking the project plan. A template is available for duplication [here](https://tmv-project-plan.notion.site/project-plan-template).

- **Key Sections to Complete:**
  - **Project Description:** A high-level overview of the project's purpose.
  - **Project Architecture:** An initial sketch of the system architecture.
  - **Naming Convention:** A critical guide for consistency across all resources.
  - **Main Steps & Step Breakdown:** A list of major project phases and their corresponding subtasks for progress tracking.

---

### 2. Naming Conventions

Consistent naming is crucial for clarity and automation. The following conventions are used throughout this project:

| Resource                   | Convention                                         | Example                            |
| :------------------------- | :------------------------------------------------- | :--------------------------------- |
| **Project Name**           | `hackernews`                                       | `hackernews`                       |
| **Terraform State Bucket** | `hn-pipeline-<env>-tfstate`                        | `hn-pipeline-dev-tfstate`          |
| **GCS Buckets**            | `hn-<env>-<layer>-bucket`                          | `hn-dev-bronze-bucket`             |
| **BigQuery Datasets**      | `hn_<layer>_<env>`                                 | `hn_silver_dev`                    |
| **BigQuery Tables**        | `snake_case` with layer prefixes                   | `stg_...`, `dim_...`, `fct_...`    |
| **dbt Models**             | Files in `models/` with layer prefixes             | `models/staging/stg_...`           |
| **Git Branches**           | `main`, `dev`, `feature/<desc>`, `bugfix/<ticket>` | `feature/add-dbt-snapshots`        |
| **Commit Messages**        | Conventional Commits                               | `feat:`, `fix:`, `docs:`, `chore:` |
| **Prefect Credentials**    | `gcp-creds`                                        | `gcp-creds`                        |

---

### 3. Repository & Environment Setup

These are the technical steps to initialize the project on your local machine.

1.  **Create GitHub Repo & Local Project:**

    - Create a new repository on GitHub.
    - Clone the repository to your local machine and navigate into the project directory.

2.  **Create a Virtual Environment:**
    Always use a virtual environment to isolate project dependencies.

    ```bash
    # Create a virtual environment named 'venv'
    python -m venv venv

    # Activate the virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

3.  **Create `requirements.txt`:**
    Even if no packages are installed yet, create an empty file to track dependencies.
    ```bash
    pip freeze > requirements.txt
    ```

---

### 4. Pre-commit Hooks Setup

#### What is Pre-commit?

`pre-commit` is a framework for managing and maintaining multi-language pre-commit hooks. These hooks run checks on your code **before** you commit, helping to ensure code quality and consistency.

**Benefits:**

- **Enforce Code Quality:** Automatically catch simple issues, syntax errors, and formatting problems.
- **Maintain Consistency:** Ensure all code in the project adheres to the same formatting style.
- **Enhance Security:** Automatically scan for secrets (passwords, API keys) that might be accidentally committed.

#### Implementation Guide

For full details, refer to the official documentation: [https://pre-commit.com/](https://pre-commit.com/)

1.  **Installation:**

    ```bash
    pip install pre-commit
    ```

2.  **Create Configuration File:**
    Create a file named `.pre-commit-config.yaml` in the project root with the following content. This defines which checks will run.

    ```yaml
    # .pre-commit-config.yaml
    default_language_version:
      python: python3.9

    repos:
      # 1. Basic File Hygiene
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.6.0 # Always use the latest stable version
        hooks:
          - id: check-added-large-files
          - id: check-json
          - id: check-merge-conflict
          - id: check-yaml
          - id: end-of-file-fixer
          - id: trailing-whitespace

      # 2. Python Code Formatter (Black)
      - repo: https://github.com/psf/black
        rev: 24.4.2
        hooks:
          - id: black

      # 3. Python Linter (Ruff)
      - repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.4.4
        hooks:
          - id: ruff
            args: [--fix] # Automatically fix what can be fixed

      # 4. Secret Detection (Gitleaks)
      - repo: https://github.com/gitleaks/gitleaks
        rev: v8.18.2
        hooks:
          - id: gitleaks
    ```

3.  **Install the Git Hooks:**
    This command installs the pre-commit script into your repository's `.git/hooks` directory. It needs to be run once per project.

    ```bash
    pre-commit install
    ```

4.  **Initial Run & Updates:**
    - To run the hooks against all files for the first time:
      ```bash
      pre-commit run --all-files
      ```
    - To automatically update the hook versions (`rev`) in your config file:
      ```bash
      pre-commit autoupdate
      ```

---

### 5. Git Workflow Setup

1.  **Create a `dev` Branch:**
    All feature development will branch off from `dev`. The `main` branch is reserved for stable, production-ready releases.

    ```bash
    # From the 'main' branch, create a new branch named 'dev' and switch to it
    git checkout -b dev
    ```

2.  **Configure Branch Protection for `main`:**
    - **Purpose:** Branch protection rules on GitHub safeguard your most important branches. They prevent direct pushes and enforce a review process via Pull Requests.
    - **Configuration (on GitHub UI):**
      - Go to your repository -> Settings -> Branches.
      - Add a "branch protection rule" for `main`.
      - Enable key options, such as:
        - Require a pull request before merging.
        - Require approvals (set to at least 1).
    - For more details, refer to the official GitHub documentation: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

---

[**> Next Step: Step 2 - GCP Infrastructure with Terraform**](./02-gcp-infrastructure.md)
