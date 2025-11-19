import os
from shutil import copyfile

def apply_patch(faulty_file: str, patch_code: str):
    """
    Applique un patch sur le fichier donné après avoir fait un backup.
    """

    if not os.path.exists(faulty_file):
        raise FileNotFoundError(f"Fichier fautif introuvable : {faulty_file}")

    # =========================
    # Backup
    # =========================
    backup_file = faulty_file + ".bak"
    copyfile(faulty_file, backup_file)
    print(f"\n💾 Backup sauvegardé : {backup_file}")

    # =========================
    # Écriture du patch
    # =========================
    with open(faulty_file, "w", encoding="utf-8") as f:
        f.write(patch_code)
        if not patch_code.endswith("\n"):
            f.write("\n")

    print(f"✅ Patch appliqué : {faulty_file}")
