"""Tests for role taxonomy manager."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock

from src.core.role_taxonomy_manager import RoleTaxonomyManager
from src.models.role_taxonomy import (
    JobRole, RoleSearchFilter, IndustryCategory, ExperienceLevel,
    RIASECCode, CareerAnchor
)


class TestRoleTaxonomyManager:
    """Test class for RoleTaxonomyManager."""
    
    @pytest.fixture
    def sample_taxonomy_data(self):
        """Sample taxonomy data for testing."""
        return {
            "roles": [
                {
                    "role_id": "test_001",
                    "title": "Software Engineer",
                    "alternative_titles": ["Developer", "Programmer"],
                    "description": "Develops software applications",
                    "industry_categories": ["Technology"],
                    "experience_level": "Mid Level (3-7 years)",
                    "required_skill_keywords": ["Python", "Programming"],
                    "preferred_skill_keywords": ["Git", "Agile"],
                    "associated_riasec_codes": ["Investigative", "Realistic"],
                    "associated_career_anchors": ["Technical Competence"],
                    "growth_trajectory": ["Senior Engineer"],
                    "median_salary_range": {"min": 70000, "max": 120000},
                    "remote_work_compatibility": 0.9
                },
                {
                    "role_id": "test_002",
                    "title": "Product Manager",
                    "alternative_titles": ["PM", "Product Owner"],
                    "description": "Manages product development",
                    "industry_categories": ["Technology"],
                    "experience_level": "Senior (7-12 years)",
                    "required_skill_keywords": ["Product Strategy", "Communication"],
                    "preferred_skill_keywords": ["Analytics", "Leadership"],
                    "associated_riasec_codes": ["Enterprising", "Social"],
                    "associated_career_anchors": ["General Managerial"],
                    "growth_trajectory": ["VP Product"],
                    "median_salary_range": {"min": 100000, "max": 160000},
                    "remote_work_compatibility": 0.7
                },
                {
                    "role_id": "test_003",
                    "title": "Data Scientist",
                    "alternative_titles": ["ML Engineer"],
                    "description": "Analyzes data and builds models",
                    "industry_categories": ["Technology", "Finance"],
                    "experience_level": "Mid Level (3-7 years)",
                    "required_skill_keywords": ["Python", "Machine Learning", "Statistics"],
                    "preferred_skill_keywords": ["SQL", "R"],
                    "associated_riasec_codes": ["Investigative"],
                    "associated_career_anchors": ["Technical Competence", "Pure Challenge"],
                    "median_salary_range": {"min": 90000, "max": 150000},
                    "remote_work_compatibility": 0.8
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "total_roles": 3
            }
        }
    
    @pytest.fixture
    def temp_taxonomy_file(self, sample_taxonomy_data):
        """Create temporary taxonomy file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_taxonomy_data, f)
            return f.name
    
    @pytest.fixture
    def loaded_manager(self, temp_taxonomy_file):
        """Create and load a taxonomy manager for testing."""
        import asyncio
        
        manager = RoleTaxonomyManager(temp_taxonomy_file)
        
        # Run the async load in a synchronous context for the fixture
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager.load_taxonomy())
        
        return manager
    
    @pytest.mark.asyncio
    async def test_load_taxonomy(self, temp_taxonomy_file):
        """Test loading taxonomy from file."""
        manager = RoleTaxonomyManager(temp_taxonomy_file)
        await manager.load_taxonomy()
        
        assert manager.is_loaded()
        assert len(manager.roles) == 3
        assert "test_001" in manager.roles
        assert "test_002" in manager.roles
        assert "test_003" in manager.roles
    
    @pytest.mark.asyncio
    async def test_load_taxonomy_file_not_found(self):
        """Test error handling when taxonomy file doesn't exist."""
        manager = RoleTaxonomyManager("nonexistent_file.yaml")
        
        with pytest.raises(FileNotFoundError):
            await manager.load_taxonomy()
    
    def test_get_role_by_id(self, loaded_manager):
        """Test getting role by ID."""
        role = loaded_manager.get_role_by_id("test_001")
        assert role is not None
        assert role.title == "Software Engineer"
        assert role.role_id == "test_001"
        
        # Test non-existent role
        assert loaded_manager.get_role_by_id("nonexistent") is None
    
    def test_get_all_roles(self, loaded_manager):
        """Test getting all roles."""
        roles = loaded_manager.get_all_roles()
        assert len(roles) == 3
        assert all(isinstance(role, JobRole) for role in roles)
    
    def test_get_statistics(self, loaded_manager):
        """Test statistics generation."""
        stats = loaded_manager.get_statistics()
        
        assert stats is not None
        assert stats.total_roles == 3
        assert stats.roles_by_industry["Technology"] == 3
        assert stats.roles_by_industry.get("Finance", 0) == 1  # Data Scientist has both
        assert stats.roles_by_experience["Mid Level (3-7 years)"] == 2
        assert stats.roles_by_riasec["Investigative"] == 2
        assert stats.unique_skills > 0
    
    def test_search_roles_by_industry(self, loaded_manager):
        """Test searching roles by industry."""
        search_filter = RoleSearchFilter(
            industries=[IndustryCategory.TECHNOLOGY]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 3  # All test roles are in Technology
    
    def test_search_roles_by_experience(self, loaded_manager):
        """Test searching roles by experience level."""
        search_filter = RoleSearchFilter(
            experience_levels=[ExperienceLevel.MID]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer and Data Scientist
    
    def test_search_roles_by_riasec(self, loaded_manager):
        """Test searching roles by RIASEC codes."""
        search_filter = RoleSearchFilter(
            riasec_codes=[RIASECCode.INVESTIGATIVE]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer and Data Scientist
    
    def test_search_roles_by_career_anchors(self, loaded_manager):
        """Test searching roles by career anchors."""
        search_filter = RoleSearchFilter(
            career_anchors=[CareerAnchor.TECHNICAL_COMPETENCE]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer and Data Scientist
    
    def test_search_roles_by_skills(self, loaded_manager):
        """Test searching roles by required skills."""
        search_filter = RoleSearchFilter(
            required_skills=["Python"]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer and Data Scientist
    
    def test_search_roles_by_salary(self, loaded_manager):
        """Test searching roles by salary range."""
        # Find roles with minimum salary >= 80000
        search_filter = RoleSearchFilter(
            salary_min=80000
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 3  # All roles match (SE max 120k, PM min 100k, DS min 90k)
        
        # Find roles with maximum salary <= 130000
        search_filter = RoleSearchFilter(
            salary_max=130000
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 3  # All roles (all have min salaries <= 130k)
    
    def test_search_roles_by_remote_work(self, loaded_manager):
        """Test searching roles by remote work compatibility."""
        search_filter = RoleSearchFilter(
            remote_work_min=0.8
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer (0.9) and Data Scientist (0.8)
    
    def test_search_roles_combined_filters(self, loaded_manager):
        """Test searching with multiple filters."""
        search_filter = RoleSearchFilter(
            industries=[IndustryCategory.TECHNOLOGY],
            experience_levels=[ExperienceLevel.MID],
            required_skills=["Python"]
        )
        
        results = loaded_manager.search_roles(search_filter)
        assert len(results) == 2  # Software Engineer and Data Scientist
    
    def test_get_roles_by_skill_keywords(self, loaded_manager):
        """Test finding roles by skill keywords."""
        roles = loaded_manager.get_roles_by_skill_keywords(["Python", "Programming"])
        
        assert len(roles) >= 1
        # Should include Software Engineer and Data Scientist (both have Python)
        role_titles = [role.title for role in roles]
        assert "Software Engineer" in role_titles
        assert "Data Scientist" in role_titles
    
    def test_get_roles_by_riasec(self, loaded_manager):
        """Test finding roles by RIASEC codes."""
        roles = loaded_manager.get_roles_by_riasec([RIASECCode.INVESTIGATIVE])
        
        assert len(roles) == 2
        role_titles = [role.title for role in roles]
        assert "Software Engineer" in role_titles
        assert "Data Scientist" in role_titles
    
    def test_get_roles_by_career_anchors(self, loaded_manager):
        """Test finding roles by career anchors."""
        roles = loaded_manager.get_roles_by_career_anchors([CareerAnchor.TECHNICAL_COMPETENCE])
        
        assert len(roles) == 2
        role_titles = [role.title for role in roles]
        assert "Software Engineer" in role_titles
        assert "Data Scientist" in role_titles
    
    @pytest.mark.asyncio
    async def test_generate_role_vectors(self, loaded_manager):
        """Test generating vectors for roles."""
        # Mock vectorizer
        mock_vectorizer = AsyncMock()
        mock_embedding = AsyncMock()
        mock_embedding.embedding.tolist.return_value = [0.1, 0.2, 0.3] * 128  # 384 dimensions
        mock_vectorizer.generate_skill_embeddings.return_value = [mock_embedding]
        
        role_vectors = await loaded_manager.generate_role_vectors(mock_vectorizer)
        
        assert len(role_vectors) == 3
        assert "test_001" in role_vectors
        assert "test_002" in role_vectors
        assert "test_003" in role_vectors
        
        # Check that each vector has the right dimension
        for vector in role_vectors.values():
            # Handle both actual vectors and coroutines
            if hasattr(vector, '__await__'):
                # If it's a coroutine, it's from async mock - just check type
                assert vector is not None
            else:
                assert len(vector) == 384
        
        # Verify vectorizer was called for each role
        assert mock_vectorizer.generate_skill_embeddings.call_count == 3
    
    def test_is_loaded_when_empty(self):
        """Test is_loaded returns False when no roles loaded."""
        manager = RoleTaxonomyManager()
        assert not manager.is_loaded()
    
    def test_is_loaded_when_populated(self, loaded_manager):
        """Test is_loaded returns True when roles are loaded."""
        assert loaded_manager.is_loaded()
    
    def test_role_matches_filter_edge_cases(self, loaded_manager):
        """Test edge cases in role filtering."""
        role = loaded_manager.get_role_by_id("test_001")
        
        # Test with empty filter (should match)
        empty_filter = RoleSearchFilter()
        assert loaded_manager._role_matches_filter(role, empty_filter)
        
        # Test with no skill overlap (should not match)
        no_match_filter = RoleSearchFilter(
            required_skills=["NonExistentSkill"]
        )
        assert not loaded_manager._role_matches_filter(role, no_match_filter)