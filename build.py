#!/usr/bin/env python3
"""Cross-compile for Wombat using Docker.

Goals:
- Pure stdlib Python (no third-party deps)
- Cross-platform host support (Windows / macOS / Linux)
- Faster builds via incremental compilation + optional parallelism
- Robust path handling (no host-absolute paths inside the container)

This script expects Docker to be installed and available on PATH.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import os
import platform
import re
import shlex
import subprocess
import sys
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

# -------------------------
# Utility helpers
# -------------------------


# Modify eprint to be a no-op function to suppress extra output
def eprint(*args: object) -> None:
    pass


def run(
    cmd: Sequence[str],
    *,
    check: bool = True,
    capture: bool = False,
    cwd: Optional[Path] = None,
    verbose: bool = False,
) -> subprocess.CompletedProcess:
    """Run a subprocess command.

    - Uses list-args to avoid shell injection.
    - Optionally captures stdout.
    """

    if verbose:
        eprint("[cmd]", " ".join(shlex.quote(c) for c in cmd))

    try:
        return subprocess.run(
            list(cmd),
            check=check,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        raise
    except subprocess.CalledProcessError as ex:
        if capture:
            if ex.stdout:
                eprint(ex.stdout.rstrip())
            if ex.stderr:
                eprint(ex.stderr.rstrip())
        raise


# -------------------------
# Minimal YAML loader
# -------------------------


_YAML_KV_RE = re.compile(r"^(?P<key>[^:#]+?)\s*:\s*(?P<value>.*)$")
_YAML_LIST_RE = re.compile(r"^\-\s+(?P<value>.*)$")


def _strip_inline_comment(s: str) -> str:
    """Strip a trailing # comment, respecting simple quotes."""
    out: List[str] = []
    in_squote = False
    in_dquote = False
    it = iter(range(len(s)))
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
        elif ch == '"' and not in_squote:
            in_dquote = not in_dquote
        elif ch == "#" and not in_squote and not in_dquote:
            break
        out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _parse_scalar(value: str) -> Any:
    v = value.strip()
    if v == "":
        return ""

    # Quoted strings
    if (len(v) >= 2) and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        return v[1:-1]

    low = v.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~"):
        return None

    # Inline empty list
    if v == "[]":
        return []

    # Integers (basic)
    if re.fullmatch(r"[-+]?\d+", v):
        try:
            return int(v, 10)
        except ValueError:
            return v

    return v


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a practical YAML subset.

    Supports:
    - key: value
    - nested dicts via indentation
    - lists under a key via:
        key:
          - item
          - item

    Not a full YAML implementation.
    """

    root: Dict[str, Any] = {}
    # Stack of (indent_threshold, container)
    stack: List[Tuple[int, Any]] = [(0, root)]

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")

        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        stripped = _strip_inline_comment(raw.strip(" "))
        if stripped == "":
            i += 1
            continue

        # Pop to the appropriate parent level
        while stack and indent < stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(0, root)]

        parent = stack[-1][1]

        # List item
        m_list = _YAML_LIST_RE.match(stripped)
        if m_list:
            if isinstance(parent, list):
                item_txt = m_list.group("value").strip()
                # Support very small subset of "- key: value" list items.
                m_inline_kv = _YAML_KV_RE.match(item_txt)
                if m_inline_kv and ":" in item_txt:
                    parent.append(
                        {
                            m_inline_kv.group("key").strip(): _parse_scalar(
                                m_inline_kv.group("value").strip()
                            )
                        }
                    )
                else:
                    parent.append(_parse_scalar(item_txt))
            i += 1
            continue

        m_kv = _YAML_KV_RE.match(stripped)
        if not m_kv:
            i += 1
            continue

        if not isinstance(parent, dict):
            i += 1
            continue

        key = m_kv.group("key").strip()
        value_raw = m_kv.group("value").strip()

        if value_raw != "":
            parent[key] = _parse_scalar(value_raw)
            i += 1
            continue

        # value is empty: decide whether this key holds a list or dict by peeking ahead
        j = i + 1
        next_is_list = False
        while j < len(lines):
            nxt_raw = lines[j].rstrip("\n")
            if not nxt_raw.strip() or nxt_raw.lstrip().startswith("#"):
                j += 1
                continue
            nxt_indent = len(nxt_raw) - len(nxt_raw.lstrip(" "))
            nxt_stripped = _strip_inline_comment(nxt_raw.strip(" "))
            if nxt_stripped == "":
                j += 1
                continue
            # If the next meaningful line is indented further and is a list item, it's a list
            if nxt_indent > indent and _YAML_LIST_RE.match(nxt_stripped):
                next_is_list = True
            break

        new_container: Any = [] if next_is_list else {}
        parent[key] = new_container
        # Any future line with indent > current indent stays within this container
        stack.append((indent + 1, new_container))
        i += 1

    return root


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge override into base (returns a new dict)."""
    out = copy.deepcopy(base)
    stack: List[Tuple[Dict[str, Any], Dict[str, Any]]] = [(out, override)]
    while stack:
        dst, src = stack.pop()
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                stack.append((dst[k], v))
            else:
                dst[k] = copy.deepcopy(v)
    return out


