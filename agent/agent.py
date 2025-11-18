import os
from dotenv import load_dotenv
from groq import Groq
import subprocess

# charger .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY non trouvé dans .env")

client = Groq(api_key=api_key)

# chemins
context_file = "agent/context.txt"
prompt_file = "agent/prompt.txt"
script_to_run = "scripts/script_a.py"

# lire le contexte et la prompt
with open(context_file, "r", encoding="utf-8") as f:
    context_text = f.read()

with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read()

# exécuter le script et récupérer l'erreur
completed = subprocess.run(
    ["python", script_to_run],
    capture_output=True,
    text=True
)

code_content = open(script_to_run, "r", encoding="utf-8").read()
error_content = completed.stderr.strip()

# créer la prompt finale
prompt_filled = prompt_template.format(code=code_content, error=error_content)

# envoyer à Groq
messages = [
    {"role": "system", "content": context_text},
    {"role": "user", "content": prompt_filled}
]

completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    max_tokens=300,
    temperature=0.0
)

response = completion.choices[0].message.content
print("Réponse JSON :\n", response)
