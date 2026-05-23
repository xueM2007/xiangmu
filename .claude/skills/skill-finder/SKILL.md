---
name: "skill-finder"
description: "Help users discover, search for, and install skills. Use when the user asks what skills they have, wants to find skills for a specific task, or asks what plugins are available."
---

# Skill Finder

Help the user discover and find skills that match their needs. This skill covers three scenarios:

## 1. Showing installed skills
When the user asks "what skills do I have" or "show my skills", use `mcp__skills__list_skills` to display all installed skills in the interactive widget. You can filter by topic using the `keywords` parameter.

## 2. Searching for new skills/plugins
When the user describes a task or workflow and wants to know if there's a skill for it, use `mcp__plugins__search_plugins` with the user's intent. If relevant plugins are found, use `mcp__plugins__suggest_plugin_install` to show them.

Always search for plugins when the user:
- Says "any skills for X?" or "find me a skill for X"
- Describes a workflow and asks "is there a plugin for this?"
- Mentions a tool/platform (Jira, Salesforce, Slack, etc.) and wants related skills
- Asks "what can I install for X?"

## 3. Recommending skills for a task
When the user describes what they want to accomplish but doesn't know which skill would help:
- First understand the task clearly
- Then search for matching plugins
- Present the best matches with a brief explanation of why each fits
- If multiple plugins match, help the user compare and decide

## Important guidelines
- Always use the interactive widgets (`list_skills`, `suggest_plugin_install`) rather than writing skill names in text
- When suggesting plugins, explain in one sentence why each is relevant to the user's specific task
- If nothing matches, be honest and suggest the user describe their need differently, or offer to help them create a custom skill
- For Cowork's built-in document skills (PPT, Word, PDF, Excel), remind the user these are always available automatically — they don't need to install anything