def load_config(config_path: Path) -> Dict[str, Any]:
    default_config: Dict[str, Any] = {
        "docker_image": "sillyfreak/wombat-cross",
        "compiler": {
            "cross_compiler": "aarch64-linux-gnu-g++",
            "flags": "-Wall",
            "optimization": "-O2",
            "debug": True,
            "c_standard": "c11",
            "cpp_standard": "c++17",
        },
        "linker": {
            "libraries": "kipr pthread m z",
            "flags": "",
        },
        "directories": {
            "source": "src",
            "include": "include",
            "output": "out",
            "objects": "obj",
            "build": "build",
        },
        "output_name": "botball_user_program",
        "extra_args": [],
        "submodules": {
            # auto: compile only submodules whose headers are included
            # all: compile all submodules under lib/
            # none: ignore lib/
            "mode": "auto",
        },
        "jobs": 0,  # 0 means auto (host cpu count)
    }

    if not config_path.exists():
        eprint(f"Note: {config_path} not found; using default configuration.")
        return default_config

    try:
        raw = config_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as ex:
        eprint(f"Warning: could not read config {config_path}: {ex}")
        eprint("Using default configuration.")
        return default_config

    try:
        if config_path.suffix.lower() == ".json":
            user_cfg = json.loads(raw)
        else:
            user_cfg = parse_simple_yaml(raw)
        if not isinstance(user_cfg, dict):
            raise TypeError("Config root must be a mapping")
        return deep_merge(default_config, user_cfg)
    except Exception as ex:
        eprint(f"Warning: could not parse config {config_path}: {ex}")
        eprint("Using default configuration.")
        return default_config


# -------------------------
# Build model
# -------------------------


@dataclasses.dataclass(frozen=True)
class Submodule:
    name: str
    root: Path
    include_dir: Optional[Path]
    src_dir: Optional[Path]
    sources: Tuple[Path, ...]


@dataclasses.dataclass(frozen=True)
class SourceUnit:
    src_abs: Path
    src_rel_posix: str
    obj_rel_posix: str
    dep_rel_posix: str
    lang: str  # "c" or "c++"
    std: str


def iter_files(root: Path, exts: Tuple[str, ...]) -> Iterator[Path]:
    """Fast-ish recursive file iteration using os.scandir."""
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            # Skip common heavy dirs
                            if entry.name in {".git", ".svn", ".hg", "__pycache__"}:
                                continue
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            name = entry.name
                            # A tiny micro-opt: avoid Path.suffix overhead
                            for ext in exts:
                                if name.endswith(ext):
                                    yield Path(entry.path)
                                    break
                    except OSError:
                        continue
        except OSError:
            continue


def discover_submodules(project_root: Path) -> List[Submodule]:
    lib_dir = project_root / "lib"
    if not lib_dir.is_dir():
        return []

    subs: List[Submodule] = []
    try:
        entries = list(os.scandir(lib_dir))
    except OSError:
        return []

    for ent in entries:
        if not ent.is_dir(follow_symlinks=False):
            continue
        name = ent.name
        root = Path(ent.path)
        include_dir = root / "include"
        src_dir = root / "src"

        inc = include_dir if include_dir.is_dir() else None
        src = src_dir if src_dir.is_dir() else None

        sources: Tuple[Path, ...] = ()
        if src is not None:
            sources = tuple(
                sorted(
                    iter_files(src, (".c", ".cc", ".cpp", ".cxx")),
                    key=lambda p: p.as_posix(),
                )
            )

        subs.append(
            Submodule(
                name=name, root=root, include_dir=inc, src_dir=src, sources=sources
            )
        )

    subs.sort(key=lambda s: s.name)
    return subs


