#!/usr/bin/env python3
"""Generate the comprehensive built-in skill tree."""

from pathlib import Path

SKILLS_ROOT = Path(__file__).parent.parent / "src" / "skilltree" / "skills" / "built-in"

SKILLS = {
    # Software Engineering
    "software-engineering/clean-code": {
        "name": "Clean Code",
        "description": "Writing readable, maintainable, and elegant code in any language.",
        "version": "1.0.0",
        "tags": ["clean-code", "readability", "maintenance", "craftsmanship"],
    },
    "software-engineering/testing": {
        "name": "Testing Strategies",
        "description": "Unit, integration, contract, and property-based testing patterns.",
        "version": "1.0.0",
        "tags": ["testing", "tdd", "quality", "pytest", "unit-tests"],
    },
    "software-engineering/architecture": {
        "name": "Software Architecture",
        "description": "Design scalable, resilient, and evolvable system architectures.",
        "version": "1.0.0",
        "tags": ["architecture", "scalability", "resilience", "systems-design"],
    },
    "software-engineering/design-patterns": {
        "name": "Design Patterns",
        "description": "Creational, structural, and behavioral patterns for robust software.",
        "version": "1.0.0",
        "tags": ["patterns", "oop", "design", "refactoring"],
    },
    # Languages
    "languages/python": {
        "name": "Python Mastery",
        "description": "Advanced Python: idioms, asyncio, typing, packaging, and performance.",
        "version": "2.0.0",
        "tags": ["python", "async", "typing", "packaging", "performance"],
    },
    "languages/rust": {
        "name": "Rust Systems",
        "description": "Memory-safe systems programming with Rust.",
        "version": "1.0.0",
        "tags": ["rust", "systems", "memory-safety", "wasm"],
    },
    "languages/go": {
        "name": "Go Backend",
        "description": "Concurrent backend services with Go.",
        "version": "1.0.0",
        "tags": ["go", "golang", "backend", "concurrency", "microservices"],
    },
    "languages/typescript": {
        "name": "TypeScript Full-Stack",
        "description": "Type-safe frontend and backend development with TypeScript.",
        "version": "1.0.0",
        "tags": ["typescript", "javascript", "frontend", "backend", "types"],
    },
    # DevOps
    "devops/docker": {
        "name": "Docker Expert",
        "description": "Advanced Docker containerization, optimization, and orchestration.",
        "version": "2.1.0",
        "tags": ["docker", "container", "orchestration", "devops", "security"],
    },
    "devops/kubernetes": {
        "name": "Kubernetes Mastery",
        "description": "Production-grade Kubernetes deployment, operations, and troubleshooting.",
        "version": "3.0.0",
        "tags": ["kubernetes", "k8s", "devops", "orchestration", "production"],
    },
    "devops/ci-cd": {
        "name": "CI/CD Pipelines",
        "description": "Build, test, and deploy automation with GitHub Actions, GitLab CI, and ArgoCD.",
        "version": "1.0.0",
        "tags": ["ci-cd", "github-actions", "gitlab-ci", "argocd", "automation"],
    },
    "devops/observability": {
        "name": "Observability",
        "description": "Logging, metrics, tracing, and alerting for production systems.",
        "version": "1.0.0",
        "tags": ["observability", "monitoring", "tracing", "prometheus", "grafana"],
    },
    "devops/terraform": {
        "name": "Infrastructure as Code",
        "description": "Declarative infrastructure with Terraform, Pulumi, and CloudFormation.",
        "version": "1.0.0",
        "tags": ["terraform", "iac", "pulumi", "cloudformation", "devops"],
    },
    # Cloud
    "cloud/aws": {
        "name": "AWS Cloud",
        "description": "Design and operate solutions on Amazon Web Services.",
        "version": "1.0.0",
        "tags": ["aws", "cloud", "ec2", "s3", "lambda", "serverless"],
    },
    "cloud/gcp": {
        "name": "Google Cloud",
        "description": "Build and run applications on Google Cloud Platform.",
        "version": "1.0.0",
        "tags": ["gcp", "google-cloud", "kubernetes", "bigquery", "serverless"],
    },
    "cloud/azure": {
        "name": "Microsoft Azure",
        "description": "Enterprise solutions on Microsoft Azure.",
        "version": "1.0.0",
        "tags": ["azure", "microsoft", "cloud", "entra", "devops"],
    },
    # Data Engineering
    "data-engineering/sql": {
        "name": "SQL Mastery",
        "description": "Advanced querying, optimization, and schema design with SQL.",
        "version": "1.0.0",
        "tags": ["sql", "database", "query-optimization", "schema-design"],
    },
    "data-engineering/etl": {
        "name": "ETL & Data Pipelines",
        "description": "Extract, transform, load patterns with Spark, dbt, and Airflow.",
        "version": "1.0.0",
        "tags": ["etl", "spark", "dbt", "airflow", "data-pipeline"],
    },
    "data-engineering/pipelines": {
        "name": "Stream Processing",
        "description": "Real-time data pipelines with Kafka, Flink, and Pulsar.",
        "version": "1.0.0",
        "tags": ["streaming", "kafka", "flink", "real-time", "event-driven"],
    },
    "data-engineering/analytics": {
        "name": "Data Analytics",
        "description": "Descriptive and diagnostic analytics with notebooks and BI tools.",
        "version": "1.0.0",
        "tags": ["analytics", "bi", "pandas", "jupyter", "visualization"],
    },
    # Security
    "security/appsec": {
        "name": "Application Security",
        "description": "Secure coding, threat modeling, and vulnerability remediation.",
        "version": "1.0.0",
        "tags": ["appsec", "security", "owasp", "threat-modeling", "sdlc"],
    },
    "security/compliance": {
        "name": "Compliance & Governance",
        "description": "SOC2, GDPR, HIPAA, and audit-ready engineering practices.",
        "version": "1.0.0",
        "tags": ["compliance", "gdpr", "soc2", "hipaa", "governance"],
    },
    "security/secrets": {
        "name": "Secrets Management",
        "description": "Vaults, key rotation, and zero-trust secret distribution.",
        "version": "1.0.0",
        "tags": ["secrets", "vault", "zero-trust", "encryption", "keys"],
    },
    # AI / ML
    "ai-ml/prompt-engineering": {
        "name": "Prompt Engineering",
        "description": "Craft effective prompts for LLMs: chaining, few-shot, and system design.",
        "version": "1.0.0",
        "tags": ["prompt-engineering", "llm", "nlu", "chain-of-thought"],
    },
    "ai-ml/rag": {
        "name": "Retrieval-Augmented Generation",
        "description": "Build RAG systems with embeddings, vector DBs, and rerankers.",
        "version": "1.0.0",
        "tags": ["rag", "vector-db", "embeddings", "search", "llm"],
    },
    "ai-ml/model-ops": {
        "name": "MLOps",
        "description": "Deploy, monitor, and govern machine learning models in production.",
        "version": "1.0.0",
        "tags": ["mlops", "model-serving", "monitoring", "governance", "ml"],
    },
    "ai-ml/fine-tuning": {
        "name": "Model Fine-Tuning",
        "description": "Fine-tune LLMs and vision models with LoRA, QLoRA, and full training.",
        "version": "1.0.0",
        "tags": ["fine-tuning", "lora", "qlora", "training", "llm"],
    },
    # Productivity
    "productivity/git": {
        "name": "Git Wizardry",
        "description": "Advanced Git: rebase, bisect, hooks, and monorepo strategies.",
        "version": "1.0.0",
        "tags": ["git", "version-control", "monorepo", "workflow"],
    },
    "productivity/shell": {
        "name": "Shell Power User",
        "description": "Bash, zsh, and POSIX scripting for automation and speed.",
        "version": "1.0.0",
        "tags": ["shell", "bash", "scripting", "automation", "cli"],
    },
    "productivity/vim": {
        "name": "Vim & Modal Editing",
        "description": "Efficient text editing with Vim motions and configuration.",
        "version": "1.0.0",
        "tags": ["vim", "neovim", "editor", "productivity", "modal"],
    },
    "productivity/note-taking": {
        "name": "Knowledge Management",
        "description": "Zettelkasten, PARA, and evergreen note-taking for developers.",
        "version": "1.0.0",
        "tags": ["notes", "zettelkasten", "para", "knowledge-management"],
    },
    # Communication
    "communication/technical-writing": {
        "name": "Technical Writing",
        "description": "Write clear docs, RFCs, ADRs, and API specifications.",
        "version": "1.0.0",
        "tags": ["writing", "docs", "rfc", "adr", "api-spec"],
    },
    "communication/documentation": {
        "name": "Documentation Engineering",
        "description": "Docs-as-code, READMEs, and developer portals.",
        "version": "1.0.0",
        "tags": ["documentation", "docs-as-code", "developer-portal", "readme"],
    },
    "communication/incident-response": {
        "name": "Incident Response",
        "description": "Runbooks, postmortems, and on-call best practices.",
        "version": "1.0.0",
        "tags": ["incident-response", "on-call", "postmortem", "sre"],
    },
    # Project Management
    "project-management/agile": {
        "name": "Agile & Lean",
        "description": "Scrum, Kanban, and lean software development practices.",
        "version": "1.0.0",
        "tags": ["agile", "scrum", "kanban", "lean", "project-management"],
    },
    "project-management/estimation": {
        "name": "Effort Estimation",
        "description": "Forecasting, story points, and probabilistic planning.",
        "version": "1.0.0",
        "tags": ["estimation", "forecasting", "planning", "story-points"],
    },
    "project-management/roadmapping": {
        "name": "Product Roadmapping",
        "description": "Build and communicate technical roadmaps.",
        "version": "1.0.0",
        "tags": ["roadmap", "strategy", "product", "planning"],
    },
    # Meta
    "code-review": {
        "name": "Code Review",
        "description": "Structured code review process and checklist for any language.",
        "version": "1.2.0",
        "tags": ["review", "quality", "process", "teamwork"],
    },
    "mcp-development": {
        "name": "MCP Development",
        "description": "Best practices for building Model Context Protocol servers and clients.",
        "version": "1.0.0",
        "tags": ["mcp", "protocol", "server", "client", "ai"],
    },
    "python-refactoring": {
        "name": "Python Refactoring",
        "description": "Patterns and techniques for refactoring Python codebases.",
        "version": "1.0.0",
        "tags": ["python", "refactoring", "patterns", "clean-code"],
    },
}


def write_skill(path: Path, meta: dict) -> None:
    path.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: {meta['name']}
description: {meta['description']}
version: {meta['version']}
tags: {meta['tags']}
dependencies: []
origin_type: embedded
metadata:
  author: skilltree
  license: MIT
---

# {meta['name']}

## Overview

{meta['description']}

## Key Practices

- Practice deliberate improvement in this domain
- Reference this skill when working on related tasks
- Combine with complementary skills for best results

## See Also

- Browse related skills via `get_skill_tree`
- Search with `search_skills` for specific topics
"""
    (path / "SKILL.md").write_text(content, encoding="utf-8")


def main() -> None:
    for rel_path, meta in SKILLS.items():
        write_skill(SKILLS_ROOT / rel_path, meta)
    print(f"Generated {len(SKILLS)} skills in {SKILLS_ROOT}")


if __name__ == "__main__":
    main()
