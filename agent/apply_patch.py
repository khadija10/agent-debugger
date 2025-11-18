import json
import sys
import os
from shutil import copyfile

def apply_patch_line_by_line(json_file, target_file):
    """Applique un patch JSON ligne par ligne sur un fichier Python."""
    
    if not os.path.exists(json_file):
        print(f"❌ Fichier JSON introuvable : {json_file}")
        return

    if not os.path.exists(target_file):
        print(f"❌ Fichier cible introuvable : {target_file}")
        return

    # Charger le JSON
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("❌ Impossible de lire le JSON :", e)
        return

    patch_code = data.get("patch")
    if not patch_code:
        print("❌ Le JSON ne contient pas de champ 'patch'.")
        return

    # Créer un backup du fichier cible
    backup_file = target_file + ".bak"
    copyfile(target_file, backup_file)
    print(f"💾 Backup créé : {backup_file}")

    # Lire le fichier original
    with open(target_file, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    patched_lines = patch_code.splitlines(keepends=True)

    # Appliquer le patch ligne par ligne
    new_lines = []
    max_len = max(len(original_lines), len(patched_lines))
    for i in range(max_len):
        patched_line = patched_lines[i] if i < len(patched_lines) else ""
        orig_line = original_lines[i] if i < len(original_lines) else ""
        new_lines.append(patched_line if patched_line != orig_line else orig_line)

    # Écrire le fichier corrigé
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Patch appliqué avec succès à {target_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python apply_patch.py patch.json fichier_cible.py")
        sys.exit(1)

    json_file = sys.argv[1]
    target_file = sys.argv[2]

    apply_patch_line_by_line(json_file, target_file)
