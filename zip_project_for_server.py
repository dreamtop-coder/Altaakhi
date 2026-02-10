import os
import zipfile

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_NAME = "altaakhi_project_with_db.zip"
EXCLUDE_DIRS = {"__pycache__", "venv", ".venv", "staticfiles"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".log", ".tmp", ".bak", ".old"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}


def should_include(file_path):
    rel_path = os.path.relpath(file_path, PROJECT_DIR)
    parts = rel_path.split(os.sep)
    for part in parts:
        if part in EXCLUDE_DIRS:
            return False
    if os.path.splitext(file_path)[1] in EXCLUDE_EXTS:
        return False
    if os.path.basename(file_path) in EXCLUDE_FILES:
        return False
    return True


def zip_project():
    zip_path = os.path.join(PROJECT_DIR, ZIP_NAME)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                file_path = os.path.join(root, file)
                if should_include(file_path):
                    arcname = os.path.relpath(file_path, PROJECT_DIR)
                    zipf.write(file_path, arcname)
    print(f"تم إنشاء الملف المضغوط: {zip_path}")


if __name__ == "__main__":
    print("تنظيف الملفات المؤقتة...")
    os.system("python clean_temp_files.py")
    print("ضغط المشروع مع قاعدة البيانات...")
    zip_project()
    print("تم بنجاح! يمكنك الآن إرسال altaakhi_project_with_db.zip إلى السيرفر.")
