#!/usr/bin/env python3
"""
Apply compatibility fixes to ayon-core repository.

This script applies two types of fixes:
1. Adds 'from __future__ import annotations' to all Python files
2. Fixes Qt compatibility issues with .screen() method for older Qt versions

Usage:
    python luma_apply_compatibility_fixes.py [--dry-run]

Options:
    --dry-run    Show what would be changed without actually modifying files
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class CompatibilityFixer:
    """Applies compatibility fixes to Python files."""

    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.stats = {
            'future_annotations_added': 0,
            'future_annotations_skipped': 0,
            'qt_screen_fixed': 0,
            'qt_screen_skipped': 0,
            'errors': []
        }

    def has_future_annotations(self, content: str) -> bool:
        """Check if file already has the future annotations import."""
        return 'from __future__ import annotations' in content

    def add_future_import(self, file_path: Path) -> bool:
        """Add future annotations import to a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['errors'].append(f"Error reading {file_path}: {e}")
            return False

        # Skip if already has it
        if self.has_future_annotations(content):
            return False

        # Skip empty files
        if not content.strip():
            return False

        lines = content.split('\n')
        insert_position = 0

        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_position = 1

        # Skip encoding declaration
        for i in range(insert_position, min(insert_position + 3, len(lines))):
            if i < len(lines) and re.match(r'#.*?coding[:=]\s*([-\w.]+)', lines[i]):
                insert_position = i + 1
                break

        # Skip docstring if it's at the very top (module-level)
        if insert_position < len(lines):
            # Check for triple-quoted strings
            if lines[insert_position].strip().startswith('"""') or lines[insert_position].strip().startswith("'''"):
                quote = '"""' if '"""' in lines[insert_position] else "'''"
                # Find end of docstring
                if lines[insert_position].count(quote) >= 2:
                    # Single line docstring
                    insert_position += 1
                else:
                    # Multi-line docstring
                    for i in range(insert_position + 1, len(lines)):
                        if quote in lines[i]:
                            insert_position = i + 1
                            break

        # Insert the import
        new_line = 'from __future__ import annotations'

        # Add blank line after if next line is not blank and not another import
        if insert_position < len(lines) and lines[insert_position].strip():
            if not lines[insert_position].startswith('import') and not lines[insert_position].startswith('from'):
                new_line += '\n'

        lines.insert(insert_position, new_line)
        new_content = '\n'.join(lines)

        if not self.dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                self.stats['errors'].append(f"Error writing {file_path}: {e}")
                return False

        return True

    def fix_qt_screen_compatibility(self, file_path: Path) -> bool:
        """Fix Qt .screen() compatibility issues in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['errors'].append(f"Error reading {file_path}: {e}")
            return False

        original_content = content
        modified = False

        # Pattern 1: screen = window.screen() / screen = dialog.screen()
        # Replace with try-except block if not already wrapped
        patterns = [
            # Pattern: variable = something.screen() followed by geometry()
            {
                'search': re.compile(
                    r'(\s+)((?:screen|window)\s*=\s*(?:window|dialog|self)\.screen\(\))\s*\n'
                    r'(\s+)(\w+\s*=\s*(?:screen|window)\.(?:geometry|availableGeometry)\(\))',
                    re.MULTILINE
                ),
                'check_wrapped': lambda match, content: self._is_in_try_block(content, match.start()),
                'replacement': (
                    r'\1try:\n'
                    r'\1    \2\n'
                    r'\3    \4\n'
                    r'\1except AttributeError:\n'
                    r'\1    # Backwards compatibility for older Qt versions\n'
                    r'\1    desktop = QtWidgets.QDesktopWidget()\n'
                    r'\1    \4'.replace('screen.', 'desktop.').replace('window.', 'desktop.')
                )
            },
        ]

        # Specific file fixes based on known patterns
        file_specific_fixes = {
            'client/ayon_core/tools/utils/lib.py': self._fix_lib_center_window,
            'client/ayon_core/tools/publisher/window.py': self._fix_publisher_window,
            'client/ayon_core/tools/launcher/ui/actions_widget.py': self._fix_actions_widget,
        }

        # Check if this file needs specific fixes
        relative_path = str(file_path.relative_to(self.repo_root))
        if relative_path in file_specific_fixes:
            new_content = file_specific_fixes[relative_path](content)
            if new_content != content:
                modified = True
                content = new_content

        if modified and not self.dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                self.stats['errors'].append(f"Error writing {file_path}: {e}")
                return False

        return modified

    def _is_in_try_block(self, content: str, pos: int) -> bool:
        """Check if position is already inside a try block."""
        # Look backwards from position to find if we're in a try block
        lines_before = content[:pos].split('\n')
        indent_level = None

        for line in reversed(lines_before[-20:]):  # Check last 20 lines
            if 'try:' in line:
                return True
            if line.strip() and not line.strip().startswith('#'):
                # If we hit a line with less indentation, we're out of the block
                if indent_level is None:
                    indent_level = len(line) - len(line.lstrip())
                else:
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent < indent_level:
                        break
        return False

    def _fix_lib_center_window(self, content: str) -> str:
        """Fix center_window function in lib.py."""
        old_pattern = re.compile(
            r'def center_window\(window\):\s*\n'
            r'\s*"""Move window to center of it\'s screen\."""\s*\n'
            r'\s*screen = window\.screen\(\)\s*\n'
            r'\s*screen_geo = screen\.geometry\(\)',
            re.MULTILINE
        )

        if old_pattern.search(content) and 'try:' not in content[content.find('def center_window'):content.find('def center_window') + 500]:
            new_text = (
                'def center_window(window):\n'
                '    """Move window to center of it\'s screen."""\n'
                '    try:\n'
                '        screen = window.screen()\n'
                '        screen_geo = screen.geometry()\n'
                '    except AttributeError:\n'
                '        # Backwards compatibility for older Qt versions\n'
                '        desktop = QtWidgets.QDesktopWidget()\n'
                '        screen_geo = desktop.availableGeometry(window)'
            )
            content = old_pattern.sub(new_text, content)

        return content

    def _fix_publisher_window(self, content: str) -> str:
        """Fix _on_help_click method in publisher window.py."""
        # Check if already fixed
        if 'def _on_help_click(self):' in content:
            method_start = content.find('def _on_help_click(self):')
            method_section = content[method_start:method_start + 800]

            if 'screen = window.screen()' in method_section and 'try:' not in method_section[:method_section.find('screen = window.screen()')]:
                old_pattern = re.compile(
                    r'(\s+)window = self\.window\(\)\s*\n'
                    r'\s+screen = window\.screen\(\)\s*\n'
                    r'\s+screen_geo = screen\.geometry\(\)',
                    re.MULTILINE
                )

                new_text = (
                    r'\1window = self.window()\n'
                    r'\1try:\n'
                    r'\1    screen = window.screen()\n'
                    r'\1    screen_geo = screen.geometry()\n'
                    r'\1except AttributeError:\n'
                    r'\1    # Backwards compatibility for older Qt versions\n'
                    r'\1    desktop = QtWidgets.QDesktopWidget()\n'
                    r'\1    screen_geo = desktop.availableGeometry(window)'
                )
                content = old_pattern.sub(new_text, content)

        return content

    def _fix_actions_widget(self, content: str) -> str:
        """Fix actions_widget.py Qt compatibility issues."""
        modified = False

        # Fix 1: Line ~525 - window = self.screen()
        pattern1 = re.compile(
            r'(\s+)label_width, label_height = label_sh\.width\(\), label_sh\.height\(\)\s*\n'
            r'\s+window = self\.screen\(\)\s*\n'
            r'\s+window_geo = window\.geometry\(\)',
            re.MULTILINE
        )

        if pattern1.search(content):
            section = content[content.find('label_width, label_height'):content.find('label_width, label_height') + 300]
            if 'try:' not in section:
                new_text1 = (
                    r'\1label_width, label_height = label_sh.width(), label_sh.height()\n'
                    r'\1try:\n'
                    r'\1    window = self.screen()\n'
                    r'\1    window_geo = window.geometry()\n'
                    r'\1except AttributeError:\n'
                    r'\1    # Backwards compatibility for older Qt versions\n'
                    r'\1    desktop = QtWidgets.QDesktopWidget()\n'
                    r'\1    window_geo = desktop.availableGeometry(self)'
                )
                content = pattern1.sub(new_text1, content)
                modified = True

        # Fix 2: _center_dialog static method
        pattern2 = re.compile(
            r'(@staticmethod\s*\n\s+def _center_dialog\(dialog, target_center_pos\):.*?)'
            r'(\s+)screen = dialog\.screen\(\)\s*\n'
            r'\s+screen_geo = screen\.availableGeometry\(\)',
            re.MULTILINE | re.DOTALL
        )

        if pattern2.search(content):
            match = pattern2.search(content)
            if match:
                section = content[match.start():match.end() + 200]
                if 'try:' not in section:
                    new_text2 = (
                        r'\1'
                        r'\2try:\n'
                        r'\2    screen = dialog.screen()\n'
                        r'\2    screen_geo = screen.availableGeometry()\n'
                        r'\2except AttributeError:\n'
                        r'\2    # Backwards compatibility for older Qt versions\n'
                        r'\2    desktop = QtWidgets.QDesktopWidget()\n'
                        r'\2    screen_geo = desktop.availableGeometry(dialog)'
                    )
                    content = pattern2.sub(new_text2, content)
                    modified = True

        return content

    def process_files(self) -> None:
        """Process all Python files in the repository."""
        # Files that specifically need Qt fixes
        qt_fix_files = [
            'client/ayon_core/tools/utils/lib.py',
            'client/ayon_core/tools/publisher/window.py',
            'client/ayon_core/tools/launcher/ui/actions_widget.py',
        ]

        print("=" * 60)
        print("Processing Python files...")
        print("=" * 60)

        # Process all Python files for future annotations
        for py_file in self.repo_root.rglob('*.py'):
            # Skip __pycache__ and .git directories
            if '__pycache__' in str(py_file) or '.git' in str(py_file):
                continue

            # Skip this script itself
            if py_file.name == 'luma_apply_compatibility_fixes.py':
                continue

            relative_path = py_file.relative_to(self.repo_root)

            # Add future annotations
            if self.add_future_import(py_file):
                self.stats['future_annotations_added'] += 1
                status = "[DRY RUN] Would modify" if self.dry_run else "✓ Modified"
                print(f"{status}: {relative_path}")
            else:
                self.stats['future_annotations_skipped'] += 1

        # Process specific files for Qt fixes
        print("\n" + "=" * 60)
        print("Applying Qt compatibility fixes...")
        print("=" * 60)

        for file_path in qt_fix_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                if self.fix_qt_screen_compatibility(full_path):
                    self.stats['qt_screen_fixed'] += 1
                    status = "[DRY RUN] Would fix" if self.dry_run else "✓ Fixed"
                    print(f"{status} Qt compatibility: {file_path}")
                else:
                    self.stats['qt_screen_skipped'] += 1
                    print(f"⊘ Skipped (already fixed or no changes needed): {file_path}")
            else:
                print(f"⚠ File not found: {file_path}")

    def print_summary(self) -> None:
        """Print summary of changes."""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if self.dry_run:
            print("DRY RUN MODE - No files were actually modified")
            print()

        print(f"Future Annotations:")
        print(f"  Added:   {self.stats['future_annotations_added']} files")
        print(f"  Skipped: {self.stats['future_annotations_skipped']} files (already had import or empty)")
        print()
        print(f"Qt Compatibility Fixes:")
        print(f"  Fixed:   {self.stats['qt_screen_fixed']} files")
        print(f"  Skipped: {self.stats['qt_screen_skipped']} files")

        if self.stats['errors']:
            print()
            print(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  ✗ {error}")

        print("=" * 60)


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # Find repo root (directory containing this script)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent

    print(f"Repository root: {repo_root}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    if dry_run:
        print("Running in DRY RUN mode - no files will be modified")
        print("Remove --dry-run flag to apply changes")
        print()

    fixer = CompatibilityFixer(repo_root, dry_run=dry_run)
    fixer.process_files()
    fixer.print_summary()

    if dry_run:
        print("\nTo apply these changes, run:")
        print(f"  python {script_path.name}")


if __name__ == '__main__':
    main()
