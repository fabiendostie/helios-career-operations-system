"""
NLP parsing service for extracting structured data from documents.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import spacy
from spacy.lang.en import English
from spacy.lang.fr import French
from spacy.matcher import Matcher

from resume_extractor.components.ingestion import Document
from resume_extractor.schemas.master_schema import WorkExperience, Project, Education


logger = logging.getLogger(__name__)


@dataclass
class ParsedData:
    """Container for parsed document data."""
    work_experiences: List[WorkExperience]
    projects: List[Project]
    skills: List[str]
    education: List[Education]
    contact_info: Dict[str, str]
    raw_entities: Dict[str, Any]
    language: str
    source_file: str


@dataclass
class Conflict:
    """Represents a conflict between parsed data from different documents."""
    field: str
    entity_id: str
    variations: List[Any]
    sources: List[str]


class ParsingService:
    """Singleton service for NLP parsing using spaCy models."""

    _instance = None
    _models = {}

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the parsing service with spaCy models."""
        if not self._initialized:
            self.en_nlp: Optional[English] = None
            self.fr_nlp: Optional[French] = None
            self._load_models()
            self._setup_matchers()
            self._initialized = True

    def _load_models(self) -> None:
        """Load spaCy language models once at startup."""
        try:
            self._models['en'] = spacy.load("en_core_web_trf")
            logger.info("Loaded English transformer spaCy model")
        except OSError:
            try:
                self._models['en'] = spacy.load("en_core_web_sm")
                logger.info("Loaded English small spaCy model as fallback")
            except OSError:
                logger.warning("English spaCy model not available")

        try:
            self._models['fr'] = spacy.load("fr_dep_news_trf")
            logger.info("Loaded French transformer spaCy model")
        except OSError:
            try:
                self._models['fr'] = spacy.load("fr_core_news_sm")
                logger.info("Loaded French small spaCy model as fallback")
            except OSError:
                logger.warning("French spaCy model not available")

    def _setup_matchers(self) -> None:
        """Setup pattern matchers for both languages."""
        self.en_matcher = Matcher(self._models.get('en', spacy.blank('en')).vocab) if 'en' in self._models else None
        self.fr_matcher = Matcher(self._models.get('fr', spacy.blank('fr')).vocab) if 'fr' in self._models else None

        # Add patterns for job titles, skills, etc.
        if self.en_matcher:
            self._add_english_patterns()
        if self.fr_matcher:
            self._add_french_patterns()

    def _add_english_patterns(self) -> None:
        """Add English-specific patterns."""
        # Job title patterns
        job_patterns = [
            [{"LOWER": {"IN": ["senior", "junior", "lead", "principal", "chief", "head"]}}, {"POS": "NOUN", "OP": "+"}],
            [{"POS": "NOUN"}, {"LOWER": {"IN": ["engineer", "developer", "manager", "analyst", "consultant", "architect"]}}],
            [{"LOWER": "software"}, {"LOWER": {"IN": ["engineer", "developer", "architect"]}}]
        ]
        for i, pattern in enumerate(job_patterns):
            self.en_matcher.add(f"JOB_TITLE_{i}", [pattern])

    def _add_french_patterns(self) -> None:
        """Add French-specific patterns."""
        # Job title patterns
        job_patterns = [
            [{"LOWER": {"IN": ["ingénieur", "développeur", "chef", "responsable", "directeur"]}}, {"POS": "NOUN", "OP": "?"}],
            [{"LOWER": "chef"}, {"LOWER": "de"}, {"LOWER": "projet"}],
            [{"LOWER": "ingénieur"}, {"LOWER": "logiciel"}]
        ]
        for i, pattern in enumerate(job_patterns):
            self.fr_matcher.add(f"JOB_TITLE_{i}", [pattern])

    def parse_document(self, document: Document) -> ParsedData:
        """Parse document using appropriate language model."""
        logger.info(f"Starting parse of document: {document.file_path.name} ({len(document.content)} chars)")
        start_time = datetime.now()

        # Detect language
        language = self._detect_language(document.content)
        logger.debug(f"Detected language: {language}")

        # Select appropriate NLP model
        model = self._models.get(language)
        if model is None:
            logger.warning(f"No NLP model available for language: {language}")
            return self._create_empty_parsed_data(document, language)

        logger.debug(f"Using {language} spaCy model: {model.meta.get('name', 'unknown')}")

        # Process document with performance limit
        content = document.content[:1000000]  # Limit to 1M chars
        if len(document.content) > 1000000:
            logger.warning(f"Document content truncated from {len(document.content)} to 1000000 chars")

        # Run NLP processing
        nlp_start = datetime.now()
        doc = model(content)
        nlp_time = (datetime.now() - nlp_start).total_seconds()
        logger.debug(f"NLP processing completed in {nlp_time:.3f} seconds")

        # Log entity extraction results
        entity_counts = {}
        for ent in doc.ents:
            entity_counts[ent.label_] = entity_counts.get(ent.label_, 0) + 1
        logger.debug(f"Extracted entities: {entity_counts}")

        # Extract structured data with individual timing
        extraction_start = datetime.now()

        work_experiences = self._extract_work_experience(doc, language)
        projects = self._extract_projects(doc, language)
        skills = self._extract_skills(doc, language)
        education = self._extract_education(doc, language)
        contact_info = self._extract_contact(doc)

        extraction_time = (datetime.now() - extraction_start).total_seconds()
        logger.debug(f"Data extraction completed in {extraction_time:.3f} seconds")

        # Log extraction results
        logger.info(f"Extraction results - Work experiences: {len(work_experiences)}, "
                   f"Projects: {len(projects)}, Skills: {len(skills)}, "
                   f"Education: {len(education)}, Contact fields: {len(contact_info)}")

        parsed_data = ParsedData(
            work_experiences=work_experiences,
            projects=projects,
            skills=skills,
            education=education,
            contact_info=contact_info,
            raw_entities={ent.text: ent.label_ for ent in doc.ents},
            language=language,
            source_file=str(document.file_path)
        )

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Document parsing completed in {processing_time:.2f} seconds")

        return parsed_data

    def _detect_language(self, text: str) -> str:
        """Detect if text is English or French."""
        # Simple heuristic - count common words
        sample_text = text[:1000].lower()

        english_words = ["the", "and", "of", "to", "a", "in", "for", "is", "on", "that"]
        french_words = ["le", "de", "et", "à", "un", "il", "être", "et", "en", "avoir"]

        en_count = sum(1 for word in english_words if word in sample_text)
        fr_count = sum(1 for word in french_words if word in sample_text)

        return "fr" if fr_count > en_count else "en"

    def _create_empty_parsed_data(self, document: Document, language: str) -> ParsedData:
        """Create empty parsed data when NLP models are not available."""
        return ParsedData(
            work_experiences=[],
            projects=[],
            skills=[],
            education=[],
            contact_info={},
            raw_entities={},
            language=language,
            source_file=str(document.file_path)
        )

    def _extract_work_experience(self, doc, language: str) -> List[WorkExperience]:
        """Extract job roles, companies, dates, and descriptions."""
        logger.debug(f"Starting work experience extraction for {language} document")
        experiences = []

        # Extract organizations (potential employers)
        organizations = [ent for ent in doc.ents if ent.label_ in ["ORG", "ORGANIZATION"]]
        logger.debug(f"Found {len(organizations)} organization entities: {[org.text for org in organizations]}")

        # Extract dates
        dates = [ent for ent in doc.ents if ent.label_ in ["DATE", "TIME"]]
        logger.debug(f"Found {len(dates)} date entities: {[date.text for date in dates]}")

        # Get job title matches using patterns
        matcher = self.en_matcher if language == 'en' else self.fr_matcher
        job_matches = matcher(doc) if matcher else []
        logger.debug(f"Found {len(job_matches)} job title pattern matches")

        # Simple extraction - match orgs with nearby job titles and dates
        for org in organizations[:10]:  # Limit to prevent over-extraction
            # Find nearby job titles and dates (within 100 characters)
            org_start, org_end = org.start_char, org.end_char

            nearby_jobs = []
            for match_id, start, end in job_matches:
                job_start, job_end = doc[start].start_char, doc[end-1].end_char
                if abs(job_start - org_end) < 100 or abs(org_start - job_end) < 100:
                    nearby_jobs.append(doc[start:end].text)

            nearby_dates = []
            for date_ent in dates:
                if abs(date_ent.start_char - org_end) < 200:
                    nearby_dates.append(date_ent.text)

            # Create work experience entry
            role = nearby_jobs[0] if nearby_jobs else "Unknown Role"
            duration = nearby_dates[0] if nearby_dates else "Unknown Duration"

            experiences.append(WorkExperience(
                company=org.text.strip(),
                role=role.strip(),
                duration=duration.strip(),
                description=None,
                accomplishments=None,
                technologies=None
            ))

        return experiences

    def _extract_skills(self, doc, language: str) -> List[str]:
        """Extract technical and soft skills with deduplication."""
        logger.debug(f"Starting skills extraction for {language} document")
        skills = set()  # Use set for automatic deduplication

        # Technical skills patterns
        tech_keywords = {
            'en': ['python', 'java', 'javascript', 'react', 'angular', 'vue', 'django', 'flask', 'sql', 'mongodb', 'aws', 'docker', 'kubernetes'],
            'fr': ['python', 'java', 'javascript', 'react', 'angular', 'vue', 'django', 'flask', 'sql', 'mongodb', 'aws', 'docker', 'kubernetes']
        }

        # Extract skills from entities
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "TECHNOLOGY", "ORG"]:
                skill_text = ent.text.lower().strip()
                if len(skill_text) > 1 and skill_text.isalpha():
                    skills.add(skill_text)

        # Extract skills using keyword matching
        text_lower = doc.text.lower()
        for keyword in tech_keywords.get(language, tech_keywords['en']):
            if keyword in text_lower:
                skills.add(keyword)

        # Extract multi-word skills using noun phrases
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            if len(chunk_text.split()) <= 3 and any(tech in chunk_text for tech in tech_keywords.get(language, tech_keywords['en'])):
                skills.add(chunk_text)

        final_skills = list(skills)[:50]  # Limit to 50 skills
        logger.debug(f"Extracted skills (after deduplication): {final_skills}")
        return final_skills

    def _extract_projects(self, doc, language: str) -> List[Project]:
        """Extract project names, descriptions, and outcomes."""
        projects = []

        # Look for project section headers
        project_keywords = {
            'en': ['project', 'projects', 'work', 'portfolio', 'application', 'system'],
            'fr': ['projet', 'projets', 'travail', 'portfolio', 'application', 'système']
        }

        # Simple extraction based on sentence structure
        sentences = list(doc.sents)

        for i, sent in enumerate(sentences):
            sent_lower = sent.text.lower()

            # Check if sentence contains project keywords
            if any(keyword in sent_lower for keyword in project_keywords.get(language, project_keywords['en'])):
                project_name = sent.text.strip()[:100]  # First 100 chars as name

                # Get description from next few sentences
                description_parts = []
                for j in range(i+1, min(i+4, len(sentences))):
                    next_sent = sentences[j].text.strip()
                    if len(next_sent) > 10:
                        description_parts.append(next_sent)

                description = ' '.join(description_parts)[:500] if description_parts else "No description available"

                projects.append(Project(
                    name=project_name,
                    description=description,
                    technologies=None,
                    url=None,
                    impact=None
                ))

                if len(projects) >= 10:  # Limit to 10 projects
                    break

        return projects

    def _extract_education(self, doc, language: str) -> List[Education]:
        """Extract education information."""
        education_entries = []

        # Education keywords
        edu_keywords = {
            'en': ['university', 'college', 'school', 'degree', 'bachelor', 'master', 'phd', 'diploma', 'certification'],
            'fr': ['université', 'école', 'diplôme', 'licence', 'master', 'doctorat', 'certification', 'formation']
        }

        # Extract educational institutions
        institutions = [ent for ent in doc.ents if ent.label_ in ["ORG", "ORGANIZATION"] and
                      any(keyword in ent.text.lower() for keyword in edu_keywords.get(language, edu_keywords['en']))]

        for inst in institutions[:5]:  # Limit to 5 institutions
            education_entries.append(Education(
                institution=inst.text.strip(),
                degree="Unknown Degree",
                field=None,
                year=None,
                gpa=None
            ))

        return education_entries

    def _extract_contact(self, doc) -> Dict[str, str]:
        """Extract contact information."""
        contact_info = {}

        # Extract email addresses using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, doc.text)
        if emails:
            contact_info['email'] = emails[0]

        # Extract phone numbers using regex
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b'
        phones = re.findall(phone_pattern, doc.text)
        if phones:
            contact_info['phone'] = phones[0]

        # Extract person names
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if persons:
            contact_info['name'] = persons[0]

        return contact_info


