import os
import shutil
import sys

REMOVE_FILES_EXT = (".pyc", ".pyo", ".log", ".tmp", ".bak", ".old")

REMOVE_DIRS = (
    "__pycache__",
    "venv",
    ".venv",
    "staticfiles",
)

REMOVE_FILES_EXACT = (
    "db.sqlite3",
    ".DS_Store",
    "Thumbs.db",
)


def clean_project(root_dir):
    removed_files = []
    removed_dirs = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # حذف المجلدات
        for dirname in list(dirnames):
            if dirname in REMOVE_DIRS:
                dir_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs.append(dir_path)
                    dirnames.remove(dirname)
                except Exception:
                    pass

        # حذف الملفات
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            if filename.endswith(REMOVE_FILES_EXT) or filename in REMOVE_FILES_EXACT:
                try:
                    os.remove(file_path)
                    removed_files.append(file_path)
                except Exception:
                    pass

    print("\n🧹 Clean finished\n")
    print(f"✔ Removed files: {len(removed_files)}")
    print(f"✔ Removed directories: {len(removed_dirs)}")

    if removed_files:
        print("\nFiles:")
        for f in removed_files:
            print(" -", f)

    if removed_dirs:
        print("\nDirectories:")
        for d in removed_dirs:
            print(" -", d)


if __name__ == "__main__":
    # Force UTF-8 encoding for stdout if possible
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        try:
            import codecs

            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        except Exception:
            pass
    clean_project(os.getcwd())
    print("\n🚀 المشروع أصبح نظيف وجاهز للرفع")
