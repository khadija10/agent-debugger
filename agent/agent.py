import os
import sys
import json
import subprocess
import re
from dotenv import load_dotenv
from groq import Groq
from apply_patch import apply_patch

# =========================
# 0) Chargement de la config
# =========================
CONFIG_PATH = "agent/config.json"
CONTEXT_PATH = "agent/context.txt"
PROMPT_PATH = "agent/prompt.txt"
OUTPUT_JSON = "agent/last_patch.json"

if not os.path.exists(CONFIG_PATH):
    print("❌ agent/config.json introuvable")
    sys.exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

project_path = config.get("project_path")
python_interpreter = config.get("venv_path", "python")

if not project_path or not os.path.exists(project_path):
    print("❌ project_path invalide dans config.json")
    sys.exit(1)

# =========================
# 1) Fichier cible
# =========================
if len(sys.argv) == 2:
    script_to_run = sys.argv[1]
else:
    script_to_run = os.path.join(project_path, "scripts", "script_a.py")

if not os.path.exists(script_to_run):
    print(f"❌ Fichier introuvable : {script_to_run}")
    sys.exit(1)

# =========================
# 2) API KEY
# =========================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY manquant")

client = Groq(api_key=api_key)

# =========================
# 3) Charger contexte + prompt template
# =========================
with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
    context_text = f.read()

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    prompt_template = f.read()

# =========================
# 4) Exécution du script cible
# =========================
completed = subprocess.run(
    [python_interpreter, script_to_run],
    capture_output=True,
    text=True
)

stderr_text = completed.stderr.strip()

if not stderr_text:
    print("🎉 Aucune erreur détectée.")
    sys.exit(0)

print("=== Erreur détectée ===")
print(stderr_text)

# =========================
# 5) Identifier le fichier fautif
# =========================
matches = re.findall(r'File "(.+?\.py)"', stderr_text)
faulty_file = matches[-1] if matches else script_to_run

print(f"\n📌 Fichier fautif : {faulty_file}")

# Rendre absolu si nécessaire
if not os.path.isabs(faulty_file):
    faulty_file = os.path.join(project_path, faulty_file)

if not os.path.exists(faulty_file):
    print("❌ Fichier fautif introuvable")
    sys.exit(1)

# =========================
# 6) Charger le code fautif
# =========================
with open(faulty_file, "r", encoding="utf-8") as f:
    faulty_code = f.read()

prompt_filled = prompt_template.format(code=faulty_code, error=stderr_text)

messages = [
    {"role": "system", "content": context_text},
    {"role": "user", "content": prompt_filled},
]

# =========================
# 7) Appel modèle Groq
# =========================
completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    max_tokens=2000,
    temperature=0
)

response_text = completion.choices[0].message.content

print("\n=== Réponse brute du modèle ===")
print(response_text)

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    f.write(response_text)

# =========================
# 8) Parser JSON
# =========================
try:
    patch_data = json.loads(response_text)
except:
    print("❌ Le modèle n'a pas renvoyé un JSON valide.")
    sys.exit(1)

patch_code = patch_data.get("patch")
diagnostic = patch_data.get("diagnostic", "")

if not patch_code:
    print("❌ Aucun champ 'patch' trouvé.")
    sys.exit(1)

# =========================
# 8.5 Déséchappage agressif
# =========================
def aggressively_unescape_patch(text):
    if "\\n" in text or "\\t" in text or "\\\"" in text:
        try:
            return json.loads(text)
        except:
            pass
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        try:
            return json.loads(text)
        except:
            pass
    return text

patch_code = aggressively_unescape_patch(patch_code)

# double tentative si encore échappé
if isinstance(patch_code, str) and "\\n" in patch_code:
    try:
        patch_code = json.loads(patch_code)
    except:
        pass

# =========================
# 9) Affichage utilisateur
# =========================
print("\n=== CORRECTION PROPOSÉE ===")
print("\n--- Diagnostic ---")
print(diagnostic)
print("\n--- Patch ---\n")
print(patch_code)
print("\n------------------------------------------\n")

confirm = input("Appliquer la correction ? (o/n) : ").strip().lower()
if confirm not in ("o", "oui", "y"):
    print("❌ Correction annulée.")
    sys.exit(0)

# =========================
# 10) Appliquer via apply_patch
# =========================
apply_patch(faulty_file, patch_code, project_path)

# =========================
# 11) Réexécuter le script
# =========================
print("\n🔄 Réexécution...\n")
completed_after = subprocess.run(
    [python_interpreter, script_to_run],
    capture_output=True,
    text=True
)

print("=== stdout ===")
print(completed_after.stdout)
print("=== stderr ===")
print(completed_after.stderr)
