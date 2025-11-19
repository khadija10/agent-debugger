import os
import json
import subprocess
from dotenv import load_dotenv
from groq import Groq
import sys
from apply_patch import apply_patch

# =========================
# 0) Charger configuration depuis config.json
# =========================
config_file = "agent/config.json"
project_path = None
python_interpreter = "python"

if os.path.exists(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
        project_path = config.get("project_path")
        python_interpreter = config.get("venv_path", "python")

# =========================
# 1) Vérifier argument ou config
# =========================
if len(sys.argv) == 2:
    script_to_run = sys.argv[1]
elif project_path:
    script_to_run = os.path.join(project_path, "scripts/script_a.py")
else:
    print("Usage : python agent.py chemin_du_script.py (ou config.json existante)")
    sys.exit(1)

if not os.path.exists(script_to_run):
    print(f"Fichier cible introuvable : {script_to_run}")
    sys.exit(1)

# =========================
# 2) Charger la clé API Groq
# =========================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY non trouvé dans .env")

client = Groq(api_key=api_key)

# =========================
# 3) Chemins pour agent
# =========================
context_file = "agent/context.txt"
prompt_file = "agent/prompt.txt"
json_output = "agent/last_patch.json"

# =========================
# 4) Lire contexte et prompt
# =========================
with open(context_file, "r", encoding="utf-8") as f:
    context_text = f.read()

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read()

# =========================
# 5) Exécuter le script cible
# =========================
completed = subprocess.run(
    [python_interpreter, script_to_run],
    capture_output=True,
    text=True
)

code_content = open(script_to_run, "r", encoding="utf-8").read()
error_content = completed.stderr.strip()

if not error_content:
    print("Aucune erreur détectée dans le script.")
    exit()

print("Erreur détectée dans le script :")
print(error_content)

# =========================
# 6) Construire la prompt
# =========================
prompt_filled = prompt_template.format(code=code_content, error=error_content)
messages = [
    {"role": "system", "content": context_text},
    {"role": "user", "content": prompt_filled}
]

# =========================
# 7) Appel Groq pour obtenir le patch
# =========================
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    max_tokens=500,
    temperature=0
)

response = completion.choices[0].message.content

print("\nRéponse JSON du modèle :")
print(response)

# =========================
# 8) Sauvegarder la réponse JSON brute
# =========================
with open(json_output, "w", encoding="utf-8") as f:
    f.write(response)

# =========================
# 9) Parser le JSON
# =========================
try:
    patch_data = json.loads(response)
except json.JSONDecodeError:
    print("Le modèle n'a pas renvoyé un JSON valide.")
    exit()

patch_code = patch_data.get("patch")
if not patch_code:
    print("Aucun patch trouvé dans la réponse.")
    exit()

# =========================
# 10) Vérification : le patch doit contenir UNIQUEMENT la fonction corrigée
# =========================
lines = [l.strip() for l in patch_code.splitlines() if l.strip()]

# doit commencer par def
if not lines[0].startswith("def "):
    print("Patch invalide : doit commencer par une définition de fonction.")
    exit()

# aucun code global autorisé
for line in lines:
    if line.startswith("print(") or "=" in line and "def " not in line:
        if not line.startswith(("def ", "return", "if ", "elif ", "else:", "#", "@")):
            print("Patch invalide : contient du code global ou des affectations hors fonction.")
            exit()

# =========================
# 11) Appliquer le patch minimal
# =========================
apply_patch(script_to_run, patch_code)

# =========================
# 12) Relancer le script corrigé
# =========================
print("\n=== Exécution du script corrigé ===\n")
completed_after = subprocess.run(
    [python_interpreter, script_to_run],
    capture_output=True,
    text=True
)

print("== stdout ==")
print(completed_after.stdout)
print("== stderr ==")
print(completed_after.stderr)