class ConflictDetector:
    """Detects conflicts between parsed documents."""

    def find_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Identify conflicting information across documents."""
        logger.info(f"Starting conflict detection across {len(parsed_data_list)} documents")
        conflicts = []

        if len(parsed_data_list) < 2:
            logger.debug("Less than 2 documents provided, no conflicts possible")
            return conflicts

        # Check work experience conflicts
        conflicts.extend(self._find_work_experience_conflicts(parsed_data_list))

        # Check project conflicts
        conflicts.extend(self._find_project_conflicts(parsed_data_list))

        # Check skills conflicts (duplicates)
        conflicts.extend(self._find_skill_conflicts(parsed_data_list))

        logger.info(f"Conflict detection completed - found {len(conflicts)} conflicts")
        for conflict in conflicts:
            logger.debug(f"Conflict in {conflict.field} for {conflict.entity_id}: {conflict.variations}")

        return conflicts

    def _find_work_experience_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Find conflicts in work experience data."""
        conflicts = []
        company_role_map = {}

        for parsed_data in parsed_data_list:
            for exp in parsed_data.work_experiences:
                key = f"{exp.company}-{exp.role}"
                if key not in company_role_map:
                    company_role_map[key] = []
                company_role_map[key].append((exp, parsed_data.source_file))

        # Find conflicts where same company+role has different durations
        for key, experiences in company_role_map.items():
            if len(experiences) > 1:
                durations = [exp[0].duration for exp in experiences]
                sources = [exp[1] for exp in experiences]

                if len(set(durations)) > 1:  # Different durations found
                    conflicts.append(Conflict(
                        field="work_experience.duration",
                        entity_id=key,
                        variations=durations,
                        sources=sources
                    ))

        return conflicts

    def _find_project_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Find conflicts in project data."""
        conflicts = []
        project_map = {}

        for parsed_data in parsed_data_list:
            for proj in parsed_data.projects:
                # Use first few words as key for similar projects
                key = ' '.join(proj.name.split()[:3]).lower()
                if key not in project_map:
                    project_map[key] = []
                project_map[key].append((proj, parsed_data.source_file))

        # Find projects with similar names but different descriptions
        for key, projects in project_map.items():
            if len(projects) > 1:
                descriptions = [proj[0].description for proj in projects]
                sources = [proj[1] for proj in projects]

                if len(set(descriptions)) > 1:
                    conflicts.append(Conflict(
                        field="project.description",
                        entity_id=key,
                        variations=descriptions,
                        sources=sources
                    ))

        return conflicts

    def _find_skill_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Find skill duplicates and variations."""
        conflicts = []
        all_skills = []

        for parsed_data in parsed_data_list:
            all_skills.extend([(skill, parsed_data.source_file) for skill in parsed_data.skills])

        # Group similar skills
        skill_groups = {}
        for skill, source in all_skills:
            skill_lower = skill.lower()
            found_group = False

            for group_key in skill_groups:
                if skill_lower in group_key or group_key in skill_lower:
                    skill_groups[group_key].append((skill, source))
                    found_group = True
                    break

            if not found_group:
                skill_groups[skill_lower] = [(skill, source)]

        # Find groups with variations
        for group_key, skills in skill_groups.items():
            if len(skills) > 1:
                unique_skills = list(set([s[0] for s in skills]))
                if len(unique_skills) > 1:
                    conflicts.append(Conflict(
                        field="skills",
                        entity_id=group_key,
                        variations=unique_skills,
                        sources=[s[1] for s in skills]
                    ))

        return conflicts
