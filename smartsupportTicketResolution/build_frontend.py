import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE_DIR, "frontend", "dist")
STATIC = os.path.join(BASE_DIR, "static")

if not os.path.isdir(DIST):
    raise SystemExit("frontend/dist not found. Run npm run build first.")

os.makedirs(STATIC, exist_ok=True)

for name in os.listdir(STATIC):
    path = os.path.join(STATIC, name)

    if name == ".gitkeep":
        continue

    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

for name in os.listdir(DIST):
    src = os.path.join(DIST, name)
    dst = os.path.join(STATIC, name)

    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)

print("React build copied to Flask static/")