_INCLUDE_RE = re.compile(r"^\s*#\s*include\s*[<\"](?P<path>[^>\"]+)[>\"]")


def to_rel_posix(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def resolve_include(
    include_token: str,
    *,
    current_dir: Path,
    include_dirs: Sequence[Path],
    cache: Dict[Tuple[str, str], Optional[Path]],
) -> Optional[Path]:
    """Resolve an include token to a local file if possible."""
    key = (str(current_dir), include_token)
    if key in cache:
        return cache[key]

    token = include_token.strip()
    # Ignore absolute paths
    if token.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", token):
        cache[key] = None
        return None

    # 1) "current directory" lookup first
    cand = current_dir / token
    if cand.exists() and cand.is_file():
        cache[key] = cand
        return cand

    # 2) include path lookup
    for inc in include_dirs:
        cand = inc / token
        if cand.exists() and cand.is_file():
            cache[key] = cand
            return cand

    cache[key] = None
    return None


def detect_used_submodules(
    project_root: Path,
    entry_sources: Sequence[Path],
    submodules: Sequence[Submodule],
    project_include_dir: Optional[Path],
    *,
    verbose: bool = False,
) -> List[Submodule]:
    """Detect submodules used by scanning transitive local includes."""

    # If no include dirs exist, there's nothing meaningful to resolve.
    include_dirs: List[Path] = []
    if project_include_dir and project_include_dir.is_dir():
        include_dirs.append(project_include_dir)
    for s in submodules:
        if s.include_dir and s.include_dir.is_dir():
            include_dirs.append(s.include_dir)

    # Map include_dir -> module name for quick containment checks.
    module_include_dirs: List[Tuple[str, Path]] = [
        (s.name, s.include_dir.resolve())
        for s in submodules
        if s.include_dir and s.include_dir.is_dir()
    ]

    used: Set[str] = set()
    visited: Set[Path] = set()
    q: deque[Path] = deque(entry_sources)
    resolve_cache: Dict[Tuple[str, str], Optional[Path]] = {}

    while q:
        f = q.popleft()
        try:
            f = f.resolve()
        except OSError:
            continue
        if f in visited or not f.exists() or not f.is_file():
            continue
        visited.add(f)

        cur_dir = f.parent
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line in text.splitlines():
            m = _INCLUDE_RE.match(line)
            if not m:
                continue
            token = m.group("path").strip()
            resolved = resolve_include(
                token,
                current_dir=cur_dir,
                include_dirs=include_dirs,
                cache=resolve_cache,
            )
            if not resolved:
                continue

            # Mark module usage
            try:
                r_res = resolved.resolve()
            except OSError:
                r_res = resolved

            for mod_name, inc_dir in module_include_dirs:
                try:
                    # Python 3.9+: is_relative_to
                    if hasattr(r_res, "is_relative_to"):
                        if r_res.is_relative_to(inc_dir):
                            used.add(mod_name)
                            break
                    else:
                        # Fallback for very old Python
                        r_res.relative_to(inc_dir)
                        used.add(mod_name)
                        break
                except Exception:
                    continue

            # Follow transitive includes if local
            q.append(resolved)

    if verbose:
        eprint(
            f"Detected used submodules: {', '.join(sorted(used)) if used else '(none)'}"
        )

    out = [s for s in submodules if s.name in used]
    out.sort(key=lambda s: s.name)
    return out


# -------------------------
# Incremental rebuild logic
# -------------------------


def parse_depfile(dep_path: Path) -> List[Path]:
    """Parse a GCC-style .d depfile into dependency Paths.

    We only return prerequisite file paths (after the first ':').
    """
    try:
        raw = dep_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    # Join line continuations
    raw = raw.replace("\\\n", " ")

    # Split on the first ':' (target: deps...)
    if ":" not in raw:
        return []
    _, rhs = raw.split(":", 1)
    rhs = rhs.strip()

    # Tokenize makefile-ish whitespace with backslash escapes.
    deps: List[str] = []
    cur: List[str] = []
    esc = False
    for ch in rhs:
        if esc:
            cur.append(ch)
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch.isspace():
            if cur:
                deps.append("".join(cur))
                cur = []
            continue
        cur.append(ch)
    if cur:
        deps.append("".join(cur))

    # Remove empty
    out: List[Path] = []
    for d in deps:
        d = d.strip()
        if not d:
            continue
        out.append(Path(d))
    return out


def is_newer(a: Path, b: Path) -> bool:
    """Return True if 'a' has a modification time newer than 'b'."""
    try:
        return a.stat().st_mtime > b.stat().st_mtime
    except OSError:
        return False


def needs_rebuild(
    *,
    project_root: Path,
    src_abs: Path,
    obj_abs: Path,
    dep_abs: Path,
    force: bool,
) -> bool:
    if force:
        return True

    if not obj_abs.exists():
        return True

    # If source is newer than object
    try:
        if src_abs.stat().st_mtime > obj_abs.stat().st_mtime:
            return True
    except OSError:
        return True

    if not dep_abs.exists():
        return True

    deps = parse_depfile(dep_abs)
    if not deps:
        return True

    obj_mtime = 0.0
    try:
        obj_mtime = obj_abs.stat().st_mtime
    except OSError:
        return True

    # If any local dependency is newer than object, rebuild.
    for dep in deps:
        # dep paths are relative to /work (project root) because we compile with relative paths
        dep_abs2 = (project_root / dep).resolve() if not dep.is_absolute() else dep
        try:
            # Only consider deps that exist on the host filesystem.
            # (System headers inside the image won't exist here; image-id changes are handled separately.)
            st = dep_abs2.stat()
        except OSError:
            continue
        if st.st_mtime > obj_mtime:
            return True

    return False


# -------------------------
# Docker helpers + cache
# -------------------------


def docker_available(verbose: bool = False) -> bool:
    try:
        run(["docker", "--version"], check=True, capture=False, verbose=verbose)
        return True
    except Exception:
        return False


def docker_image_exists(image: str, verbose: bool = False) -> bool:
    try:
        run(
            ["docker", "image", "inspect", image],
            check=True,
            capture=False,
            verbose=verbose,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def ensure_image(image: str, verbose: bool = False) -> None:
    if docker_image_exists(image, verbose=verbose):
        return
    eprint(f"Docker image '{image}' not found locally; pulling...")
    run(["docker", "pull", image], check=True, capture=False, verbose=verbose)


def docker_image_id(image: str, verbose: bool = False) -> Optional[str]:
    """Return the image ID (sha256:...) if possible."""
    try:
        cp = run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image],
            check=True,
            capture=True,
            verbose=verbose,
        )
        s = (cp.stdout or "").strip()
        return s or None
    except Exception:
        return None


