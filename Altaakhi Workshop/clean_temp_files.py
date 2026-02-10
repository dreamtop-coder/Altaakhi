import os
import shutil


def remove_pyc_and_pycache(root_dir):
    removed_files = 0
    removed_dirs = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove .pyc files
        for filename in filenames:
            if filename.endswith(".pyc"):
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                    removed_files += 1
                except Exception:
                    pass
        # Remove __pycache__ directories
        for dirname in dirnames:
            if dirname == "__pycache__":
                dir_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs += 1
                except Exception:
                    pass
    print(
        f"Removed {removed_files} .pyc files and {removed_dirs} __pycache__ directories."
    )


if __name__ == "__main__":
    remove_pyc_and_pycache(os.getcwd())
    # يمكنك حذف السكريبتات المؤقتة يدويًا بعد التشغيل
    print("تنظيف الملفات المؤقتة تم بنجاح.")
