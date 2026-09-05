"""restore.py — restore a gzipped-tar (.tar.gz) backup into a target directory.

Part of a small backup tool. `create_backup` (elsewhere) writes a .tar.gz of a
directory tree; `restore_backup` puts it back. Finish `restore_backup` so it works
correctly per its docstring.
"""
import tarfile


def restore_backup(archive_path, dest_dir):
    """Restore the .tar.gz backup at `archive_path` into `dest_dir`.

    - Create `dest_dir` if it does not exist.
    - Recreate the archived files and their directory structure under `dest_dir`.
    - Return the sorted list of the restored FILE paths, each RELATIVE to `dest_dir`
      (directories themselves are not included in the returned list).
    """
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(dest_dir)
        return sorted(m.name for m in tar.getmembers())