@dataclasses.dataclass
class BuildCache:
    schema: int = 1
    docker_image: str = ""
    docker_image_id: str = ""
    compile_sig: str = ""
    link_sig: str = ""


def load_cache(path: Path) -> BuildCache:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return BuildCache()
        return BuildCache(
            schema=int(data.get("schema", 1)),
            docker_image=str(data.get("docker_image", "")),
            docker_image_id=str(data.get("docker_image_id", "")),
            compile_sig=str(data.get("compile_sig", "")),
            link_sig=str(data.get("link_sig", "")),
        )
    except Exception:
        return BuildCache()


def save_cache(path: Path, cache: BuildCache) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": cache.schema,
                "docker_image": cache.docker_image,
                "docker_image_id": cache.docker_image_id,
                "compile_sig": cache.compile_sig,
                "link_sig": cache.link_sig,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def signature_for(
    *,
    image: str,
    image_id: str,
    cross_compiler: str,
    base_flags: str,
    c_std: str,
    cpp_std: str,
    include_dirs_rel: Sequence[str],
    extra_args: Sequence[str],
    link_flags: str,
    libs: Sequence[str],
) -> Tuple[str, str]:
    # Keep signatures as stable strings (JSON is an easy canonical form).
    compile_payload = {
        "image": image,
        "image_id": image_id,
        "cross_compiler": cross_compiler,
        "base_flags": base_flags,
        "c_std": c_std,
        "cpp_std": cpp_std,
        "include_dirs": list(include_dirs_rel),
        "extra_args": list(extra_args),
    }
    link_payload = {
        "image": image,
        "image_id": image_id,
        "cross_compiler": cross_compiler,
        "link_flags": link_flags,
        "libs": list(libs),
        "extra_args": list(extra_args),
    }
    return (
        json.dumps(compile_payload, sort_keys=True, separators=(",", ":")),
        json.dumps(link_payload, sort_keys=True, separators=(",", ":")),
    )


