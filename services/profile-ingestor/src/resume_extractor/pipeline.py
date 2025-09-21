"""
Pipeline orchestration for the resume extraction process.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from resume_extractor.components.ingestion import IngestionEngine
from resume_extractor.components.parsing import ParsingService
from resume_extractor.components.consolidation import ConsolidationEngine
from resume_extractor.schemas.master_schema import MasterCareerDatabase
from resume_extractor.ui.conflict_resolver import ConflictResolverUI
from resume_extractor.ui.elicitation import ElicitationUI


logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline for processing resume files."""

    def __init__(self, input_directory: Path, output_file: str):
        """Initialize pipeline with input directory and output file."""
        self.input_directory = input_directory
        self.output_file = output_file

        # Initialize components
        self.ingestion_engine = IngestionEngine()
        self.parsing_service = ParsingService()
        self.consolidation_engine = ConsolidationEngine()
        self.conflict_resolver = ConflictResolverUI()
        self.elicitation_ui = ElicitationUI()

        logger.info(f"Pipeline initialized for directory: {input_directory}")

    def run(self) -> None:
        """Execute the complete resume extraction pipeline."""
        logger.info("Starting resume extraction pipeline")

        # Step 1: File Ingestion
        logger.info("Step 1: Ingesting files")
        documents = self.ingestion_engine.ingest_files(self.input_directory)
        logger.info(f"Ingested {len(documents)} documents")

        # Step 2: Language Detection and NLP Parsing
        logger.info("Step 2: Parsing documents")
        parsed_data: List[Dict[str, Any]] = []
        for document in documents:
            data = self.parsing_service.parse_document(document)
            parsed_data.append(data)

        # Step 3: Data Consolidation
        logger.info("Step 3: Consolidating data")
        consolidated_data, conflicts = self.consolidation_engine.consolidate(
            parsed_data
        )

        # Step 4: Interactive Conflict Resolution
        if conflicts:
            logger.info("Step 4: Resolving conflicts")
            resolved_data = self.conflict_resolver.resolve_conflicts_legacy(
                consolidated_data, conflicts
            )
        else:
            resolved_data = consolidated_data

        # Step 5: Interactive Elicitation
        logger.info("Step 5: Conducting interactive interview")
        elicited_info = self.elicitation_ui.conduct_interview(resolved_data)

        # Merge elicited info into final data
        final_data = resolved_data.copy()
        final_data["holistic_profile"] = elicited_info

        # Step 6: Generate Master Career Database
        logger.info("Step 6: Generating master database")
        master_db = MasterCareerDatabase.from_dict(final_data)

        # Step 7: Write output
        self._write_output(master_db.to_dict())

        logger.info("Pipeline completed successfully")

    def _write_output(self, data: Dict[str, Any]) -> None:
        """Write the final data to JSON file."""
        import json

        output_path = Path(self.output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Output written to: {output_path}")
