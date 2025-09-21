#!/usr/bin/env python3
"""
Advanced file watcher for automatic documentation generation.
Watches for changes in Python files and regenerates documentation automatically.
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from typing import Set, Dict
from datetime import datetime

# Fix encoding issues on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class DocumentationHandler(FileSystemEventHandler):
    """Handles file system events and triggers documentation regeneration."""

    def __init__(self, project_root: Path, debounce_delay: float = 2.0):
        super().__init__()
        self.project_root = project_root
        self.debounce_delay = debounce_delay
        self.pending_changes: Set[str] = set()
        self.last_change_time = 0
        self.timer = None
        self.generation_in_progress = False

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Only process Python files
        if not event.src_path.endswith('.py'):
            return

        # Skip __pycache__ and other generated files
        if '__pycache__' in event.src_path or '.pyc' in event.src_path:
            return

        self.handle_change(event.src_path)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        if event.src_path.endswith('.py'):
            self.handle_change(event.src_path)

    def handle_change(self, file_path: str):
        """Handle a file change with debouncing."""
        if self.generation_in_progress:
            return

        self.pending_changes.add(file_path)
        self.last_change_time = time.time()

        # Cancel existing timer
        if self.timer:
            self.timer.cancel()

        # Start new timer
        self.timer = threading.Timer(self.debounce_delay, self.regenerate_docs)
        self.timer.start()

    def regenerate_docs(self):
        """Regenerate documentation for pending changes."""
        if self.generation_in_progress:
            return

        self.generation_in_progress = True

        try:
            if self.pending_changes:
                print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Changes detected:")
                for file_path in sorted(self.pending_changes):
                    rel_path = Path(file_path).relative_to(self.project_root)
                    print(f"   📝 {rel_path}")

                print("\n📚 Regenerating documentation...")
                start_time = time.time()

                # Run documentation generation
                result = subprocess.run(
                    [sys.executable, "scripts/generate_docs.py"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                elapsed = time.time() - start_time

                if result.returncode == 0:
                    print(f"✅ Documentation updated in {elapsed:.1f}s")
                else:
                    print(f"❌ Documentation generation failed:")
                    print(result.stderr)

                self.pending_changes.clear()

        finally:
            self.generation_in_progress = False


class FallbackWatcher:
    """Fallback file watcher when watchdog is not available."""

    def __init__(self, project_root: Path, watch_dirs: list):
        self.project_root = project_root
        self.watch_dirs = watch_dirs
        self.file_times: Dict[str, float] = {}
        self.last_check = time.time()

    def scan_for_changes(self) -> Set[str]:
        """Scan directories for file changes."""
        changed_files = set()
        current_time = time.time()

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            for py_file in watch_dir.rglob("*.py"):
                if '__pycache__' in str(py_file):
                    continue

                try:
                    mtime = py_file.stat().st_mtime
                    file_path = str(py_file)

                    if file_path not in self.file_times:
                        self.file_times[file_path] = mtime
                    elif mtime > self.file_times[file_path] and mtime > self.last_check:
                        changed_files.add(file_path)
                        self.file_times[file_path] = mtime

                except OSError:
                    continue

        self.last_check = current_time
        return changed_files

    def watch(self, check_interval: float = 2.0):
        """Start watching for changes."""
        print("📡 Using fallback file watching (polling mode)")
        print(f"🔄 Checking for changes every {check_interval} seconds")

        handler = DocumentationHandler(self.project_root)

        while True:
            try:
                changed_files = self.scan_for_changes()
                for file_path in changed_files:
                    handler.handle_change(file_path)

                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("\n🛑 Stopping file watcher...")
                break


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"

    if not services_dir.exists():
        print(f"❌ Services directory not found: {services_dir}")
        sys.exit(1)

    # Watch directories
    watch_dirs = [services_dir]

    print("🚀 HELIOS Documentation Watcher")
    print("=" * 40)
    print(f"📂 Project root: {project_root}")
    print(f"👀 Watching: {', '.join(str(d) for d in watch_dirs)}")
    print("🔄 Auto-regenerating documentation on file changes")
    print("🛑 Press Ctrl+C to stop\n")

    # Initial documentation generation
    print("📚 Generating initial documentation...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/generate_docs.py"],
            cwd=project_root,
            check=True
        )
        print("✅ Initial documentation generated\n")
    except subprocess.CalledProcessError:
        print("❌ Failed to generate initial documentation")
        sys.exit(1)

    try:
        if WATCHDOG_AVAILABLE:
            # Use watchdog for efficient file watching
            print("📡 Using advanced file watching (watchdog)")
            observer = Observer()
            handler = DocumentationHandler(project_root)

            for watch_dir in watch_dirs:
                observer.schedule(handler, str(watch_dir), recursive=True)

            observer.start()
            print("👀 Watching for changes...")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping file watcher...")
            finally:
                observer.stop()
                observer.join()

        else:
            # Use fallback polling method
            print("⚠️  watchdog package not available, using fallback polling")
            print("💡 Install watchdog for better performance: pip install watchdog\n")

            watcher = FallbackWatcher(project_root, watch_dirs)
            watcher.watch()

    except KeyboardInterrupt:
        print("\n👋 Documentation watcher stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