# -------------------------
# Docker build script emission
# -------------------------


def emit_bash_build_script(
    *,
    cross_compiler: str,
    base_flags: str,
    include_dirs_rel: Sequence[str],
    extra_args: Sequence[str],
    compile_units: Sequence[SourceUnit],
    all_obj_rel: Sequence[str],
    out_binary_rel: str,
    link_flags: str,
    libs: Sequence[str],
    jobs: int,
    verbose: bool,
) -> str:
    """Generate a bash script that compiles and links inside the container."""

    # Note: everything is relative to /work and we run with -w /work.
    # We use bash arrays to safely handle spaces.

    lines: List[str] = []
    lines.append("#!/usr/bin/env bash")
    lines.append("set -euo pipefail")
    if verbose:
        lines.append("set -x")

    # Basic variables
    lines.append(f"CXX={shlex.quote(cross_compiler)}")

    # Arrays: BASE_FLAGS, INCLUDE_FLAGS, EXTRA_ARGS
    base_list = shlex.split(base_flags) if base_flags.strip() else []

    def bash_array(name: str, items: Sequence[str]) -> None:
        quoted = " ".join(shlex.quote(i) for i in items)
        lines.append(f"{name}=({quoted})")

    bash_array("BASE_FLAGS", base_list)
    bash_array("INCLUDE_FLAGS", [f"-I{d}" for d in include_dirs_rel])
    bash_array("EXTRA_ARGS", list(extra_args))

    # Job control
    j = max(1, int(jobs))
    lines.append(f"MAX_JOBS={j}")
    lines.append("pids=()")
    lines.append(
        "start_job() {\n"
        '  "$@" &\n'
        '  pids+=("$!")\n'
        '  if [ "${#pids[@]}" -ge "$MAX_JOBS" ]; then\n'
        "    # Wait the oldest job to keep at most MAX_JOBS running.\n"
        '    wait "${pids[0]}"\n'
        '    pids=("${pids[@]:1}")\n'
        "  fi\n"
        "}\n"
    )
    lines.append(
        "finish_jobs() {\n"
        "  local pid\n"
        '  for pid in "${pids[@]}"; do\n'
        '    wait "$pid"\n'
        "  done\n"
        "  pids=()\n"
        "}\n"
    )

    # Compile function
    lines.append(
        "compile_one() {\n"
        '  local src="$1"\n'
        '  local obj="$2"\n'
        '  local dep="$3"\n'
        '  local lang="$4"\n'
        '  local std="$5"\n'
        '  mkdir -p "$(dirname "$obj")"\n'
        "  # -MMD/-MP writes a depfile next to the object for fast incremental rebuilds.\n"
        '  "$CXX" "${BASE_FLAGS[@]}" "${INCLUDE_FLAGS[@]}" -x "$lang" -std="$std" \\\n'
        '    -MMD -MP -MF "$dep" -MT "$obj" \\\n'
        '    -c "$src" -o "$obj" "${EXTRA_ARGS[@]}"\n'
        "}\n"
    )

    # Build directory for binary
    # out_binary_rel is already a POSIX-style path (intended for /work inside the container).
    out_bin_parent = PurePosixPath(out_binary_rel).parent.as_posix()
    lines.append(f"mkdir -p {shlex.quote(out_bin_parent)}")

    # Compile steps
    if compile_units:
        lines.append("# ---- Compile ----")
        for u in compile_units:
            # call compile_one "src" "obj" "dep" "lang" "std"
            lines.append(
                "start_job compile_one "
                + " ".join(
                    shlex.quote(x)
                    for x in (
                        u.src_rel_posix,
                        u.obj_rel_posix,
                        u.dep_rel_posix,
                        u.lang,
                        u.std,
                    )
                )
            )
        lines.append("finish_jobs")
    else:
        lines.append("# No compilation needed.")

    # Link step
    lines.append("# ---- Link ----")

    # Objects array
    bash_array("OBJS", list(all_obj_rel))

    # Link flags + libs
    link_list = shlex.split(link_flags) if link_flags.strip() else []
    bash_array("LINK_FLAGS", link_list)
    bash_array("LIBS", [f"-l{lib}" for lib in libs if lib])

    lines.append(
        '"$CXX" "${OBJS[@]}" -o '
        + shlex.quote(out_binary_rel)
        + ' "${LINK_FLAGS[@]}" "${LIBS[@]}" "${EXTRA_ARGS[@]}"'
    )

    return "\n".join(lines) + "\n"


