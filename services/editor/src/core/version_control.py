"""Version control system for tracking text changes."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict
import difflib
import threading

from .config import settings
from ..models.version_control import (
    Version, VersionHistory, ChangeLog, TextDiff, DiffOperation, VersionComparison
)

logger = logging.getLogger(__name__)


class VersionController:
    """Manages version control for text editing sessions."""

    def __init__(self):
        """Initialize the version controller."""
        self.versions: Dict[str, List[Version]] = {}  # session_id -> versions
        self.max_versions = getattr(settings, 'MAX_VERSIONS', 10)
        self._lock = threading.RLock()

    def create_version(self, session_id: str, text: str, edit_type: str,
                      comment: Optional[str] = None, author: str = "system") -> Version:
        """Create a new version for the given session."""
        if not session_id or session_id.strip() == "":
            raise ValueError("Session ID cannot be empty")

        if not text or text.strip() == "":
            raise ValueError("Text cannot be empty")

        with self._lock:
            # Get existing versions for this session
            session_versions = self.versions.get(session_id, [])

            # Determine version number
            version_number = len(session_versions) + 1

            # Get parent version ID
            parent_version_id = None
            if session_versions:
                # Mark previous current version as not current
                for v in session_versions:
                    v.is_current = False
                parent_version_id = session_versions[-1].version_id

            # Calculate quality score (placeholder - could be enhanced)
            quality_score = self._calculate_quality_score(text)

            # Create new version
            version = Version(
                version_id=str(uuid.uuid4()),
                session_id=session_id,
                version_number=version_number,
                text=text,
                comment=comment,
                author=author,
                edit_type=edit_type,
                quality_score=quality_score,
                word_count=len(text.split()),
                character_count=len(text),
                parent_version_id=parent_version_id,
                is_current=True
            )

            # Add to session versions
            if session_id not in self.versions:
                self.versions[session_id] = []

            self.versions[session_id].append(version)

            # Enforce version limit
            self._enforce_version_limit(session_id)

            logger.info(f"Created version {version_number} for session {session_id}")
            return version

    def get_version_history(self, session_id: str) -> VersionHistory:
        """Get the complete version history for a session."""
        with self._lock:
            session_versions = self.versions.get(session_id, [])

            if not session_versions:
                return VersionHistory(
                    session_id=session_id,
                    versions=[],
                    current_version_id="",
                    total_versions=0,
                    total_edits=0
                )

            current_version = next(
                (v for v in session_versions if v.is_current),
                session_versions[-1] if session_versions else None
            )

            return VersionHistory(
                session_id=session_id,
                versions=session_versions.copy(),
                current_version_id=current_version.version_id if current_version else "",
                total_versions=len(session_versions),
                total_edits=len(session_versions) - 1,  # Exclude initial version
                creation_date=session_versions[0].created_at if session_versions else datetime.now(),
                last_modified=session_versions[-1].created_at if session_versions else datetime.now()
            )

    def get_current_version(self, session_id: str) -> Optional[Version]:
        """Get the current version for a session."""
        with self._lock:
            session_versions = self.versions.get(session_id, [])
            return next((v for v in session_versions if v.is_current), None)

    def get_version_by_id(self, session_id: str, version_id: str) -> Optional[Version]:
        """Get a specific version by ID."""
        with self._lock:
            session_versions = self.versions.get(session_id, [])
            return next((v for v in session_versions if v.version_id == version_id), None)

    def compare_versions(self, session_id: str, version_a_id: str,
                        version_b_id: str) -> VersionComparison:
        """Compare two versions and return differences."""
        with self._lock:
            version_a = self.get_version_by_id(session_id, version_a_id)
            version_b = self.get_version_by_id(session_id, version_b_id)

            if not version_a or not version_b:
                raise ValueError("One or both versions not found")

            # Generate diff
            diff = self.generate_diff(version_a.text, version_b.text)

            # Calculate similarity
            similarity = self.calculate_similarity(version_a.text, version_b.text)

            # Count changes
            additions = len([d for d in diff if d.operation == DiffOperation.INSERT])
            deletions = len([d for d in diff if d.operation == DiffOperation.DELETE])
            modifications = len([d for d in diff if d.operation == DiffOperation.REPLACE])

            # Generate summary
            change_summary = self._generate_change_summary(additions, deletions, modifications)

            # Calculate quality improvement
            quality_improvement = None
            if version_a.quality_score and version_b.quality_score:
                quality_improvement = version_b.quality_score - version_a.quality_score

            return VersionComparison(
                session_id=session_id,
                version_a_id=version_a_id,
                version_b_id=version_b_id,
                version_a_number=version_a.version_number,
                version_b_number=version_b.version_number,
                diff=diff,
                similarity_score=similarity,
                change_summary=change_summary,
                additions=additions,
                deletions=deletions,
                modifications=modifications,
                quality_improvement=quality_improvement
            )

    def revert_to_version(self, session_id: str, target_version_id: str,
                         comment: Optional[str] = None) -> Version:
        """Revert to a previous version by creating a new version with that content."""
        with self._lock:
            target_version = self.get_version_by_id(session_id, target_version_id)
            if not target_version:
                raise ValueError("Target version not found")

            # Create new version with the target version's text
            new_version = self.create_version(
                session_id=session_id,
                text=target_version.text,
                edit_type="revert",
                comment=comment or f"Reverted to version {target_version.version_number}",
                author="system"
            )

            # Set parent to the target version for tracking
            new_version.parent_version_id = target_version_id

            return new_version

    def create_change_log(self, session_id: str, version_from: int,
                         version_to: int, editor_type: str) -> ChangeLog:
        """Create a change log between two versions."""
        with self._lock:
            session_versions = self.versions.get(session_id, [])

            # Find versions by number
            from_version = next(
                (v for v in session_versions if v.version_number == version_from),
                None
            )
            to_version = next(
                (v for v in session_versions if v.version_number == version_to),
                None
            )

            if not from_version or not to_version:
                raise ValueError("One or both versions not found")

            # Generate diff
            changes = self.generate_diff(from_version.text, to_version.text)

            # Create summary
            change_count = len([c for c in changes
                              if c.operation != DiffOperation.EQUAL])
            summary = self._generate_change_summary_detailed(changes)

            return ChangeLog(
                session_id=session_id,
                version_from=version_from,
                version_to=version_to,
                changes=changes,
                change_summary=summary,
                change_count=change_count,
                editor_type=editor_type
            )

    def generate_diff(self, text1: str, text2: str) -> List[TextDiff]:
        """Generate a diff between two texts."""
        # Use difflib for word-level differences
        words1 = text1.split()
        words2 = text2.split()

        differ = difflib.SequenceMatcher(None, words1, words2)
        diffs = []

        pos1 = 0  # Position in original text
        pos2 = 0  # Position in new text

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag == 'equal':
                # Calculate positions in original text
                original_text = ' '.join(words1[i1:i2])
                new_text = ' '.join(words2[j1:j2])

                diff = TextDiff(
                    operation=DiffOperation.EQUAL,
                    start_pos=pos1,
                    end_pos=pos1 + len(original_text),
                    original_text=original_text,
                    new_text=new_text,
                    length=len(original_text)
                )
                diffs.append(diff)

                pos1 += len(original_text) + (1 if i2 > i1 else 0)  # +1 for space

            elif tag == 'delete':
                original_text = ' '.join(words1[i1:i2])
                diff = TextDiff(
                    operation=DiffOperation.DELETE,
                    start_pos=pos1,
                    end_pos=pos1 + len(original_text),
                    original_text=original_text,
                    new_text="",
                    length=len(original_text)
                )
                diffs.append(diff)

                pos1 += len(original_text) + (1 if i2 > i1 else 0)

            elif tag == 'insert':
                new_text = ' '.join(words2[j1:j2])
                diff = TextDiff(
                    operation=DiffOperation.INSERT,
                    start_pos=pos1,
                    end_pos=pos1,
                    original_text="",
                    new_text=new_text,
                    length=len(new_text)
                )
                diffs.append(diff)

            elif tag == 'replace':
                original_text = ' '.join(words1[i1:i2])
                new_text = ' '.join(words2[j1:j2])

                diff = TextDiff(
                    operation=DiffOperation.REPLACE,
                    start_pos=pos1,
                    end_pos=pos1 + len(original_text),
                    original_text=original_text,
                    new_text=new_text,
                    length=len(original_text)
                )
                diffs.append(diff)

                pos1 += len(original_text) + (1 if i2 > i1 else 0)

        return diffs

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts."""
        if text1 == text2:
            return 1.0

        if not text1 and not text2:
            return 1.0

        if not text1 or not text2:
            return 0.0

        # Use SequenceMatcher for similarity
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _enforce_version_limit(self, session_id: str):
        """Enforce the maximum number of versions per session."""
        session_versions = self.versions.get(session_id, [])

        if len(session_versions) > self.max_versions:
            # Remove oldest versions, but keep the first one (initial version)
            versions_to_remove = len(session_versions) - self.max_versions

            # Sort by creation date and remove oldest (but not the first)
            sorted_versions = sorted(session_versions[1:], key=lambda v: v.created_at)
            for _ in range(min(versions_to_remove, len(sorted_versions))):
                version_to_remove = sorted_versions.pop(0)
                session_versions.remove(version_to_remove)
                logger.info(f"Removed old version {version_to_remove.version_id} "
                           f"from session {session_id}")

    def _calculate_quality_score(self, text: str) -> float:
        """Calculate a basic quality score for text."""
        if not text:
            return 0.0

        score = 50.0  # Base score

        # Add points for length (reasonable length)
        word_count = len(text.split())
        if 10 <= word_count <= 500:
            score += 10
        elif word_count > 500:
            score += 5  # Longer isn't always better

        # Add points for sentence variety
        sentences = text.split('.')
        if len(sentences) > 1:
            score += 10

        # Add points for proper capitalization
        if text and text[0].isupper():
            score += 5

        # Subtract points for excessive repetition
        words = text.lower().split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio < 0.5:
                score -= 20
            elif repetition_ratio < 0.7:
                score -= 10

        return max(0.0, min(100.0, score))

    def _generate_change_summary(self, additions: int, deletions: int,
                               modifications: int) -> str:
        """Generate a summary of changes."""
        total_changes = additions + deletions + modifications

        if total_changes == 0:
            return "No changes"

        parts = []
        if additions > 0:
            parts.append(f"{additions} addition{'s' if additions > 1 else ''}")
        if deletions > 0:
            parts.append(f"{deletions} deletion{'s' if deletions > 1 else ''}")
        if modifications > 0:
            parts.append(f"{modifications} modification{'s' if modifications > 1 else ''}")

        return ", ".join(parts)

    def _generate_change_summary_detailed(self, changes: List[TextDiff]) -> str:
        """Generate a detailed summary of changes."""
        if not changes:
            return "No changes"

        change_types = {}
        for change in changes:
            if change.operation != DiffOperation.EQUAL:
                change_types[change.operation] = change_types.get(change.operation, 0) + 1

        if not change_types:
            return "No changes"

        summary_parts = []
        for operation, count in change_types.items():
            op_name = operation.value
            summary_parts.append(f"{count} {op_name}{'s' if count > 1 else ''}")

        return ", ".join(summary_parts)