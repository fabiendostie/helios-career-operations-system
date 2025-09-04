"""
Unit tests for SkillMapper functionality.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from resume_extractor.components.consolidation import (
    SkillMapper, 
    SkillEntry, 
    SkillInventoryEntry
)


@pytest.fixture
def sample_skill_map():
    """Sample skill mapping data for tests."""
    return {
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
                "programmation python"
            ],
            "JavaScript": [
                "javascript",
                "js",
                "JS"
            ]
        }
    }


@pytest.fixture
def temp_skill_map_file(tmp_path, sample_skill_map):
    """Create a temporary skill map file for testing."""
    skill_map_file = tmp_path / "test_skill_map.json"
    with open(skill_map_file, 'w', encoding='utf-8') as f:
        json.dump(sample_skill_map, f)
    return skill_map_file


@pytest.fixture
def skill_mapper(temp_skill_map_file):
    """Create a SkillMapper instance with test data."""
    return SkillMapper(mapping_file=temp_skill_map_file)


class TestSkillMapper:
    """Test cases for SkillMapper class."""

    def test_init_with_valid_file(self, skill_mapper):
        """Test SkillMapper initialization with valid file."""
        assert skill_mapper.skill_mappings is not None
        assert "Project Management" in skill_mapper.skill_mappings
        assert skill_mapper.fuzzy_threshold == 85

    def test_init_with_missing_file(self, tmp_path):
        """Test SkillMapper initialization with missing file."""
        missing_file = tmp_path / "missing.json"
        mapper = SkillMapper(mapping_file=missing_file)
        assert mapper.skill_mappings == {}
        assert mapper.canonical_skills == {}

    def test_init_with_invalid_json(self, tmp_path):
        """Test SkillMapper initialization with invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        mapper = SkillMapper(mapping_file=invalid_file)
        assert mapper.skill_mappings == {}

    def test_build_canonical_index(self, skill_mapper):
        """Test building canonical skill index."""
        assert "project management" in skill_mapper.canonical_skills
        assert "gestion de projet" in skill_mapper.canonical_skills
        assert "pm" in skill_mapper.canonical_skills
        assert skill_mapper.canonical_skills["project management"] == "Project Management"
        assert skill_mapper.canonical_skills["gestion de projet"] == "Project Management"

    def test_exact_matching_canonical(self, skill_mapper):
        """Test exact matching of canonical skill names."""
        result = skill_mapper._find_canonical_skill("Project Management")
        assert result == "Project Management"

    def test_exact_matching_variation(self, skill_mapper):
        """Test exact matching of skill variations."""
        result = skill_mapper._find_canonical_skill("Gestion de projet")
        assert result == "Project Management"

    def test_case_insensitive_matching(self, skill_mapper):
        """Test case-insensitive skill matching."""
        result = skill_mapper._find_canonical_skill("PROJECT MANAGEMENT")
        assert result == "Project Management"
        
        result = skill_mapper._find_canonical_skill("gestion DE projet")
        assert result == "Project Management"

    def test_fuzzy_matching_close_match(self, skill_mapper):
        """Test fuzzy matching for close variations."""
        # Should match "Project Management" with high similarity
        result = skill_mapper._find_canonical_skill("Project Managment")  # Missing 'e'
        assert result == "Project Management"

    def test_fuzzy_matching_threshold(self, skill_mapper):
        """Test fuzzy matching respects threshold."""
        # Should not match due to low similarity
        result = skill_mapper._find_canonical_skill("Completely Different Skill")
        assert result == "Completely Different Skill"  # Returns original

    def test_no_match_returns_original(self, skill_mapper):
        """Test that unmatched skills return original name."""
        result = skill_mapper._find_canonical_skill("Brand New Skill")
        assert result == "Brand New Skill"

    def test_user_corrections_priority(self, skill_mapper):
        """Test that user corrections take priority."""
        skill_mapper.learn_from_user_input("custom skill", "Canonical Skill")
        result = skill_mapper._find_canonical_skill("custom skill")
        assert result == "Canonical Skill"

    def test_map_skills_basic(self, skill_mapper):
        """Test basic skill mapping functionality."""
        skills = [
            SkillEntry("Python", "doc1", "Programming"),
            SkillEntry("programmation python", "doc2", "Programming"),
            SkillEntry("Gestion de projet", "doc3", "Management")
        ]
        
        result = skill_mapper.map_skills(skills)
        
        # Should consolidate Python and programmation python
        assert "Python" in result
        assert "Project Management" in result
        assert len(result) == 2
        
        # Check evidence pointers
        python_entry = result["Python"]
        assert len(python_entry.evidence_pointers) == 2
        assert "doc1" in python_entry.evidence_pointers
        assert "doc2" in python_entry.evidence_pointers

    def test_map_skills_categories(self, skill_mapper):
        """Test skill mapping preserves and merges categories."""
        skills = [
            SkillEntry("Python", "doc1", "Programming Languages"),
            SkillEntry("python", "doc2", "Technical Skills")
        ]
        
        result = skill_mapper.map_skills(skills)
        python_entry = result["Python"]
        
        assert "Programming Languages" in python_entry.categories
        assert "Technical Skills" in python_entry.categories
        assert len(python_entry.categories) == 2

    def test_proficiency_determination(self, skill_mapper):
        """Test proficiency level determination based on evidence count."""
        # Create entries with different evidence counts
        beginner_entry = SkillInventoryEntry("Skill1", ["doc1"], set(), [])
        intermediate_entry = SkillInventoryEntry("Skill2", ["doc1", "doc2", "doc3"], set(), [])
        expert_entry = SkillInventoryEntry("Skill3", ["doc1", "doc2", "doc3", "doc4", "doc5"], set(), [])
        
        assert beginner_entry._determine_proficiency() == "beginner"
        assert intermediate_entry._determine_proficiency() == "intermediate"
        assert expert_entry._determine_proficiency() == "expert"

    def test_skill_inventory_entry_to_dict(self, skill_mapper):
        """Test SkillInventoryEntry serialization to dict."""
        entry = SkillInventoryEntry(
            skill="Python",
            evidence_pointers=["doc1", "doc2", "doc3"],
            categories={"Programming", "Technical"},
            proficiency_indicators=[]
        )
        
        result = entry.to_dict()
        
        assert result["skill"] == "Python"
        assert result["evidence_pointers"] == ["doc1", "doc2", "doc3"]
        assert set(result["categories"]) == {"Programming", "Technical"}
        assert result["proficiency"] == "intermediate"

    def test_add_skill_mapping(self, skill_mapper):
        """Test adding new skill mappings at runtime."""
        skill_mapper.add_skill_mapping("Data Science", ["science des données", "DS"])
        
        # Should now map the new variations
        result = skill_mapper._find_canonical_skill("science des données")
        assert result == "Data Science"
        
        result = skill_mapper._find_canonical_skill("DS")
        assert result == "Data Science"

    def test_learn_from_user_input(self, skill_mapper):
        """Test learning from user corrections."""
        skill_mapper.learn_from_user_input("ML", "Machine Learning")
        
        # Should now map ML to Machine Learning
        result = skill_mapper._find_canonical_skill("ML")
        assert result == "Machine Learning"
        
        # Should be case insensitive
        result = skill_mapper._find_canonical_skill("ml")
        assert result == "Machine Learning"

    def test_assign_categories_programming_languages(self, skill_mapper):
        """Test category assignment for programming languages."""
        skills = ["Python", "Java", "JavaScript", "C++", "TypeScript"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "Python" in categorized["Programming Languages"]
        assert "Java" in categorized["Programming Languages"]
        assert "JavaScript" in categorized["Programming Languages"]

    def test_assign_categories_frameworks(self, skill_mapper):
        """Test category assignment for frameworks."""
        skills = ["React", "Django", "TensorFlow", "Angular"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "React" in categorized["Frameworks & Libraries"]
        assert "Django" in categorized["Frameworks & Libraries"]

    def test_assign_categories_databases(self, skill_mapper):
        """Test category assignment for databases."""
        skills = ["MySQL", "PostgreSQL", "MongoDB", "SQL"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "MySQL" in categorized["Databases"]
        assert "PostgreSQL" in categorized["Databases"]

    def test_assign_categories_cloud(self, skill_mapper):
        """Test category assignment for cloud technologies."""
        skills = ["AWS", "Docker", "Kubernetes", "DevOps"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "AWS" in categorized["Cloud & DevOps"]
        assert "Docker" in categorized["Cloud & DevOps"]

    def test_assign_categories_soft_skills(self, skill_mapper):
        """Test category assignment for soft skills."""
        skills = ["Leadership", "Communication", "Team Management"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "Leadership" in categorized["Soft Skills"]
        assert "Communication" in categorized["Soft Skills"]

    def test_assign_categories_other(self, skill_mapper):
        """Test category assignment falls back to Other."""
        skills = ["Unknown Skill", "Random Technology"]
        categorized = skill_mapper._assign_categories(skills)
        
        assert "Unknown Skill" in categorized["Other"]
        assert "Random Technology" in categorized["Other"]

    def test_bilingual_skill_consolidation(self, skill_mapper):
        """Test end-to-end bilingual skill consolidation."""
        skills = [
            SkillEntry("Project Management", "doc1", None),
            SkillEntry("Gestion de projet", "doc2", None),
            SkillEntry("Chef de projet", "doc3", None),
            SkillEntry("Python", "doc4", None),
            SkillEntry("programmation python", "doc5", None)
        ]
        
        result = skill_mapper.map_skills(skills)
        
        # Should consolidate to 2 unique skills
        assert len(result) == 2
        assert "Project Management" in result
        assert "Python" in result
        
        # Project Management should have 3 evidence pointers
        pm_entry = result["Project Management"]
        assert len(pm_entry.evidence_pointers) == 3
        
        # Python should have 2 evidence pointers
        python_entry = result["Python"]
        assert len(python_entry.evidence_pointers) == 2

    def test_empty_skills_list(self, skill_mapper):
        """Test handling of empty skills list."""
        result = skill_mapper.map_skills([])
        assert result == {}

    def test_skills_with_none_values(self, skill_mapper):
        """Test handling of skills with None or empty values."""
        skills = [
            SkillEntry("", "doc1", None),
            SkillEntry("   ", "doc2", None),
            SkillEntry("Python", "doc3", None)
        ]
        
        result = skill_mapper.map_skills(skills)
        
        # Should handle empty/whitespace skills gracefully
        assert "Python" in result
        # Empty skills should still create entries (normalized to empty string)
        assert len(result) >= 1

    def test_special_characters_in_skills(self, skill_mapper):
        """Test handling of skills with special characters."""
        skills = [
            SkillEntry("C++", "doc1", None),
            SkillEntry("C#", "doc2", None),
            SkillEntry(".NET", "doc3", None)
        ]
        
        result = skill_mapper.map_skills(skills)
        
        # Should handle special characters without errors
        assert len(result) == 3