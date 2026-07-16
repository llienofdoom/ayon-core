# CLAUDE.md

Guidance for working on the Luma Studios fork of `ayon-core`.

## Project Overview

`ayon-core` is the base addon: the pipeline library, publish/load plugin
framework, and the artist tools (Loader, Scene Inventory/Manager, Publisher,
Tray). Almost every other addon depends on it, so changes here are high blast
radius — prefer fixing a host addon when the bug is host-specific.

## Branch Convention

```
origin   -> github.com/{GITHUB_USERNAME}/ayon-core   (fork)
upstream -> github.com/ynput/ayon-core               (ynput)

develop  -- mirrors upstream. Never commit directly.
luma     -- Luma production branch, based on upstream release tags.
```

## Versioning (Luma Studios)

Format: `{upstream_version}+ls.{major}.{minor}.{patch}` — e.g. `1.9.8+ls.0.2.0`.

**Edit `package.py` only.** `create_package.py` regenerates the rest
(`client/ayon_core/version.py`, `pyproject.toml`). A build therefore leaves
version-file diffs in the working tree — that is expected; commit them.

Upstream sync bumps the base and increments the LS minor; a bug fix increments
the LS patch.

## Compatibility Fixes (run after every upstream sync)

```bash
python3 luma_apply_compatibility_fixes.py --dry-run   # preview
python3 luma_apply_compatibility_fixes.py             # apply
```

Adds `from __future__ import annotations` broadly, plus Qt `.screen()` fallbacks
for pre-5.14 bindings. Idempotent. See `luma_COMPATIBILITY_FIXES_README.md`.

**It does not cover runtime Python 3.7 breaks.** The `__future__` import only
makes *annotations* lazy. After a sync, also scan `client/` for: walrus (`:=`),
`match`, `str.removeprefix`/`removesuffix`, dict union, and PEP 604 unions
evaluated at runtime. Only annotations in **signatures** and at **module/class
level** are evaluated — the same expression inside a function body is harmless.
A syntax-only gate (`ast.parse(..., feature_version=(3, 7))`) will not catch the
runtime ones. Full pattern table in
`_ayon-manager/docs/dev_contribute.md`.

---

## Known Issues / Deferred

### CollectAudio breaks review publishes on a sitesync local site

**Status: deferred, not fixed.** Recorded 2026-07-16. Present upstream and in
every version we ship (verified identical in **1.9.1** and **1.9.8**).

**Symptom:** publishing a review from Nuke on a sitesync **local** active site
fails, looking for the shot's audio under the publish folder. Downloading the
audio manually and re-publishing succeeds. Observed on LumaRND
`/shots/ChiefChickenTest/sh0020`.

**Cause** — `client/ayon_core/plugins/publish/collect_audio.py`:

```python
class CollectAudio(pyblish.api.ContextPlugin):
    families = ["review"]
    settings_category = "core"
    audio_product_name = "audioMain"
...
    repre_path = get_representation_path_with_anatomy(repre_entity, anatomy)
    instance.data["audio"] = [{"offset": 0, "filename": repre_path}]
```

The path is resolved through **anatomy**, i.e. the *active site's* roots. With
sitesync and `active_site = local`, that is a local path (`…\WORK_LOCAL\…`) that
does not exist until the file has been downloaded. There is **no existence
check** (no `os.path.exists` anywhere in the plugin).

`client/ayon_core/plugins/publish/extract_review.py` then asks only whether audio
was *collected*, never whether it is *present*:

```python
with_audio = True
if (
    "no-audio" in output_def["tags"]        # profile tag
    or not instance.data.get("audio")       # nothing collected
):
    with_audio = False
```

So ffmpeg receives a missing input and the publish dies with an opaque error
instead of "audio is not available on your local site".

**Desired behaviour:** it should not fail. Either skip with a clear warning when
the file is not on the active site, or expose a toggle on `CollectAudioModel`
(`server/settings/publish_plugins.py`) — e.g. *"Skip if unavailable"* — so
studios opt in rather than getting an ffmpeg error.

**Workarounds today:**
- download the audio before publishing;
- add the `no-audio` tag to the review output
  (`core → publish → ExtractReview → profiles → outputs → tags`);
- or disable `core → publish → Collect Audio`.

**Generalise:** this is not audio-specific. Anything publish resolves through
anatomy on a local site can be missing. When a publish fails oddly on a local
site, first ask whether the dependency is actually downloaded.

**Upstream:** candidate PR, alongside the `ayon-sitesync` fixes.

---

## Commit Conventions

```
<type>(<scope>): <summary>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `perf`.
