---
name: wiki-agent-session
description: >
  Use this skill whenever the user wants to explore a topic using the wiki-agent
  tool suite. Triggers include: "/wiki start <topic>", "explore X with wiki",
  "let's do a wiki session on X", or any request to deep-dive a domain using
  the structured Level 1 → Level 2 → Level 3 knowledge tree. Also triggers on
  "/wiki end" to close an active session with a report. Enforces a full session
  lifecycle: initiation → exploration → closure.
---

# Wiki-Agent Session Skill

The wiki-agent is a **session-oriented knowledge exploration tool**. It has two
distinct memory layers with different lifetimes:

| Layer | Tools | Lifetime |
|---|---|---|
| Content | `generate_level1/2/3`, `get_level1`, `search_level3` | ♾️ Persistent across chats |
| Session | `add_user_query`, `record_visit`, `get_session_summary` | ⏱️ This chat only |
| Closure | `generate_report` | ♾️ Persistent (stored as generated content) |

Your job is to enforce the full lifecycle — initiation, exploration, and
closure — as described below.

---

## Tool Reference

| Tool | Params | Purpose |
|---|---|---|
| `generate_level1` | `topic` | Generate 15-section ToC via Outline Architect |
| `get_level1` | `topic` | Retrieve cached ToC (no regeneration) |
| `generate_level2` | `topic`, `section_number`, `section_title` | Expand a section into ~8 subtopics |
| `generate_level3` | `topic`, `subtopic_number`, `subtopic_title`, `parent_section_title?` | Generate a dense article for a leaf node |
| `search_level3` | `keyword` | Search all previously generated Level 3 articles |
| `add_user_query` | `query` | Log a query to session memory |
| `record_visit` | `node_path` | Log a visited node (e.g. `topic > 5 > 5.8`) |
| `get_session_summary` | *(none)* | Return session stats: nodes visited, queries, duration |
| `generate_report` | `topic` | Generate a full exploration report (permanent) |

---

## Session Lifecycle

### 1. INITIATION — `/wiki start <topic>`

When the user triggers a session:

```
1. generate_level1(topic)
2. Display the ToC clearly as a numbered table
3. Remind user of available moves (see Move Menu below)
```

**Move Menu** — always show this after initiation and after each interaction:

```
📖 Pick a section number     → I'll expand it (Level 2)
📄 Pick a subsection number  → I'll generate the full article (Level 3)
🔍 /wiki search <keyword>    → Search existing articles
❓ Ask a conceptual question → I'll generate it as a permanent article
📊 /wiki end                 → Close session with a report
```

If the topic has a cached Level 1 (`get_level1` returns results), retrieve
and display it instead of regenerating.

---

### 2. EXPLORATION — Every Interaction

**Every single user interaction inside a session must follow this exact sequence:**

```
Step 1 — add_user_query(raw query or action description)
Step 2 — Determine interaction type (see below)
Step 3 — Execute the appropriate tool(s)
Step 4 — record_visit(node_path)
Step 5 — Respond to user
Step 6 — Show abbreviated Move Menu as a reminder
```

Never skip Steps 1 or 4. They are mandatory for the session report to be
meaningful at closure.

#### Interaction Types

**A. User picks a section number (e.g. "5")**
```
→ generate_level2(topic, section_number, section_title)
→ record_visit("topic > N")
→ Display subtopics as a table
```

**B. User picks a subsection number (e.g. "5.8")**
```
→ generate_level3(topic, subtopic_number, subtopic_title, parent_section_title)
→ record_visit("topic > N > N.M")
→ Display the article
```

**C. User asks a conceptual question (e.g. "explain the joint distribution")**

This is the most important case. Do NOT answer from your own knowledge.
Instead:

```
→ add_user_query(question)
→ Derive a clean subtopic_title from the question
  (e.g. "explain joint distribution" → "Joint Distribution Derivation and Markov Assumption")
→ Assign a subtopic_number extending the last visited node
  (e.g. if last visited was 5.8, use "5.8.1")
→ generate_level3(topic, subtopic_number, derived_title, parent_section_title)
→ record_visit("topic > N > N.M > N.M.K")
→ Display the generated article
```

**Why this matters:** `generate_level3` output is stored permanently and
searchable via `search_level3` in any future session. Answering from your
own knowledge produces nothing persistent. Every conceptual question is a
content generation opportunity.

**D. User runs `/wiki search <keyword>`**
```
→ search_level3(keyword)
→ Display matching articles or summaries
→ Offer to expand any result to full Level 3 if not already generated
```

**E. User navigates back up (e.g. "go back to section 5")**
```
→ get_level1(topic) or recall Level 2 from context
→ Display the relevant level
→ record_visit("topic > N")
```

---

### 3. CLOSURE — `/wiki end`

When the user triggers session end:

```
1. get_session_summary()          → retrieve session stats
2. Display summary to user:
   - Topics covered
   - Nodes visited (with paths)
   - Queries asked
   - Session duration
3. generate_report(topic)         → generate permanent closure artifact
4. Display the report
5. Suggest /wiki start <related_topic> if natural follow-on exists
```

The report is permanent — it lives in the content layer and is retrievable
in future sessions.

---

## Key Principles

### Conceptual questions = generate_level3, always
Never answer "explain X" or "what is X" from memory inside a wiki session.
Always generate a Level 3 article. This is the mechanism by which the
session builds a permanent, searchable knowledge base.

### Node path convention
```
topic > section_number > subsection_number > concept_number
e.g.  "bayesian network in e-commerce > 5 > 5.8 > 5.8.1"
```
Use this format consistently for `record_visit`.

### Subtopic numbering for conceptual questions
Extend the last visited node's path:
- Last visited: `5.8` → conceptual article gets `5.8.1`, `5.8.2`, etc.
- Last visited: `5` → conceptual article gets `5.0.1` (section-level concept)
- No prior visit → use `0.1`, `0.2` etc. (intro-level concepts)

### Move Menu cadence
Show the abbreviated Move Menu after every response. Keep it short:
```
→ Pick section | Pick subsection | Ask a question | /wiki search | /wiki end
```

### Session state in context
Track the following in your working memory throughout the session:
- `current_topic` — the active topic string
- `last_visited_path` — most recent node path
- `last_visited_number` — most recent subtopic number (for concept numbering)

---

## Example Session Flow

```
User:  /wiki start bayesian network in e-commerce
Claude: [generate_level1] → display 15 sections → show Move Menu

User:  5
Claude: [add_user_query] [generate_level2] [record_visit] → display 8 subtopics → Move Menu

User:  5.8
Claude: [add_user_query] [generate_level3] [record_visit] → display article → Move Menu

User:  explain the joint distribution
Claude: [add_user_query]
        → derive title: "Joint Distribution Derivation and Markov Assumption"
        → assign number: "5.8.1"
        [generate_level3("5.8.1", derived_title)]
        [record_visit("topic > 5 > 5.8 > 5.8.1")]
        → display article → Move Menu

User:  /wiki end
Claude: [get_session_summary] → display stats
        [generate_report] → display report
        → suggest follow-on topic
```

---

## Anti-Patterns to Avoid

| ❌ Wrong | ✅ Right |
|---|---|
| Answer conceptual questions from memory | `generate_level3` every time |
| Skip `add_user_query` | Always log before acting |
| Skip `record_visit` | Always log after acting |
| Show full Move Menu every time | Show abbreviated version mid-session |
| Regenerate Level 1 if cached | Use `get_level1` first |
| End session without `generate_report` | Always close with a report |
