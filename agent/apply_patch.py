import os
from shutil import copyfile

def apply_patch(script_path: str, patch_code: str):
    """
    Applique un patch MINIMAL :
    - Ne remplace que la fonction corrigée
    - Ignore TOUT ce qui est en dehors de la fonction (ex: result = ...)
    - Place les sauvegardes dans scripts/backups/
    """

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script introuvable : {script_path}")

    # ===========================
    # 1) Créer dossier backups
    # ===========================
    script_dir = os.path.dirname(script_path)
    backup_dir = os.path.join(script_dir, "backups")

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    script_name = os.path.basename(script_path)
    backup_path = os.path.join(backup_dir, script_name + ".bak")

    # Sauvegarde propre
    copyfile(script_path, backup_path)
    print(f"💾 Backup créé : {backup_path}")

    # ===========================
    # 2) Lire fichier original
    # ===========================
    with open(script_path, "r", encoding="utf-8") as f:
        original = f.readlines()

    # ===========================
    # 3) Extraire la fonction du patch
    # ===========================
    patch_lines = patch_code.splitlines()

    func_start = None
    for i, line in enumerate(patch_lines):
        if line.strip().startswith("def "):
            func_start = i
            break

    if func_start is None:
        print("❌ Patch invalide : aucune fonction trouvée")
        return False

    func_name = patch_lines[func_start].strip().split()[1].split("(")[0]

    # extraire uniquement le bloc de fonction
    func_block = []
    for line in patch_lines[func_start:]:
        if line.startswith("def ") and len(func_block) > 0:
            break
        func_block.append(line)

    patched = [(l if l.endswith("\n") else l + "\n") for l in func_block]

    # ===========================
    # 4) Localiser la fonction originale
    # ===========================
    start = None
    for i, line in enumerate(original):
        if line.strip().startswith(f"def {func_name}("):
            start = i
            break

    if start is None:
        print(f"⚠️ Fonction {func_name} introuvable → ajout à la fin.")
        new = original + ["\n"] + patched

    else:
        # trouver fin du bloc existant
        end = start + 1
        while end < len(original) and (
            original[end].startswith(" ") or original[end].startswith("\t")
        ):
            end += 1

        # Remplacement propre
        new = original[:start] + patched + original[end:]

    # ===========================
    # 5) Écrire fichier final
    # ===========================
    with open(script_path, "w", encoding="utf-8") as f:
        f.writelines(new)

    print(f"✅ Fonction {func_name} corrigée dans {script_path}")
    return True
