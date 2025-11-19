import os
from shutil import copyfile

def apply_patch(file_path: str, patch_code: str, project_path: str):
    """
    Applique un patch minimal :
    - Le patch doit contenir UNE SEULE fonction complète (débutant par "def")
    - On remplace UNIQUEMENT cette fonction dans le fichier cible
    - Aucun code global n'est modifié
    - Le backup est déplacé dans scripts/backups/
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    # ============================
    # 1) Préparation du dossier backups
    # ============================
    backup_dir = os.path.join(project_path, "scripts", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    base_name = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, base_name + ".bak")

    # Backup
    copyfile(file_path, backup_path)
    print(f"💾 Backup créé : {backup_path}")

    # ============================
    # 2) Lire le fichier original
    # ============================
    with open(file_path, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    # ============================
    # 3) Extraire la fonction du patch
    # ============================
    patch_lines = patch_code.splitlines()

    # Trouver le def
    func_start_idx = None
    for i, line in enumerate(patch_lines):
        if line.strip().startswith("def "):
            func_start_idx = i
            break

    if func_start_idx is None:
        print("❌ Patch invalide : aucune fonction trouvée.")
        return False

    full_func = []
    for line in patch_lines[func_start_idx:]:
        if line.startswith("def ") and len(full_func) > 0:
            break
        full_func.append(line)

    # Ajouter \n à chaque ligne
    full_func = [(l if l.endswith("\n") else l + "\n") for l in full_func]

    # Nom de la fonction
    func_name = patch_lines[func_start_idx].strip().split()[1].split("(")[0]

    # ============================
    # 4) Trouver la fonction dans le fichier original
    # ============================
    start = None
    for i, line in enumerate(original_lines):
        if line.strip().startswith(f"def {func_name}("):
            start = i
            break

    if start is None:
        print(f"⚠️ Fonction {func_name} non trouvée → ajout à la fin.")
        new_lines = original_lines + ["\n"] + full_func
    else:
        # Trouver la fin du bloc
        end = start + 1
        while end < len(original_lines) and (
            original_lines[end].startswith(" ") or original_lines[end].startswith("\t")
        ):
            end += 1

        new_lines = original_lines[:start] + full_func + original_lines[end:]

    # ============================
    # 5) Écriture du fichier corrigé
    # ============================
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Fonction {func_name} remplacée dans {file_path}")

    return True
