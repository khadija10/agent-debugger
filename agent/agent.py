import os
import json
import subprocess
from shutil import copyfile
from dotenv import load_dotenv
from groq import Groq
import sys

# =========================
# Vérifier argument
# =========================
if len(sys.argv) != 2:
    print("Usage : python agent.py chemin_du_script.py")
    sys.exit(1)

script_to_run = sys.argv[1]

if not os.path.exists(script_to_run):
    print(f"❌ Fichier cible introuvable : {script_to_run}")
    sys.exit(1)

# =========================
# 1) Charger la clé API
# =========================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY non trouvé dans .env")

client = Groq(api_key=api_key)

# =========================
# 2) Chemins pour agent
# =========================
context_file = "agent/context.txt"
prompt_file = "agent/prompt.txt"
json_output = "agent/last_patch.json"

# =========================
# 3) Lire le contexte et la prompt
# =========================
with open(context_file, "r", encoding="utf-8") as f:
    context_text = f.read()

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read()

# =========================
# 4) Exécuter le script cible
# =========================
completed = subprocess.run(
    ["python", script_to_run],
    capture_output=True,
    text=True
)

code_content = open(script_to_run, "r", encoding="utf-8").read()
error_content = completed.stderr.strip()

if not error_content:
    print("🎉 Aucune erreur détectée dans le script.")
    exit()

print("❗ Erreur détectée :")
print(error_content)

# =========================
# 5) Construire la prompt
# =========================
prompt_filled = prompt_template.format(code=code_content, error=error_content)

messages = [
    {"role": "system", "content": context_text},
    {"role": "user", "content": prompt_filled}
]

# =========================
# 6) Appel Groq
# =========================
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    max_tokens=500,
    temperature=0
)

response = completion.choices[0].message.content
print("\n📩 Réponse JSON du modèle :")
print(response)

# =========================
# 7) Sauvegarder le JSON
# =========================
with open(json_output, "w", encoding="utf-8") as f:
    f.write(response)

# =========================
# 8) Parser le JSON
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
# 9) Appliquer le patch ligne par ligne (étape 6)
# =========================
backup_file = script_to_run + ".bak"
copyfile(script_to_run, backup_file)
print(f"💾 Backup du fichier original créé : {backup_file}")

with open(script_to_run, "r", encoding="utf-8") as f:
    original_lines = f.readlines()

patched_lines = patch_code.splitlines(keepends=True)

new_lines = []
max_len = max(len(original_lines), len(patched_lines))
for i in range(max_len):
    patched_line = patched_lines[i] if i < len(patched_lines) else ""
    orig_line = original_lines[i] if i < len(original_lines) else ""
    new_lines.append(patched_line if patched_line != orig_line else orig_line)

with open(script_to_run, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"\n✅ Patch appliqué au fichier : {script_to_run}")

# =========================
# 10) Relancer le script corrigé
# =========================
print("\n🔄 Exécution du script corrigé...\n")
completed_after = subprocess.run(
    ["python", script_to_run],
    capture_output=True,
    text=True
)

print("== stdout ==")
print(completed_after.stdout)
print("== stderr ==")
print(completed_after.stderr)
