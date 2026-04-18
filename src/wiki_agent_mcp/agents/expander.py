from typing import List, Dict, Any
from wiki_agent_mcp.agents.base import BaseAgent

class ExpanderAgent(BaseAgent):
    def generate_level2_subtopics(self, topic: str, section_number: str, section_title: str) -> List[Dict[str, Any]]:
        """Generate Level 2 subtopics under a given Level 1 section."""
        cache_key = f"{topic}:{section_number}"
        if cache_key in self.session.generated_level2:
            return self.session.generated_level2[cache_key]

        system = "You are a Subtopic Expander. Generate 4-8 relevant Level 2 subtopics for a given section. Output JSON only."
        prompt = f"""For the wiki topic "{topic}", the Level 1 section "{section_number}. {section_title}" needs Level 2 subtopics.
Output format (JSON array):
[
  {{"number": "{section_number}.1", "title": "Specific Subtopic Title", "path": "{topic} > {section_number} > {section_number}.1"}},
  ...
]"""
        
        response = self.llm.generate(prompt, system=system, temperature=0.4)
        level2 = self._parse_json_response(response)
        
        if level2:
            self.session.generated_level2[cache_key] = level2
            return level2
            
        # Fallback
        fallback = [
            {"number": f"{section_number}.1", "title": "Foundational Concepts", "path": f"{topic} > {section_number} > {section_number}.1"},
            {"number": f"{section_number}.2", "title": "Key Principles", "path": f"{topic} > {section_number} > {section_number}.2"},
            {"number": f"{section_number}.3", "title": "Practical Applications", "path": f"{topic} > {section_number} > {section_number}.3"},
            {"number": f"{section_number}.4", "title": "Common Challenges", "path": f"{topic} > {section_number} > {section_number}.4"},
        ]
        self.session.generated_level2[cache_key] = fallback
        return fallback
