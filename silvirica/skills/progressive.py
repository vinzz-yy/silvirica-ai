from __future__ import annotations
from typing import Any, Dict, List, Tuple
from silvirica.core.types import ComplexityLevel, SkillLevel
from silvirica.skills.loader import SkillLoader
from silvirica.skills.registry import SkillDefinition


class ProgressiveSkillManager:
    @classmethod
    def get_level0_metadata(cls, loader: SkillLoader) -> List[Dict[str, Any]]:
        return [
            {"name": s.name, "version": s.version, "priority": s.priority, "triggers": s.triggers}
            for s in loader.list_skills()
        ]

    @classmethod
    def get_level1_summaries(cls, loader: SkillLoader, skill_names: List[str]) -> str:
        return loader.load_skills_level1(skill_names)

    @classmethod
    def get_level2_full_instructions(cls, loader: SkillLoader, skill_names: List[str]) -> str:
        return loader.load_skills_level2(skill_names)


class ProgressiveSkillLoader:
    def __init__(self, loader: SkillLoader):
        self.loader = loader

    def resolve_and_render_skills(self, matched_skill_names: List[str], complexity: ComplexityLevel, max_level_2_skills: int = 2) -> Tuple[str, Dict[str, int]]:
        all_skills = self.loader.list_skills()
        skill_map = {s.name: s for s in all_skills}
        level_stats = {"installed": len(all_skills), "matched": len(matched_skill_names), "level_0": 0, "level_1": 0, "level_2": 0}
        rendered_sections: List[str] = []
        fully_loaded_count = 0
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_matched = sorted(matched_skill_names, key=lambda name: priority_order.get(skill_map.get(name, SkillDefinition("")).priority, 2))

        for name in sorted_matched:
            skill = skill_map.get(name)
            if not skill:
                continue
            if complexity >= ComplexityLevel.LEVEL_3_COMPLEX and fully_loaded_count < max_level_2_skills:
                rendered_sections.append(skill.render(SkillLevel.LEVEL_2_FULL))
                level_stats["level_2"] += 1
                fully_loaded_count += 1
            elif complexity >= ComplexityLevel.LEVEL_1_SIMPLE:
                rendered_sections.append(skill.render(SkillLevel.LEVEL_1_SUMMARY))
                level_stats["level_1"] += 1
                fully_loaded_count += 1
            else:
                rendered_sections.append(skill.render(SkillLevel.LEVEL_0_METADATA))
                level_stats["level_0"] += 1

        return "\n\n".join(rendered_sections), level_stats
