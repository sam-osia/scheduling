import shutil
from pathlib import Path

backend_dir = Path(__file__).parent

# Remove directories
for dir_name in ["uploads", "outputs", "database"]:
    dir_path = backend_dir / dir_name
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(exist_ok=True)