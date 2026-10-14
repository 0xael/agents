# Agents

A collection of AI agents, skills, and workflows for Claude Code.

## Structure

```
agents/
├── prompts/         # Agent system prompts
├── skills/          # Reusable skills (.md + scripts)
├── workflows/       # Multi-agent workflow scripts (.js)
└── tools/           # Custom MCP tools and integrations
```

## Agents

| Agent | Description |
|-------|-------------|
| [k8s-mentor](prompts/k8s-mentor.md) | Kubernetes mentor — explains concepts, debugs cluster issues, cites official docs. Covers Flux CD, Crossplane, Helm, Gardener. |
| [corporate-email-drafter](prompts/corporate-email-drafter.md) | Drafts professional corporate emails — escalations, status updates, pushback, follow-ups — calibrated to audience and stakes. |
| [explain-code](prompts/explain-code.md) | Explains code with visual ASCII diagrams, analogies, and step-by-step walkthroughs. |

## Skills

| Skill | Description |
|-------|-------------|
| [code-review-ts](skills/code-review-ts/) | Deep code review for TypeScript and JavaScript — security, correctness, performance, maintainability. |
| [duplicate-finder](skills/duplicate-finder/) | Find and safely remove duplicate files in any folder using SHA-256 content hashing. |
| [frontend-design](skills/frontend-design/) | Create distinctive, production-grade frontend interfaces with high design quality. |
| [move-latest-community-recording](skills/move-latest-community-recording/) | Transfer Teams meeting recordings from OneDrive to SharePoint via Microsoft Graph API. |
| [print-ali](skills/print-ali/) | Print the name ALI with stars. |
| [skill-creator](skills/skill-creator/) | Meta-skill for creating, testing, and iteratively improving other skills. |
| [text-style-engineer](skills/text-style-engineer/) | Writing style guide for technical audiences — cuts prose to ~50%, plain English, precise terms. |

## Usage

Each agent/skill includes its own SKILL.md or prompt file with setup and usage instructions.
