from typing import List, Dict, Any
from wiki_agent_mcp.agents.base import BaseAgent

class ArchitectAgent(BaseAgent):
    def generate_level1_toc(self, topic: str) -> List[Dict[str, Any]]:
        """Generate main Level 1 headings for the topic."""
        if topic in self.session.generated_level1:
            return self.session.generated_level1[topic]

        system = "You are an expert Outline Architect. Create a Level 1 Table of Contents for a wiki article on a given topic. Output only valid JSON."
        prompt = f"""Create a Level 1 Table of Contents for a wiki article on "{topic}".
Requirements:
- 8 to 15 main sections (number them 1, 2, 3...)
- Each section should have a clear, descriptive title
- Return ONLY the JSON array.
Format:
[
  {{"number": 1, "title": "Introduction & Core Definition", "path": "{topic} > 1"}},
  ...
]"""
        
        response = self.llm.generate(prompt, system=system, temperature=0.4)
        level1 = self._parse_json_response(response)
        
        if level1:
            for item in level1:
                if "path" not in item:
                    item["path"] = f"{topic} > {item['number']}"
            self.session.save_level1(topic, level1)
            return level1
        
        # Fallback
        fallback = [
            {"number": 1, "title": "Introduction & Core Definition", "path": f"{topic} > 1"},
            {"number": 2, "title": "History & Evolution", "path": f"{topic} > 2"},
            {"number": 3, "title": "Core Methodologies", "path": f"{topic} > 3"},
            {"number": 4, "title": "Key Tools & Technologies", "path": f"{topic} > 4"},
            {"number": 5, "title": "Case Studies", "path": f"{topic} > 6"},
            {"number": 6, "title": "Future Trajectories", "path": f"{topic} > 7"},
        ]
        self.session.save_level1(topic, fallback)
        return fallback
