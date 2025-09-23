"""
Integration tests for skill consolidation in ConsolidationEngine.
"""

import json
import pytest
from pathlib import Path

from resume_extractor.components.consolidation import (
    ConsolidationEngine,
    ParsedData,
    SkillMapper
)


@pytest.fixture
def sample_skill_map(tmp_path):
    """Create a sample skill map file."""
    skill_map = {
        "skill_mappings": {
            "Project Management": [
                "Gestion de projet",
                "Chef de projet",
                "Project Manager",
                "PM"
            ],
            "Python": [
                "python",
                "py",
                "python3",
                "programmation python",
                "développement python"
            ],
            "Data Analysis": [
                "Analyse de données",
                "Data Analytics",
                "analyse des données"
            ]
        }
    }

    skill_map_file = tmp_path / "skill_map.json"
    with open(skill_map_file, 'w', encoding='utf-8') as f:
        json.dump(skill_map, f)
    return skill_map_file


@pytest.fixture
def consolidation_engine(sample_skill_map):
    """Create ConsolidationEngine with test skill mapper."""
    engine = ConsolidationEngine()
    engine.skill_mapper = SkillMapper(sample_skill_map)
    return engine


@pytest.fixture
def sample_parsed_data():
    """Sample parsed data with bilingual skills."""
    return [
        ParsedData(
            content={
                "skills": ["Python", "Project Management", "Data Analysis"],
                "work_experience": [
                    {"title": "Developer", "company": "TechCorp"}
                ]
            },
            source_file="resume_en.pdf",
            language="en"
        ),
        ParsedData(
            content={
                "skills": ["programmation python", "Gestion de projet", "Analyse de données"],
                "work_experience": [
                    {"title": "Développeur", "company": "TechCorp"}
                ]
            },
            source_file="cv_fr.pdf",
            language="fr"
        ),
        ParsedData(
            content={
                "skills": ["py", "PM", "Data Analytics"],
                "projects": [
                    {"name": "Data Pipeline"}
                ]
            },
            source_file="portfolio.md",
            language="en"
        )
    ]


