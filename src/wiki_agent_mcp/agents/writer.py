from wiki_agent_mcp.agents.base import BaseAgent

class WriterAgent(BaseAgent):
    def generate_level3_article(self, topic: str, subtopic_number: str, subtopic_title: str, parent_section_title: str = "") -> str:
        """Generate dense, wiki-style article for a Level 3 subtopic."""
        cache_key = f"{topic}:{subtopic_number} {subtopic_title}"
        if cache_key in self.session.generated_level3:
            return self.session.generated_level3[cache_key]

        system = "You are an expert Wiki Article Writer. Produce dense, factual, well-structured content in Markdown."
        prompt = f"""Write a detailed wiki-style article for:
Topic: "{topic}"
Section: "{parent_section_title}"
Subtopic: "{subtopic_number} {subtopic_title}"
Length: 800-1200 words."""
        
        response = self.llm.generate(prompt, system=system, temperature=0.5)
        self.session.generated_level3[cache_key] = response
        
        # Store summary in persistent memory
        summary = self._summarize_article(response)
        self.persistent.save_summary(topic, cache_key, summary)
        return response

    def _summarize_article(self, article: str, max_chars: int = 300) -> str:
        lines = article.splitlines()
        text = []
        for line in lines:
            if line.startswith('#'): continue
            if line.strip(): text.append(line.strip())
            if len(' '.join(text)) > max_chars: break
        summary = ' '.join(text)[:max_chars]
        if len(summary) >= max_chars:
            summary = summary.rsplit(' ', 1)[0] + "..."
        return summary
