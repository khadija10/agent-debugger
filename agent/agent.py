import os
import json
import subprocess
from shutil import copyfile
from dotenv import load_dotenv
from groq import Groq
import sys

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
    print(f"❌ Fichier cible introuvable : {script_to_run}")
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
    print("🎉 Aucune erreur détectée dans le script.")
    exit()

# Windows safe print
print("Erreur détectée :")
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
# 8) Sauvegarder le JSON
# =========================
with open(json_output, "w", encoding="utf-8") as f:
    f.write(response)

# =========================
# 9) Parser le JSON
# =========================
try:
    patch_data = json.loads(response)
except json.JSONDecodeError:
    print("❌ Le modèle n'a pas renvoyé un JSON valide !")
    exit()

patch_code = patch_data.get("patch")
if not patch_code:
    print("❌ Aucun patch trouvé dans la réponse.")
    exit()

# =========================
# 10) Appliquer le patch uniquement sur la fonction ciblée
# =========================
backup_file = script_to_run + ".bak"
copyfile(script_to_run, backup_file)
print(f"💾 Backup du fichier original créé : {backup_file}")

with open(script_to_run, "r", encoding="utf-8") as f:
    original_lines = f.readlines()

# Préparer les lignes du patch
patched_lines = [line + "\n" for line in patch_code.splitlines()]

# Identifier le nom de la fonction du patch
first_line = patched_lines[0].strip()
if first_line.startswith("def "):
    func_name = first_line.split()[1].split("(")[0]
else:
    func_name = None

if func_name:
    # Trouver la fonction correspondante dans l'original
    start_index = None
    for i, line in enumerate(original_lines):
        if line.strip().startswith(f"def {func_name}("):
            start_index = i
            break

    if start_index is not None:
        # Trouver la fin de la fonction existante
        end_index = start_index + 1
        while end_index < len(original_lines) and (original_lines[end_index].startswith(' ') or original_lines[end_index].startswith('\t')):
            end_index += 1
        # Remplacer uniquement la fonction
        new_lines = original_lines[:start_index] + patched_lines + original_lines[end_index:]
    else:
        # Fonction non trouvée → ajouter le patch à la fin du fichier
        new_lines = original_lines + ["\n"] + patched_lines
else:
    # Pas de fonction détectée dans le patch → ne rien modifier
    print("⚠️ Patch ne contient pas de fonction identifiable, aucun changement effectué.")
    new_lines = original_lines

with open(script_to_run, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"\n✅ Patch appliqué au fichier : {script_to_run}")

# =========================
# 11) Relancer le script corrigé
# =========================
print("\n🔄 Exécution du script corrigé...\n")
completed_after = subprocess.run(
    [python_interpreter, script_to_run],
    capture_output=True,
    text=True
)

print("== stdout ==")
print(completed_after.stdout)
print("== stderr ==")
print(completed_after.stderr)
