import json
import sys

def apply_patch(json_file, target_file):
    """Applique le patch contenu dans un fichier JSON à un fichier Python."""
    
    # Charger le JSON
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("❌ Impossible de lire le JSON :", e)
        return
    
    if "patch" not in data:
        print("❌ Le JSON ne contient pas de champ 'patch'.")
        return
    
    patch = data["patch"]

    # Écrire le patch dans le fichier cible
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(patch)
        print(f"✅ Patch appliqué avec succès à {target_file}")
    except Exception as e:
        print("❌ Impossible d'écrire dans le fichier :", e)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python apply_patch.py patch.json fichier_cible.py")
        sys.exit(1)

    json_file = sys.argv[1]
    target_file = sys.argv[2]

    apply_patch(json_file, target_file)