class TestConsolidationEngineSkills:
    """Test skill consolidation in ConsolidationEngine."""

    def test_consolidate_skills_method(self, sample_skill_map):
        """Test the consolidate_skills method directly."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        parsed_data = [
            ParsedData(
                content={"skills": ["Python", "Gestion de projet"]},
                source_file="doc1.pdf",
                language="en"
            ),
            ParsedData(
                content={"skills": ["programmation python", "PM"]},
                source_file="doc2.pdf",
                language="fr"
            )
        ]

        result = engine.consolidate_skills(parsed_data)

        # Should consolidate to canonical forms
        assert "Python" in str(result)
        assert "Project Management" in str(result)

        # Should have proper categorization
        assert isinstance(result, dict)

        # Should contain evidence pointers
        for category_skills in result.values():
            for skill_data in category_skills.values():
                assert "evidence_pointers" in skill_data
                assert len(skill_data["evidence_pointers"]) > 0

    def test_legacy_consolidate_skills(self, sample_skill_map):
        """Test the legacy _consolidate_skills method."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        skills = ["Python", "programmation python", "Gestion de projet", "PM"]
        result = engine._consolidate_skills(skills)

        # Should consolidate bilingual skills
        assert "Python" in result
        assert "Project Management" in result
        assert len(result) == 2

    def test_infer_category(self, consolidation_engine):
        """Test category inference for skills."""
        engine = consolidation_engine

        assert engine._infer_category("Python") == "Programming Languages"
        assert engine._infer_category("React") == "Frameworks & Libraries"
        assert engine._infer_category("MySQL") == "Databases"
        assert engine._infer_category("AWS") == "Cloud & DevOps"
        assert engine._infer_category("Leadership") == "Soft Skills"
        assert engine._infer_category("Unknown Skill") == "Other"

    def test_categorize_inventory(self, sample_skill_map):
        """Test inventory categorization."""
        from resume_extractor.components.consolidation import SkillInventoryEntry

        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        inventory = {
            "Python": SkillInventoryEntry(
                skill="Python",
                evidence_pointers=["doc1"],
                categories={"Programming Languages"},
                proficiency_indicators=[]
            ),
            "Leadership": SkillInventoryEntry(
                skill="Leadership",
                evidence_pointers=["doc2"],
                categories={"Soft Skills"},
                proficiency_indicators=[]
            )
        }

        result = engine._categorize_inventory(inventory)

        assert "Programming Languages" in result
        assert "Soft Skills" in result
        assert "Python" in result["Programming Languages"]
        assert "Leadership" in result["Soft Skills"]

    def test_bilingual_consolidation_integration(self, sample_parsed_data, sample_skill_map):
        """Test end-to-end bilingual skill consolidation."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        result = engine.consolidate_skills(sample_parsed_data)

        # Should have consolidated bilingual skills
        all_skills = []
        for category_skills in result.values():
            all_skills.extend(category_skills.keys())

        assert "Python" in all_skills
        assert "Project Management" in all_skills
        assert "Data Analysis" in all_skills

        # Should not have duplicate language variants
        assert "programmation python" not in all_skills
        assert "Gestion de projet" not in all_skills
        assert "PM" not in all_skills

    def test_evidence_pointers_tracking(self, sample_parsed_data, sample_skill_map):
        """Test that evidence pointers correctly track source documents."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        result = engine.consolidate_skills(sample_parsed_data)

        # Find Python skill across categories
        python_data = None
        for category_skills in result.values():
            if "Python" in category_skills:
                python_data = category_skills["Python"]
                break

        assert python_data is not None
        assert len(python_data["evidence_pointers"]) == 3  # 3 documents mention Python variants

        # Should track different source documents
        evidence = python_data["evidence_pointers"]
        assert any("resume_en.pdf" in ref for ref in evidence)
        assert any("cv_fr.pdf" in ref for ref in evidence)
        assert any("portfolio.md" in ref for ref in evidence)

    def test_proficiency_levels(self, sample_parsed_data, sample_skill_map):
        """Test proficiency level assignment based on evidence."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        result = engine.consolidate_skills(sample_parsed_data)

        # Python appears in all 3 documents, should be intermediate
        python_data = None
        for category_skills in result.values():
            if "Python" in category_skills:
                python_data = category_skills["Python"]
                break

        assert python_data is not None
        assert python_data["proficiency"] == "intermediate"  # 3 evidence points

    def test_empty_skills_handling(self, sample_skill_map):
        """Test handling of documents with no skills."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        parsed_data = [
            ParsedData(
                content={"skills": []},
                source_file="empty.pdf",
                language="en"
            ),
            ParsedData(
                content={},  # No skills key
                source_file="nostills.pdf",
                language="fr"
            )
        ]

        result = engine.consolidate_skills(parsed_data)

        # Should handle gracefully
        assert isinstance(result, dict)
        assert len(result) == 0  # No skills to consolidate

    def test_case_insensitive_consolidation(self, sample_skill_map):
        """Test case-insensitive skill consolidation."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        parsed_data = [
            ParsedData(
                content={"skills": ["PYTHON", "project management"]},
                source_file="doc1.pdf",
                language="en"
            ),
            ParsedData(
                content={"skills": ["Python", "PROJECT MANAGEMENT"]},
                source_file="doc2.pdf",
                language="en"
            )
        ]

        result = engine.consolidate_skills(parsed_data)

        # Should consolidate despite case differences
        all_skills = []
        for category_skills in result.values():
            all_skills.extend(category_skills.keys())

        assert "Python" in all_skills
        assert "Project Management" in all_skills
        assert len([s for s in all_skills if s.lower() == "python"]) == 1
        assert len([s for s in all_skills if s.lower() == "project management"]) == 1

    def test_special_characters_in_skills(self, sample_skill_map):
        """Test handling of skills with special characters."""
        engine = ConsolidationEngine()
        engine.skill_mapper = SkillMapper(sample_skill_map)

        parsed_data = [
            ParsedData(
                content={"skills": ["C++", "C#", ".NET", "Node.js"]},
                source_file="tech.pdf",
                language="en"
            )
        ]

        result = engine.consolidate_skills(parsed_data)

        # Should handle special characters without errors
        assert isinstance(result, dict)

        # Should create entries for each skill
        all_skills = []
        for category_skills in result.values():
            all_skills.extend(category_skills.keys())

        assert len(all_skills) == 4
