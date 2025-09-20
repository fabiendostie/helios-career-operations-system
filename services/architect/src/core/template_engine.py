"""Template engine with Jinja2 and memory optimization for document generation."""

import os
import gc
import time
import asyncio
import tempfile
import weakref
from functools import lru_cache
from typing import Dict, Any, Optional, List
from pathlib import Path

import psutil
import structlog
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from jinja2.exceptions import TemplateError

from .config import get_settings, TEMPLATES_DIR, PERFORMANCE_THRESHOLDS

logger = structlog.get_logger(__name__)


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""
    pass


class MemoryOptimizedTemplateEngine:
    """Template engine with memory optimization patterns."""
    
    def __init__(self, max_cache_size: int = 50):
        self.settings = get_settings()
        self.max_cache_size = max_cache_size
        self._template_cache = weakref.WeakValueDictionary()
        self._template_access_count = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            auto_reload=False,  # Disable auto-reload for production
            cache_size=0,       # Disable Jinja2's internal cache (we handle caching)
            optimized=True,     # Enable template optimization
            finalize=lambda x: x if x is not None else '',  # Handle None values
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['format_duration'] = self._format_duration
        self.env.filters['join_with_comma'] = self._join_with_comma
        self.env.filters['truncate_text'] = self._truncate_text
        self.env.filters['capitalize_first'] = self._capitalize_first
        
        logger.info("Template engine initialized", max_cache_size=max_cache_size)
    
    def _format_duration(self, start_date: str, end_date: Optional[str] = None) -> str:
        """Format employment duration."""
        if not end_date or end_date.lower() == 'present':
            return f"{start_date} - Present"
        return f"{start_date} - {end_date}"
    
    def _join_with_comma(self, items: List[str], limit: int = None) -> str:
        """Join items with commas, optionally limiting count."""
        if not items:
            return ""
        
        if limit and len(items) > limit:
            items = items[:limit]
        
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"
    
    def _truncate_text(self, text: str, length: int = 200) -> str:
        """Truncate text to specified length."""
        if not text or len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + "..."
    
    def _capitalize_first(self, text: str) -> str:
        """Capitalize only the first letter."""
        if not text:
            return text
        return text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    @lru_cache(maxsize=50)
    def get_compiled_template(self, template_path: str) -> Template:
        """Get compiled template with LRU caching."""
        self._cache_misses += 1
        
        try:
            # Resolve template path
            if not os.path.isabs(template_path):
                template_path = os.path.join(TEMPLATES_DIR, template_path)
            
            # Check if template file exists
            if not os.path.exists(template_path):
                raise TemplateNotFound(f"Template not found: {template_path}")
            
            # Load and compile template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            template = self.env.from_string(template_content)
            
            logger.debug("Template compiled", template_path=template_path)
            return template
            
        except Exception as e:
            logger.error("Failed to compile template", template_path=template_path, error=str(e))
            raise TemplateRenderError(f"Template compilation failed: {e}")
    
    def record_template_cache_hit(self):
        """Record template cache hit."""
        self._cache_hits += 1
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get template cache statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / max(1, total_requests)) * 100
        cache_info = self.get_compiled_template.cache_info()
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": f"{hit_rate:.1f}%",
            "cache_size": cache_info.currsize if hasattr(cache_info, 'currsize') else 0
        }
    
    async def render_template_with_memory_management(
        self, 
        template_path: str, 
        context: Dict[str, Any],
        enable_streaming: bool = True
    ) -> str:
        """
        Render template with memory optimization strategies.
        
        Memory optimization techniques:
        1. Streaming for large documents
        2. Context data chunking  
        3. Aggressive garbage collection
        4. Temporary file usage for large renders
        """
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            template = self.get_compiled_template(template_path)
            
            # For large contexts, use streaming approach
            context_size = self._estimate_context_size(context)
            if context_size > 50:  # >50MB estimated
                logger.info("Using streaming render for large context", 
                           context_size_mb=context_size, template_path=template_path)
                return await self._render_with_streaming(template, context)
            else:
                return await self._render_standard(template, context)
                
        except MemoryError:
            # Emergency memory cleanup
            await self._emergency_memory_cleanup()
            logger.warning("Memory error during template rendering, attempting recovery")
            
            # Retry with minimal memory footprint
            return await self._render_minimal_memory(template_path, context)
        
        finally:
            # Post-render cleanup
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = final_memory - initial_memory
            
            if memory_delta > 100:  # >100MB increase
                await asyncio.sleep(0.1)  # Brief pause for GC
                gc.collect()  # Force garbage collection
                logger.info("Post-render memory cleanup", memory_delta_mb=memory_delta)
    
    def _estimate_context_size(self, context: Dict[str, Any]) -> int:
        """Estimate context size in MB."""
        try:
            size_estimate = 0
            
            for key, value in context.items():
                if isinstance(value, str):
                    size_estimate += len(value.encode('utf-8'))
                elif isinstance(value, list):
                    size_estimate += len(value) * 1000  # Rough estimate
                elif isinstance(value, dict):
                    size_estimate += len(str(value))
            
            return size_estimate / (1024 * 1024)  # Convert to MB
        except:
            return 10  # Default conservative estimate
    
    async def _render_with_streaming(
        self, 
        template: Template, 
        context: Dict[str, Any]
    ) -> str:
        """Render large templates using streaming approach."""
        try:
            # For very large contexts, use chunked rendering
            if 'work_experience' in context and len(context['work_experience']) > 10:
                # Process experience entries in batches
                experience_batches = [
                    context['work_experience'][i:i+5] 
                    for i in range(0, len(context['work_experience']), 5)
                ]
                
                rendered_chunks = []
                for batch in experience_batches:
                    batch_context = context.copy()
                    batch_context['work_experience'] = batch
                    
                    chunk = await asyncio.to_thread(template.render, batch_context)
                    rendered_chunks.append(chunk)
                    
                    # Memory cleanup after each batch
                    del chunk
                    gc.collect()
                
                # Combine chunks
                return '\n'.join(rendered_chunks)
            else:
                # Standard render for smaller contexts
                return await asyncio.to_thread(template.render, context)
            
        except Exception as e:
            logger.error(f"Streaming render failed: {e}")
            # Fallback to standard render
            return await asyncio.to_thread(template.render, context)
    
    async def _render_standard(self, template: Template, context: Dict[str, Any]) -> str:
        """Standard rendering with memory monitoring."""
        return await asyncio.to_thread(template.render, context)
    
    async def _render_minimal_memory(
        self, 
        template_path: str, 
        context: Dict[str, Any]
    ) -> str:
        """Emergency minimal memory rendering."""
        # Clear all caches
        self.get_compiled_template.cache_clear()
        gc.collect()
        
        # Use minimal context
        minimal_context = {
            'candidate_name': context.get('candidate_name', 'Professional'),
            'email': context.get('email', ''),
            'phone': context.get('phone', ''),
            'work_experience': context.get('work_experience', [])[:3],  # Limit to 3 jobs
            'education': context.get('education', [])[:2],  # Limit to 2 education entries
            'core_skills': context.get('core_skills', [])[:10]  # Limit skills
        }
        
        template = self.get_compiled_template(template_path)
        return await asyncio.to_thread(template.render, minimal_context)
    
    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup procedures."""
        # Clear template cache
        self.get_compiled_template.cache_clear()
        self._template_cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Brief pause to allow memory reclamation
        await asyncio.sleep(0.5)
        
        logger.warning("Emergency memory cleanup executed")
    
    async def warm_cache(self, template_paths: Optional[List[str]] = None):
        """Warm up template cache with common templates."""
        if not template_paths:
            # Default templates to warm
            template_paths = [
                "resume/t_shaped_classic.j2",
                "resume/t_shaped_modern.j2",
                "resume/t_shaped_minimal.j2",
                "cover_letter/pain_promise.j2"
            ]
        
        logger.info("Warming template cache", template_count=len(template_paths))
        
        for template_path in template_paths:
            try:
                self.get_compiled_template(template_path)
                logger.debug("Template warmed", template_path=template_path)
            except Exception as e:
                logger.warning("Failed to warm template", 
                              template_path=template_path, error=str(e))
        
        cache_stats = self.get_cache_stats()
        logger.info("Template cache warmed", **cache_stats)
    
    async def clear_cache(self):
        """Clear template cache."""
        self.get_compiled_template.cache_clear()
        self._template_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Template cache cleared")


class TemplateEngine:
    """High-level template engine interface."""
    
    def __init__(self):
        self.settings = get_settings()
        self._memory_engine = MemoryOptimizedTemplateEngine(
            max_cache_size=self.settings.template_cache_size
        )
        self._last_cleanup = time.time()
        
        logger.info("Template engine initialized")
    
    async def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Generic template rendering method."""
        return await self._memory_engine.render_template_with_memory_management(
            template_path, context
        )
    
    async def render_resume_template(
        self,
        template_name: str,
        career_data: Dict[str, Any],
        job_requirements: Optional[Dict[str, Any]] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render resume template with career data."""
        # Prepare template context
        context = self._prepare_resume_context(
            career_data, job_requirements, customizations
        )
        
        # Determine template path
        template_path = f"resume/{template_name}.j2"
        
        # Render template
        start_time = time.time()
        
        try:
            rendered_content = await self._memory_engine.render_template_with_memory_management(
                template_path, context
            )
            
            render_time = time.time() - start_time
            
            # Log performance warning if needed
            if render_time > PERFORMANCE_THRESHOLDS["generation_time_warning"]:
                logger.warning(
                    "Slow template rendering",
                    template_name=template_name,
                    render_time=render_time
                )
            
            logger.info(
                "Resume template rendered",
                template_name=template_name,
                render_time=render_time,
                context_keys=list(context.keys())
            )
            
            return rendered_content
            
        except Exception as e:
            logger.error(
                "Resume template rendering failed",
                template_name=template_name,
                error=str(e),
                exc_info=True
            )
            raise TemplateRenderError(f"Failed to render resume template: {e}")
    
    async def render_cover_letter_template(
        self,
        template_name: str,
        career_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render cover letter template with career and job data."""
        # Prepare template context
        context = self._prepare_cover_letter_context(
            career_data, job_requirements, company_data
        )
        
        # Determine template path
        template_path = f"cover_letter/{template_name}.j2"
        
        # Render template
        start_time = time.time()
        
        try:
            rendered_content = await self._memory_engine.render_template_with_memory_management(
                template_path, context
            )
            
            render_time = time.time() - start_time
            
            logger.info(
                "Cover letter template rendered",
                template_name=template_name,
                render_time=render_time
            )
            
            return rendered_content
            
        except Exception as e:
            logger.error(
                "Cover letter template rendering failed",
                template_name=template_name,
                error=str(e),
                exc_info=True
            )
            raise TemplateRenderError(f"Failed to render cover letter template: {e}")
    
    def _prepare_resume_context(
        self,
        career_data: Dict[str, Any],
        job_requirements: Optional[Dict[str, Any]] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare context for resume template rendering."""
        # Extract basic information
        context = {
            'candidate_name': career_data.get('candidate_name', 'Professional'),
            'email': career_data.get('email', ''),
            'phone': career_data.get('phone', ''),
            'location': career_data.get('location', ''),
            'linkedin': career_data.get('linkedin', ''),
            'website': career_data.get('website', ''),
        }
        
        # Add work experience
        work_experience = career_data.get('work_experience', [])
        context['work_experience'] = work_experience
        context['years_experience'] = self._calculate_years_experience(work_experience)
        
        # Add education
        context['education'] = career_data.get('education', [])
        
        # Add skills
        skills_inventory = career_data.get('skills_inventory', {})
        context['core_skills'] = self._extract_core_skills(skills_inventory)
        context['technical_skills'] = skills_inventory.get('technical_skills', {})
        context['soft_skills'] = skills_inventory.get('soft_skills', [])
        
        # Add strategic metadata for T-shaped summary
        strategic_metadata = career_data.get('strategic_metadata', {})
        context['core_competencies'] = strategic_metadata.get('core_competencies', [])
        context['quantified_achievements'] = strategic_metadata.get('quantified_achievements', [])
        
        # T-shaped resume specific fields
        context.update(self._prepare_t_shaped_context(career_data, job_requirements))
        
        # Apply customizations
        if customizations:
            context.update(customizations)
        
        return context
    
    def _prepare_cover_letter_context(
        self,
        career_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare context for cover letter template rendering."""
        context = {
            'candidate_name': career_data.get('candidate_name', 'Professional'),
            'email': career_data.get('email', ''),
            'phone': career_data.get('phone', ''),
            'current_date': time.strftime("%B %d, %Y"),
            
            # Job and company information
            'role_title': job_requirements.get('role_title', 'Position'),
            'company_name': job_requirements.get('company', 'Company'),
            'hiring_manager_name': job_requirements.get('hiring_manager', ''),
            
            # Company data
            'company_address': company_data.get('address', '') if company_data else '',
        }
        
        # Pain & Promise specific context
        context.update(self._prepare_pain_promise_context(career_data, job_requirements, company_data))
        
        return context
    
    def _prepare_t_shaped_context(
        self,
        career_data: Dict[str, Any],
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare T-shaped resume specific context fields."""
        # Determine target role from job requirements or career data
        target_role = "Professional"
        if job_requirements:
            target_role = job_requirements.get('role_title', target_role)
        
        # Select appropriate adjective based on experience level
        years_exp = self._calculate_years_experience(career_data.get('work_experience', []))
        adjective = self._select_adjective_by_experience(years_exp)
        
        # Extract core competencies (limit to top 3)
        strategic_metadata = career_data.get('strategic_metadata', {})
        core_competencies = strategic_metadata.get('core_competencies', [])[:3]
        
        # Get top quantified achievement
        achievements = strategic_metadata.get('quantified_achievements', [])
        top_achievement = achievements[0] if achievements else "delivered exceptional results"
        
        # Extract primary skill area
        skills_inventory = career_data.get('skills_inventory', {})
        technical_skills = skills_inventory.get('technical_skills', {})
        primary_skill_area = list(technical_skills.keys())[0] if technical_skills else "technology"
        
        return {
            'target_role_title': target_role,
            'adjective': adjective,
            'years_experience': years_exp,
            'core_competency_1': core_competencies[0] if len(core_competencies) > 0 else "expertise",
            'core_competency_2': core_competencies[1] if len(core_competencies) > 1 else "leadership",
            'core_technology': core_competencies[2] if len(core_competencies) > 2 else "innovation",
            'top_quantified_achievement': top_achievement,
            'skill_area': primary_skill_area,
        }
    
    def _prepare_pain_promise_context(
        self,
        career_data: Dict[str, Any],
        job_requirements: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare Pain & Promise cover letter specific context."""
        # Get top achievement for promise paragraph
        strategic_metadata = career_data.get('strategic_metadata', {})
        achievements = strategic_metadata.get('quantified_achievements', [])
        top_achievement = achievements[0] if achievements else "delivered significant results"
        
        # Extract relevant experience for bridge
        work_experience = career_data.get('work_experience', [])
        previous_company = work_experience[0]['company_name'] if work_experience else "previous role"
        
        # Get core competencies for skills demonstration
        core_competencies = strategic_metadata.get('core_competencies', [])
        primary_competency = core_competencies[0] if core_competencies else "expertise"
        
        return {
            # Pain identification (to be customized based on company research)
            'company_challenge_context': "recent growth and market expansion",
            'inferred_pain_point': "scaling operations efficiently while maintaining quality",
            'specific_challenge_detail': "implementing robust systems and processes",
            
            # Skills bridge
            'key_skill_1': primary_competency,
            'key_skill_2': core_competencies[1] if len(core_competencies) > 1 else "leadership",
            
            # Promise demonstration
            'top_quantified_achievement': top_achievement,
            'previous_company': previous_company,
            'specific_metric': "measurable improvements in efficiency and performance",
            'relevant_skill_area': primary_competency,
            'connection_to_pain_point': "addressing similar operational challenges",
            'core_competency': primary_competency,
            'success_pattern': "consistent value delivery",
            'target_audience': "growing organizations",
            
            # Close
            'primary_skill_area': primary_competency,
            'specialization_area': core_competencies[0] if core_competencies else "strategic implementation",
        }
    
    def _calculate_years_experience(self, work_experience: List[Dict[str, Any]]) -> int:
        """Calculate total years of experience from work history."""
        if not work_experience:
            return 0
        
        # Simple calculation - count number of positions (rough estimate)
        # In practice, would parse dates properly
        return min(len(work_experience) * 2, 20)  # Cap at 20 years
    
    def _select_adjective_by_experience(self, years: int) -> str:
        """Select appropriate adjective based on experience level."""
        if years < 3:
            return "Motivated"
        elif years < 7:
            return "Experienced" 
        elif years < 12:
            return "Senior"
        else:
            return "Strategic"
    
    def _extract_core_skills(self, skills_inventory: Dict[str, Any]) -> List[str]:
        """Extract core skills from skills inventory."""
        core_skills = []
        
        # Get technical skills
        technical_skills = skills_inventory.get('technical_skills', {})
        for category, skills in technical_skills.items():
            if isinstance(skills, list):
                core_skills.extend(skills[:3])  # Top 3 from each category
        
        # Add soft skills
        soft_skills = skills_inventory.get('soft_skills', [])
        core_skills.extend(soft_skills[:3])
        
        # Return top 8 skills for ATS optimization
        return core_skills[:8]
    
    async def warm_cache(self):
        """Warm up template cache."""
        await self._memory_engine.warm_cache()
    
    async def clear_cache(self):
        """Clear template cache."""
        await self._memory_engine.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get template cache statistics."""
        return self._memory_engine.get_cache_stats()