# -------------------------
# Main
# -------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-compile for Wombat using Docker + aarch64-linux-gnu-g++ (incremental + parallel)"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove output directory before building"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Only clean output directory and exit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print commands (and set -x in container)",
        default=False,  # Ensure verbose is False by default
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: run container as root (for write perms on mounted workspace)",
    )
    parser.add_argument(
        "--config",
        default="configs/config.dev.yaml",
        help="Path to configuration file (YAML subset or JSON)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recompilation of all sources (still uses the cache for signatures)",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=None,
        help="Max parallel compile jobs inside the container (default: config.jobs or CPU count)",
    )
    parser.add_argument(
        "--submodules",
        choices=("auto", "all", "none"),
        default=None,
        help="Submodule compilation mode overriding config (auto/all/none)",
    )

    # Capture any extra compiler/linker flags after a '--'
    args, extra = parser.parse_known_args(argv)

    project_root = Path.cwd().resolve()
    cfg_path = Path(args.config)
    config = load_config(cfg_path)

    docker_image = str(config.get("docker_image", "sillyfreak/wombat-cross"))

    if args.ci:
        eprint("Running in CI mode...")

    if not docker_available(verbose=args.verbose):
        eprint(
            "Error: Docker is not available on the system PATH. Please ensure Docker is installed and running."
        )
        return 1

    try:
        ensure_image(docker_image, verbose=args.verbose)
    except Exception as ex:
        eprint(
            f"Error: Failed to ensure Docker image '{docker_image}'. Exception: {ex}"
        )
        return 1

    try:
        img_id = docker_image_id(docker_image, verbose=args.verbose) or ""
    except Exception as ex:
        eprint(
            f"Error: Failed to retrieve Docker image ID for '{docker_image}'. Exception: {ex}"
        )
        return 1

    if not img_id:
        eprint(
            f"Error: Docker image ID for '{docker_image}' could not be determined. Ensure the image is available."
        )
        return 1

    # Output paths (host)
    dirs = config.get("directories", {}) or {}
    out_dir = project_root / str(dirs.get("output", "out"))
    obj_root = out_dir / str(dirs.get("objects", "obj"))
    build_dir = out_dir / str(dirs.get("build", "build"))

    cache_path = out_dir / ".wombat_build_cache.json"

    # Clean
    if args.clean or args.clean_only:
        if out_dir.exists():
            eprint(f"Cleaning: {out_dir}")
            # shutil.rmtree is fine; but keep imports light in hot path.
            import shutil  # stdlib

            shutil.rmtree(out_dir, ignore_errors=True)
        else:
            eprint("Nothing to clean.")

        if args.clean_only:
            return 0

    # Ensure output directories exist (host-side)
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_root.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Gather sources
    src_dir = project_root / str(dirs.get("source", "src"))
    if not src_dir.is_dir():
        eprint(f"Source directory not found: {src_dir}")
        return 1

    project_sources = tuple(
        sorted(
            iter_files(src_dir, (".c", ".cc", ".cpp", ".cxx")),
            key=lambda p: p.as_posix(),
        )
    )

    submodules = discover_submodules(project_root)

    sub_cfg = config.get("submodules", {}) or {}
    mode_cfg = str(sub_cfg.get("mode", "auto")).lower()
    mode = (args.submodules or mode_cfg).lower()
    if mode not in {"auto", "all", "none"}:
        mode = "auto"

    include_dir = project_root / str(dirs.get("include", "include"))
    project_include_dir = include_dir if include_dir.is_dir() else None

    used_subs: List[Submodule] = []
    if mode == "none":
        used_subs = []
    elif mode == "all":
        used_subs = list(submodules)
    else:
        used_subs = detect_used_submodules(
            project_root,
            project_sources,
            submodules,
            project_include_dir,
            verbose=args.verbose,
        )

    sub_sources: List[Path] = []
    for s in used_subs:
        sub_sources.extend(list(s.sources))

    all_sources = tuple(
        sorted((*project_sources, *sub_sources), key=lambda p: p.as_posix())
    )
    if not all_sources:
        eprint("No source files found.")
        return 1

    # Build include dirs (relative to project root, as POSIX, for container)
    include_dirs_rel: List[str] = []
    if project_include_dir:
        include_dirs_rel.append(to_rel_posix(project_include_dir, project_root))
    for s in used_subs:
        if s.include_dir and s.include_dir.is_dir():
            include_dirs_rel.append(to_rel_posix(s.include_dir, project_root))

    # Deduplicate while preserving order
    seen_inc: Set[str] = set()
    include_dirs_rel = [
        d for d in include_dirs_rel if not (d in seen_inc or seen_inc.add(d))
    ]

    # Compiler/linker settings
    compiler_cfg = config.get("compiler", {}) or {}
    linker_cfg = config.get("linker", {}) or {}

    cross_compiler = str(compiler_cfg.get("cross_compiler", "aarch64-linux-gnu-g++"))
    flags = str(compiler_cfg.get("flags", "-Wall")).strip()
    opt = str(compiler_cfg.get("optimization", "-O2")).strip()
    debug = bool(compiler_cfg.get("debug", True))

    base_flags = " ".join(x for x in (flags, opt, "-g" if debug else "") if x)

    c_std = str(compiler_cfg.get("c_standard", "c11"))
    cpp_std = str(compiler_cfg.get("cpp_standard", "c++17"))

    link_flags = str(linker_cfg.get("flags", "")).strip()

    libs_raw = linker_cfg.get("libraries", "")
    if isinstance(libs_raw, str):
        libs = [x for x in libs_raw.split() if x]
    elif isinstance(libs_raw, list):
        libs = [str(x) for x in libs_raw if str(x).strip()]
    else:
        libs = []

    cfg_extra = config.get("extra_args", [])
    if isinstance(cfg_extra, str):
        cfg_extra_list = shlex.split(cfg_extra)
    elif isinstance(cfg_extra, list):
        cfg_extra_list = [str(x) for x in cfg_extra]
    else:
        cfg_extra_list = []

    extra_args = [*cfg_extra_list, *extra]

    # Determine jobs
    jobs_cfg = int(config.get("jobs", 0) or 0)
    jobs = (
        int(args.jobs)
        if args.jobs is not None
        else (jobs_cfg if jobs_cfg > 0 else (os.cpu_count() or 1))
    )
    jobs = max(1, jobs)

    # Cache/signatures
    cache_prev = load_cache(cache_path)
    compile_sig, link_sig = signature_for(
        image=docker_image,
        image_id=img_id,
        cross_compiler=cross_compiler,
        base_flags=base_flags,
        c_std=c_std,
        cpp_std=cpp_std,
        include_dirs_rel=include_dirs_rel,
        extra_args=extra_args,
        link_flags=link_flags,
        libs=libs,
    )

    # If docker image changed (or compile signature changed), force rebuild.
    force_compile = bool(args.force)
    if cache_prev.docker_image and cache_prev.docker_image != docker_image:
        force_compile = True
    if cache_prev.docker_image_id and img_id and cache_prev.docker_image_id != img_id:
        force_compile = True
    if cache_prev.compile_sig and cache_prev.compile_sig != compile_sig:
        force_compile = True

    # Build units
    compile_units: List[SourceUnit] = []
    all_obj_rel: List[str] = []

    for src in all_sources:
        rel = to_rel_posix(src, project_root)

        rel_path = Path(rel)  # uses POSIX separators already
        obj_rel = (
            Path(str(dirs.get("output", "out")))
            / str(dirs.get("objects", "obj"))
            / rel_path
        ).with_suffix(".o")
        dep_rel = obj_rel.with_suffix(".d")

        ext = src.suffix.lower()
        if ext == ".c":
            lang = "c"
            std = c_std
        else:
            lang = "c++"
            std = cpp_std

        all_obj_rel.append(obj_rel.as_posix())

        obj_abs = project_root / obj_rel
        dep_abs = project_root / dep_rel

        if needs_rebuild(
            project_root=project_root,
            src_abs=src,
            obj_abs=obj_abs,
            dep_abs=dep_abs,
            force=force_compile,
        ):
            compile_units.append(
                SourceUnit(
                    src_abs=src,
                    src_rel_posix=rel,
                    obj_rel_posix=obj_rel.as_posix(),
                    dep_rel_posix=dep_rel.as_posix(),
                    lang=lang,
                    std=std,
                )
            )

    # Determine if linking is necessary
    output_name = str(config.get("output_name", "botball_user_program"))
    out_bin_rel = (
        Path(str(dirs.get("output", "out")))
        / str(dirs.get("build", "build"))
        / output_name
    ).as_posix()
    out_bin_abs = project_root / out_bin_rel

    needs_link = False
    if not out_bin_abs.exists():
        needs_link = True
    else:
        # If any object is newer than the binary
        try:
            bin_mtime = out_bin_abs.stat().st_mtime
        except OSError:
            bin_mtime = 0.0
        for o in all_obj_rel:
            p = project_root / o
            try:
                if p.stat().st_mtime > bin_mtime:
                    needs_link = True
                    break
            except OSError:
                # missing object => we must link after compile
                needs_link = True
                break

    if compile_units:
        needs_link = True

    if cache_prev.link_sig and cache_prev.link_sig != link_sig:
        needs_link = True

    # Fast path: nothing to do
    if not compile_units and not needs_link:
        print(f"Up to date: {out_bin_abs}")
        return 0

    # Emit the bash build script into the workspace (so docker can execute it).
    internal_dir = out_dir / ".wombat_build"
    internal_dir.mkdir(parents=True, exist_ok=True)
    build_sh = internal_dir / "build.sh"

    script = emit_bash_build_script(
        cross_compiler=cross_compiler,
        base_flags=base_flags,
        include_dirs_rel=include_dirs_rel,
        extra_args=extra_args,
        compile_units=compile_units,
        all_obj_rel=all_obj_rel,
        out_binary_rel=out_bin_rel,
        link_flags=link_flags,
        libs=libs,
        jobs=jobs,
        verbose=args.verbose,
    )
    build_sh.write_text(script, encoding="utf-8")

    # Docker options
    host_arch = platform.machine().lower()

    docker_cmd: List[str] = ["docker", "run", "--rm"]

    if args.ci:
        docker_cmd += ["--user", "root"]

    # On Apple Silicon (arm64 hosts), force linux/amd64 to suppress warnings and ensure image compatibility.
    if host_arch in ("arm64", "aarch64", "arm64e"):
        docker_cmd += ["--platform", "linux/amd64"]

    # Robust mount syntax across Windows/macOS/Linux
    docker_cmd += [
        "--mount",
        f"type=bind,source={str(project_root)},target=/work",
        "-w",
        "/work",
        docker_image,
        "bash",
        (Path(out_bin_rel).parents[1] / ".wombat_build" / "build.sh").as_posix(),
    ]

    # NOTE: the last argument is a path *inside the container*, but because we're in -w /work,
    # using the same relative path works.

    if args.verbose:
        eprint("Build plan:")
        eprint(f"  Sources total: {len(all_sources)}")
        eprint(f"  To compile:    {len(compile_units)}")
        eprint(f"  To link:       {needs_link}")
        eprint(f"  Jobs:          {jobs}")
        eprint(f"  Output:        {out_bin_rel}")

    try:
        run(docker_cmd, check=True, capture=False, verbose=args.verbose)
    except FileNotFoundError:
        eprint("Docker executable not found on PATH.")
        return 1
    except subprocess.CalledProcessError:
        eprint("Build failed. See errors above.")
        return 1

    # Update cache
    cache_new = BuildCache(
        schema=1,
        docker_image=docker_image,
        docker_image_id=img_id,
        compile_sig=compile_sig,
        link_sig=link_sig,
    )
    try:
        save_cache(cache_path, cache_new)
    except Exception as ex:
        if args.verbose:
            eprint(f"Warning: could not write cache file: {ex}")

    print("Build completed successfully.")
    print(f"Executable location: {out_bin_abs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
