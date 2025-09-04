"""
Main entry point for the Intelligent Resume Data Extractor CLI application.
"""

import argparse
import sys
from pathlib import Path

from resume_extractor.pipeline import Pipeline
from resume_extractor.utils.logging_config import setup_logging


def main() -> None:
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Extract and consolidate resume data from multiple formats"
    )
    parser.add_argument(
        "directory", type=str, help="Directory containing resume files to process"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="master_career_database.json",
        help="Output file name (default: master_career_database.json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Validate input directory
    input_dir = Path(args.directory)
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' does not exist.")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a directory.")
        sys.exit(1)

    # Initialize and run pipeline
    try:
        pipeline = Pipeline(input_directory=input_dir, output_file=args.output)
        pipeline.run()
        print(f"Successfully created {args.output}")
    except Exception as e:
        print(f"Error processing resumes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
