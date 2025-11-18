import streamlit as st
import subprocess
import os
import json

# =========================
# Lire la config
# =========================
config_file = "agent/config.json"
if not os.path.exists(config_file):
    st.error("⚠️ config.json introuvable !")
    st.stop()

with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)

project_path = config.get("project_path")
python_interpreter = config.get("venv_path", "python")

if not project_path or not os.path.exists(project_path):
    st.error("⚠️ project_path invalide dans config.json !")
    st.stop()

# =========================
# Titre
# =========================
st.title("Agent Debugger - Analyse de script Python")

# =========================
# Choisir un script à analyser
# =========================
scripts_folder = os.path.join(project_path, "scripts")
all_scripts = [f for f in os.listdir(scripts_folder) if f.endswith(".py")]

script_selected = st.selectbox("Choisir un script :", all_scripts)

# =========================
# Bouton pour analyser
# =========================
if st.button("Analyser et corriger"):
    script_path = os.path.join(scripts_folder, script_selected)
    
    # Lancer agent.py sur le script sélectionné
    process = subprocess.run(
        [python_interpreter, os.path.join(project_path, "agent/agent.py"), script_path],
        capture_output=True,
        text=True
    )

    # Afficher la sortie standard (stdout) et les erreurs (stderr)
    st.subheader("=== Sortie du script corrigé ===")
    st.code(process.stdout)

    st.subheader("=== Erreurs éventuelles ===")
    st.code(process.stderr)

    # Afficher le JSON de correction généré
    json_file = os.path.join(project_path, "agent/last_patch.json")
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            patch_json = f.read()
        st.subheader("=== Correction proposée (JSON) ===")
        st.code(patch_json)
    else:
        st.warning("Aucune correction générée.")
