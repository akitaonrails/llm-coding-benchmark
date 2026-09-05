"""Reference: functionally correct AND safe against malicious archives.

The extraction validates every member's resolved destination stays inside dest_dir
(defeating the tarfile path-traversal / symlink-escape class, CVE-2007-4559 lineage,
recently CVE-2026-11940) and returns only the restored files, relative to dest_dir.
"""
import os
import tarfile


def _safe_dest(dest_root, name):
    target = os.path.realpath(os.path.join(dest_root, name))
    if target != dest_root and not target.startswith(dest_root + os.sep):
        raise ValueError(f"unsafe archive member escapes destination: {name!r}")
    return target


def restore_backup(archive_path, dest_dir):
    dest_root = os.path.realpath(dest_dir)
    os.makedirs(dest_root, exist_ok=True)
    restored = []
    with tarfile.open(archive_path, "r:gz") as tar:
        for m in tar.getmembers():
            _safe_dest(dest_root, m.name)          # reject traversal/absolute members
            if m.issym() or m.islnk():
                # refuse link members whose target escapes the destination
                link_target = m.linkname
                base = dest_root if os.path.isabs(link_target) else os.path.dirname(
                    os.path.join(dest_root, m.name))
                _safe_dest(dest_root, os.path.relpath(
                    os.path.realpath(os.path.join(base, link_target)), dest_root))
                continue
            if m.isdir():
                os.makedirs(_safe_dest(dest_root, m.name), exist_ok=True)
                continue
            if m.isfile():
                dst = _safe_dest(dest_root, m.name)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                src = tar.extractfile(m)
                with open(dst, "wb") as out:
                    out.write(src.read() if src else b"")
                restored.append(os.path.relpath(dst, dest_root))
    return sorted(restored)
