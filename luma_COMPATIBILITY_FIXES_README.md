# AYON-Core Compatibility Fixes

This directory contains a script to apply compatibility fixes to the ayon-core repository after updates.

## Quick Start

After pulling updates from the upstream repository, run:

```bash
python luma_apply_compatibility_fixes.py
```

To preview changes without modifying files:

```bash
python luma_apply_compatibility_fixes.py --dry-run
```

## What This Script Does

### 1. Future Annotations Import

Adds `from __future__ import annotations` to all Python files that don't already have it.

**Why?**
- Enables PEP 563 postponed annotation evaluation
- Allows cleaner type hints without string quotes
- Prevents `NameError` from forward references
- Improves code readability and IDE support
- Required for modern Python typing patterns

**Example:**
```python
# Before
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .some_module import SomeClass

def method(self) -> "SomeClass":  # Needs quotes
    pass

# After
from __future__ import annotations
from .some_module import SomeClass

def method(self) -> SomeClass:  # No quotes needed!
    pass
```

### 2. Qt Compatibility Fixes

Fixes `.screen()` method calls that fail on older Qt versions (pre-5.14).

**Files Fixed:**
- `client/ayon_core/tools/utils/lib.py` - `center_window()` function
- `client/ayon_core/tools/publisher/window.py` - `_on_help_click()` method
- `client/ayon_core/tools/launcher/ui/actions_widget.py` - Multiple methods

**Why?**
- The `.screen()` method only exists in Qt 5.14+ and newer bindings (PySide6)
- Older DCCs (Maya, Nuke, Houdini, etc.) may use older Qt versions
- Falls back to `QDesktopWidget()` for compatibility

**Example:**
```python
# Before (breaks on older Qt)
screen = window.screen()
screen_geo = screen.geometry()

# After (works on all Qt versions)
try:
    screen = window.screen()
    screen_geo = screen.geometry()
except AttributeError:
    # Backwards compatibility for older Qt versions
    desktop = QtWidgets.QDesktopWidget()
    screen_geo = desktop.availableGeometry(window)
```

## When to Run This Script

Run this script after:

1. **Pulling updates from upstream ayon-core repository**
   ```bash
   git pull upstream develop
   python luma_apply_compatibility_fixes.py
   ```

2. **Merging new code from main branch**
   ```bash
   git merge upstream/develop
   python luma_apply_compatibility_fixes.py
   ```

3. **After adding new Python files** that need these fixes

## Workflow Example

```bash
# 1. Pull latest changes
cd /path/to/ayon-core
git pull upstream develop

# 2. Preview what would change
python luma_apply_compatibility_fixes.py --dry-run

# 3. Apply the fixes
python luma_apply_compatibility_fixes.py

# 4. Review the changes
git diff

# 5. Commit if needed
git add -u
git commit -m "Apply compatibility fixes after upstream merge"
```

## Script Behavior

### Safe to Run Multiple Times
- The script is idempotent - running it multiple times won't cause issues
- It automatically skips files that already have the fixes applied
- Always shows a summary of what was changed

### Dry Run Mode
```bash
python luma_apply_compatibility_fixes.py --dry-run
```
- Shows exactly what would change
- Doesn't modify any files
- Useful for reviewing before applying

### What Gets Modified

**Future Annotations:**
- Inserted after encoding declarations (`# -*- coding: utf-8 -*-`)
- Inserted after shebang lines (`#!/usr/bin/env python`)
- Placed before module docstrings where appropriate
- Smart positioning to maintain proper Python file structure

**Qt Fixes:**
- Only modifies specific known problem areas
- Wraps `.screen()` calls in try-except blocks
- Adds proper fallback for older Qt versions
- Preserves all existing functionality

### What Gets Skipped

- Files that already have `from __future__ import annotations`
- Files where Qt fixes are already applied
- Empty files
- Files in `__pycache__` or `.git` directories
- The script itself (`luma_apply_compatibility_fixes.py`)

## Troubleshooting

### Error: "SyntaxError: invalid syntax"
If you see syntax errors after running the script, this might be due to:
- Python version incompatibility (ensure Python 3.7+)
- Malformed source files in the repository

Run with `--dry-run` first to check what would change.

### Files Not Being Fixed
If specific files aren't being modified:
1. Check if they already have the fixes (look for `from __future__ import annotations` at the top)
2. Verify the file path matches what's in the script
3. Check the summary output for error messages

### Qt Fixes Not Applied
The Qt fixes are targeted to specific files. If you encounter Qt-related errors in other files:
1. Note the file path and error message
2. Add the file to the `qt_fix_files` list in the script
3. Create a custom fix method if needed

## Customization

### Adding New Files to Qt Fix List

Edit `luma_apply_compatibility_fixes.py` and add to the `qt_fix_files` list:

```python
qt_fix_files = [
    'client/ayon_core/tools/utils/lib.py',
    'client/ayon_core/tools/publisher/window.py',
    'client/ayon_core/tools/launcher/ui/actions_widget.py',
    'path/to/your/new/file.py',  # Add here
]
```

### Creating Custom Fix Methods

For complex file-specific fixes, add a method to the `CompatibilityFixer` class:

```python
def _fix_your_custom_file(self, content: str) -> str:
    """Fix specific issues in your custom file."""
    # Your fix logic here
    return content
```

Then add it to `file_specific_fixes`:

```python
file_specific_fixes = {
    'path/to/your/file.py': self._fix_your_custom_file,
}
```

## Script Output

Example output:
```
============================================================
Processing Python files...
============================================================
✓ Modified: client/ayon_core/some_file.py
✓ Modified: client/ayon_core/another_file.py

============================================================
Applying Qt compatibility fixes...
============================================================
✓ Fixed Qt compatibility: client/ayon_core/tools/utils/lib.py
⊘ Skipped (already fixed): client/ayon_core/tools/publisher/window.py

============================================================
SUMMARY
============================================================
Future Annotations:
  Added:   2 files
  Skipped: 450 files (already had import or empty)

Qt Compatibility Fixes:
  Fixed:   1 files
  Skipped: 2 files
============================================================
```

## Version History

- **v1.0** - Initial version
  - Adds future annotations import
  - Fixes Qt .screen() compatibility issues
  - Supports dry-run mode

## Additional Notes

### Impact on Other Packages
- These fixes **only affect files in ayon-core**
- External packages that import from ayon-core are **not affected**
- The `from __future__ import annotations` is file-scoped only
- Safe to use with all Python 3.7+ versions

### Python Version Requirements
- Minimum: Python 3.7 (for `from __future__ import annotations`)
- Recommended: Python 3.9+ (matches AYON's requirements)

### Performance
- Script typically completes in under 10 seconds
- Processes 450+ files efficiently
- No impact on runtime performance of the fixed code

## Support

If you encounter issues with this script:
1. Run with `--dry-run` to see what would change
2. Check the error messages in the summary
3. Manually inspect problematic files
4. Update the script if new patterns emerge

---

**Maintained for:** AYON-Core compatibility patches
**Last Updated:** 2025-11-25
