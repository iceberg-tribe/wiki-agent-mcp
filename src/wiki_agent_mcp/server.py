import os
import json
import sys
from pathlib import Path
import mcp.types as types
from mcp.server import Server

from wiki_agent_mcp.infrastructure.llm_client import LLMClient
from wiki_agent_mcp.storage.session import SessionMemory
from wiki_agent_mcp.storage.persistent import PersistentMemory
from wiki_agent_mcp.agents.architect import ArchitectAgent
from wiki_agent_mcp.agents.expander import ExpanderAgent
from wiki_agent_mcp.agents.writer import WriterAgent
from wiki_agent_mcp.domain.reporting import ReportingService
from wiki_agent_mcp.utils.config import init_data_dirs, CACHE_DIR

# Global state
session_memory = SessionMemory(cache_dir=CACHE_DIR)
persistent_memory = PersistentMemory()
llm_client = LLMClient(provider=os.environ.get("LLM_PROVIDER", "openai"), 
                       model=os.environ.get("LLM_MODEL", None))

# Portable path to SKILL.md
SKILL_PATH = Path(__file__).parent / "SKILL.md"

architect = ArchitectAgent(llm_client, session_memory, persistent_memory)
expander = ExpanderAgent(llm_client, session_memory, persistent_memory)
writer = WriterAgent(llm_client, session_memory, persistent_memory)
reporter = ReportingService(llm_client, session_memory, persistent_memory)

server = Server("wiki-agent-server")
current_topic = None

# -------------------------------
# Resources & Prompts
# -------------------------------

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="wiki://skill-guide",
            name="Wiki-Agent Session Skill Guide",
            description="The master operating manual for running a wiki research session.",
            mimeType="text/markdown"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    if uri == "wiki://skill-guide":
        if SKILL_PATH.exists():
            return SKILL_PATH.read_text(encoding="utf-8")
        return f"Skill guide not found at {SKILL_PATH}"
    raise ValueError(f"Unknown resource: {uri}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="wiki-session",
            description="Start a new focused research session on a topic.",
            arguments=[
                types.PromptArgument(
                    name="topic",
                    description="The research topic to explore.",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    if name == "wiki-session":
        topic = arguments.get("topic", "General Research")
        return types.GetPromptResult(
            description=f"Initializes a wiki session for {topic}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Let's start a wiki session for '{topic}'. Please follow the rules in SKILL.md (available at wiki://skill-guide) to initiate, explore, and eventually close this session."
                    )
                )
            ]
        )
    raise ValueError(f"Unknown prompt: {name}")

# -------------------------------
# Tools
# -------------------------------

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_level1",
            description="INITIATION: Generate Level 1 Table of Contents for a topic. Use this to start a session.",
            inputSchema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"]
            }
        ),
        types.Tool(
            name="get_level1",
            description="RECALL: Retrieve cached Level 1 ToC. Check this before regenerating a topic.",
            inputSchema={"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}
        ),
        types.Tool(
            name="generate_level2",
            description="EXPLORATION: Generate Level 2 subtopics for a section.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "section_number": {"type": "string"},
                    "section_title": {"type": "string"}
                },
                "required": ["topic", "section_number", "section_title"]
            }
        ),
        types.Tool(
            name="generate_level3",
            description="DEEP DIVE: Generate a dense Level 3 article. Use this for all conceptual questions to build a permanent KB.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "subtopic_number": {"type": "string"},
                    "subtopic_title": {"type": "string"},
                    "parent_section_title": {"type": "string"}
                },
                "required": ["topic", "subtopic_number", "subtopic_title"]
            }
        ),
        types.Tool(
            name="record_visit",
            description="MANDATORY: Record that a specific node path was explored. Must be called AFTER every tool interaction.",
            inputSchema={
                "type": "object",
                "properties": {"node_path": {"type": "string"}},
                "required": ["node_path"]
            }
        ),
        types.Tool(
            name="generate_report",
            description="CLOSURE: Generate an exploration report. Use this with /wiki end to finalize the session.",
            inputSchema={"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}
        ),
        types.Tool(
            name="get_session_summary",
            description="STATS: Get a summary of current session memory (nodes, queries, duration).",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="add_user_query",
            description="MANDATORY: Record a user query. Must be called BEFORE answering or taking any action.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        ),
        types.Tool(
            name="search_level3",
            description="SEARCH: Search generated Level 3 articles in the current session.",
            inputSchema={"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]}
        ),
        types.Tool(
            name="suggest_next_steps",
            description="GUIDANCE: Analyze current session and suggest the top 3 most logical sections to explore next.",
            inputSchema={"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}
        ),
        types.Tool(
            name="get_skill_guide",
            description="HELP: Retrieve the full SKILL.md operating manual for the wiki agent.",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    global current_topic
    try:
        if name == "generate_level1":
            topic = arguments["topic"]
            current_topic = topic
            level1 = architect.generate_level1_toc(topic)
            result = json.dumps(level1, indent=2)
        elif name == "get_level1":
            topic = arguments["topic"]
            if topic in session_memory.generated_level1:
                result = json.dumps(session_memory.generated_level1[topic], indent=2)
            else:
                result = f"No Level 1 generated for '{topic}'."
        elif name == "generate_level2":
            topic = arguments["topic"]
            section_num = arguments["section_number"]
            section_title = arguments["section_title"]
            level2 = expander.generate_level2_subtopics(topic, section_num, section_title)
            result = json.dumps(level2, indent=2)
        elif name == "generate_level3":
            topic = arguments["topic"]
            sub_num = arguments["subtopic_number"]
            sub_title = arguments["subtopic_title"]
            parent_title = arguments.get("parent_section_title", "")
            article = writer.generate_level3_article(topic, sub_num, sub_title, parent_title)
            result = article
        elif name == "record_visit":
            node_path = arguments["node_path"]
            session_memory.record_visit(node_path)
            result = f"Recorded visit to: {node_path}"
        elif name == "generate_report":
            topic = arguments["topic"]
            report = reporter.generate_exploration_report(topic)
            result = report
        elif name == "get_session_summary":
            result = json.dumps(session_memory.get_summary(), indent=2)
        elif name == "add_user_query":
            query = arguments["query"]
            session_memory.add_query(query)
            result = f"Added query: {query}"
        elif name == "search_level3":
            keyword = arguments["keyword"].lower()
            matches = []
            for key, content in session_memory.generated_level3.items():
                if keyword in content.lower(): matches.append(key)
            result = f"Found in:\n- " + "\n- ".join(matches[:10]) if matches else f"No matches for '{keyword}'."
        elif name == "suggest_next_steps":
            topic = arguments["topic"]
            result = reporter.suggest_next_steps(topic)
        elif name == "get_skill_guide":
            if SKILL_PATH.exists():
                result = SKILL_PATH.read_text(encoding="utf-8")
            else:
                result = f"Skill guide not found at {SKILL_PATH}"
        else:
            result = f"Unknown tool: {name}"
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]