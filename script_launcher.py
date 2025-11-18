import subprocess

script_to_run = "scripts/script_a.py"

try:
    completed = subprocess.run(
        ["python", script_to_run],
        capture_output=True,
        text=True
    )

    if completed.stderr:
        print("=== Erreur détectée ===")
        print(completed.stderr)

except Exception as e:
    print("Erreur lors de l'exécution :", e)
