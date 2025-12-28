
import os
import subprocess

target_dir = r"C:\Users\yenshilun\Desktop\20251225 Skyrim AI"
os.chdir(target_dir)

# 1. 建立 .gitignore
with open(".gitignore", "w", encoding="utf-8") as f:
    f.write("__pycache__/\n*.xml\n*.pyc\n")

# 2. 建立 README.md (如果不存在)
if not os.path.exists("README.md"):
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# Skyrim Mod AI Translation Tool\n\nA local AI tool to translate Skyrim mods using Ollama.\n")

# 3. Git 操作
def run_git(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    print(f"git {' '.join(args)}: {result.stdout.strip()} {result.stderr.strip()}")

# 初始化
if not os.path.exists(".git"):
    run_git(["init"])

run_git(["add", "."])
run_git(["commit", "-m", "Initial commit: AI Translate Tool"])
run_git(["branch", "-M", "main"])

print("Git repository initialized successfully!")
