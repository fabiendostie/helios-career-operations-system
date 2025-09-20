"""
Advanced NLP Processing Pipeline for Dynamic Research Engine
Implements semantic analysis using spaCy and Transformers
"""

import spacy
from transformers import pipeline
import structlog
from typing import Dict, List, Any
import asyncio
import functools
import torch

logger = structlog.get_logger(__name__)

class AdvancedNLPProcessor:
    """
    Production-grade NLP processor for semantic analysis of research content
    """
    
    def __init__(self):
        self.nlp_model = None
        self.summarizer = None
        self.classifier = None
        self.sentiment_analyzer = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all NLP models asynchronously"""
        if self._initialized:
            return
            
        logger.info("Initializing advanced NLP models...")
        
        # Load spaCy model for NER and text processing
        try:
            self.nlp_model = spacy.load("en_core_web_lg")
            logger.info("spaCy large model loaded successfully")
        except OSError:
            logger.warning("en_core_web_lg not found, falling back to en_core_web_sm")
            self.nlp_model = spacy.load("en_core_web_sm")
        
        # Initialize Transformers pipelines
        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")
        
        # Summarization pipeline
        self.summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn",
            device=device,
            max_length=150,
            min_length=30,
            do_sample=False
        )
        
        # Zero-shot classification pipeline
        self.classifier = pipeline(
            "zero-shot-classification", 
            model="facebook/bart-large-mnli",
            device=device
        )
        
        # Sentiment analysis pipeline
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=device
        )
        
        self._initialized = True
        logger.info("All NLP models initialized successfully")
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using spaCy
        Returns organized entities by type
        """
        if not self._initialized:
            await self.initialize()
            
        # Run spaCy processing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp_model, text)
        
        entities = {
            "PERSON": [],
            "ORG": [],
            "PRODUCT": [],
            "GPE": [],  # Geopolitical Entity
            "MONEY": [],
            "PERCENT": [],
            "DATE": [],
            "TECH_SKILLS": [],  # Custom category
            "BUSINESS_TERMS": []  # Custom category
        }
        
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text.strip())
            elif ent.label_ in ["PRODUCT", "EVENT"]:
                # Classify as potential tech skills or business terms
                text_lower = ent.text.lower()
                if any(tech_word in text_lower for tech_word in 
                      ["python", "aws", "docker", "kubernetes", "ai", "ml", "api", "cloud"]):
                    entities["TECH_SKILLS"].append(ent.text.strip())
                else:
                    entities["BUSINESS_TERMS"].append(ent.text.strip())
        
        # Remove duplicates and empty strings
        for key in entities:
            entities[key] = list(set([item for item in entities[key] if item.strip()]))
        
        return entities
    
    async def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Generate abstractive summary using BART model
        """
        if not self._initialized:
            await self.initialize()
            
        # Truncate text if too long (BART has token limits)
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        try:
            loop = asyncio.get_event_loop()
            summary_result = await loop.run_in_executor(
                None, 
                functools.partial(
                    self.summarizer, 
                    text, 
                    max_length=max_length, 
                    min_length=max(30, max_length // 5)
                )
            )
            return summary_result[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Fallback to simple truncation
            return text[:max_length] + "..." if len(text) > max_length else text
    
    async def classify_content(self, text: str, labels: List[str]) -> Dict[str, float]:
        """
        Classify text against dynamic list of labels using zero-shot classification
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                functools.partial(self.classifier, text, candidate_labels=labels)
            )
            return dict(zip(result['labels'], result['scores']))
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Return uniform distribution as fallback
            return {label: 1.0 / len(labels) for label in labels}
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text content
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.sentiment_analyzer, text)
            
            # Convert to standardized format
            sentiment_map = {
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral', 
                'LABEL_2': 'positive'
            }
            
            label = result[0]['label']
            score = result[0]['score']
            
            return {
                'sentiment': sentiment_map.get(label, label.lower()),
                'confidence': score,
                'raw_result': result[0]
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'raw_result': None
            }
    
    async def extract_skills_and_trends(self, text: str) -> Dict[str, Any]:
        """
        Advanced skill and trend extraction using combined NLP techniques
        """
        if not self._initialized:
            await self.initialize()
        
        # Industry-specific skill categories for classification
        skill_categories = [
            "programming_languages",
            "cloud_platforms", 
            "data_analysis",
            "project_management",
            "leadership",
            "communication",
            "technical_architecture",
            "machine_learning",
            "cybersecurity",
            "business_strategy"
        ]
        
        # Extract entities first
        entities = await self.extract_entities(text)
        
        # Classify content by skill categories
        skill_classification = await self.classify_content(text, skill_categories)
        
        # Extract trending keywords using spaCy
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp_model, text)
        
        # Extract meaningful phrases (noun chunks and compound words)
        trending_terms = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2 and len(chunk.text) < 50:
                trending_terms.append(chunk.text.strip())
        
        # Extract technical terms based on POS patterns
        technical_patterns = []
        for token in doc:
            # Look for capitalized technical terms
            if (token.pos_ in ["NOUN", "PROPN"] and 
                token.text[0].isupper() and 
                len(token.text) > 2):
                technical_patterns.append(token.text)
        
        return {
            "extracted_entities": entities,
            "skill_categories": skill_classification,
            "trending_terms": list(set(trending_terms))[:10],  # Top 10
            "technical_terms": list(set(technical_patterns))[:15],  # Top 15
            "confidence_score": sum(skill_classification.values()) / len(skill_classification)
        }

# Global instance for reuse
_nlp_processor = AdvancedNLPProcessor()

async def get_nlp_processor() -> AdvancedNLPProcessor:
    """Get initialized NLP processor instance"""
    if not _nlp_processor._initialized:
        await _nlp_processor.initialize()
    return _nlp_processor