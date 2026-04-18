import json
from wiki_agent_mcp.infrastructure.llm_client import LLMClient
from wiki_agent_mcp.storage.session import SessionMemory
from wiki_agent_mcp.storage.persistent import PersistentMemory

class ReportingService:
    def __init__(self, llm_client: LLMClient, session_memory: SessionMemory, persistent_memory: PersistentMemory):
        self.llm = llm_client
        self.session = session_memory
        self.persistent = persistent_memory

    def generate_exploration_report(self, topic: str) -> str:
        session_summary = self.session.get_summary()
        persistent_summaries = self.persistent.get_all_summaries_for_topic(topic)
        recommendations = self.persistent.get_recommendations(topic)

        system = "You are a research assistant. Create a concise report based on exploration history."
        visited_nodes_text = "\n".join(session_summary["paths"]) if session_summary["paths"] else "None yet."
        summaries_text = "\n".join([f"- {path}: {summary[:100]}..." for path, summary in list(persistent_summaries.items())[:5]])
        recs_text = "\n".join([f"- {r['path']}: {r['reason']}" for r in recommendations[:5]])

        prompt = f"""Generate an exploration report for topic "{topic}".
Visited nodes: {session_summary['nodes_visited']}
Paths explored:
{visited_nodes_text}
Summaries:
{summaries_text}
Previous recommendations:
{recs_text}
Output Markdown report."""
        
        report = self.llm.generate(prompt, system=system, temperature=0.4)
        self._generate_smart_recommendations(topic)
        return report

    def _generate_smart_recommendations(self, topic: str):
        all_level1 = self.session.generated_level1.get(topic, [])
        all_level2 = []
        for key, l2list in self.session.generated_level2.items():
            if key.startswith(f"{topic}:"): all_level2.extend(l2list)
        
        visited = set(self.session.visited_nodes)
        unvisited = [item.get("path") for item in all_level1 if item.get("path") not in visited]
        unvisited.extend([item.get("path") for item in all_level2 if item.get("path") not in visited])
        
        if not unvisited: return
        
        system = "You are a recommendation engine."
        prompt = f"Topic: {topic}\nVisited: {', '.join(list(visited)[:10])}\nUnvisited: {', '.join(unvisited[:15])}\nRecommend up to 3 nodes as JSON."
        response = self.llm.generate(prompt, system=system, temperature=0.3)
        try:
            if "```json" in response: response = response.split("```json")[1].split("```")[0]
            recs = json.loads(response)
            for rec in recs:
                self.persistent.save_recommendation(topic, rec["path"], rec["reason"])
        except:
            if unvisited:
                self.persistent.save_recommendation(topic, unvisited[0], "Logical next step.")
