# agent-debugger
agent de debugging automatique

## Étape 1 — Schéma d'architecture

Le schéma suivant illustre le fonctionnement général de l'agent de débogage automatique :

<img width="293" height="344" alt="Diagramme sans nom drawio" src="https://github.com/user-attachments/assets/5d103bf5-70a2-46a3-a7aa-0747326470ef" />


### Description des composants :
- **Interface de configuration** : Permet aux utilisateurs de configurer les paramètres du processus de débogage, tels que les chemins des scripts, les paramètres d'environnement virtuel et les configurations du modèle IA.
- **Exécuter le script cible** : Exécute le script Python spécifié dans un environnement virtuel pour isoler l'exécution.
- **Capturer les erreurs d'exécution** : Surveille l'exécution du script et récupère les erreurs d'exécution ou les exceptions.
- **Envoyer au modèle IA** : Transmet le code original ainsi que les détails de l'erreur capturée à un modèle IA pour analyse.
- **Recevoir les corrections JSON** : Obtient les propositions de corrections de l'IA sous forme de JSON structuré.
- **Appliquer les corrections** : Fournit des options pour afficher les corrections suggérées ou les appliquer automatiquement au code.

## Étape 2 — Comprendre les environnements virtuels

Un environnement virtuel Python est un environnement isolé qui permet d'installer des dépendances spécifiques à un projet sans affecter l'installation globale de Python. Cela évite les conflits de versions entre bibliothèques et assure que chaque projet peut avoir ses propres exigences en matière de packages.

### Pourquoi un script a besoin de ses propres dépendances
Chaque script Python peut nécessiter des versions spécifiques de bibliothèques. Sans environnement virtuel, l'installation de dépendances pour un projet pourrait casser un autre projet utilisant des versions différentes. L'environnement virtuel isole ces dépendances, permettant une exécution cohérente et reproductible.

### Arborescence de l'environnement virtuel
L'environnement virtuel du projet est situé dans le répertoire `data_env/`. Voici sa structure principale :

```
data_env/
├── etc/
│   └── jupyter/
│       └── nbconfig/
│           └── notebook.d/
├── Include/
├── Scripts/
└── share/
    └── jupyter/
        └── nbextensions/
            └── pydeck/
```

### Emplacement du binaire Python
L'interpréteur Python de l'environnement virtuel se trouve à : `data_env/Scripts/python.exe` (sur Windows).

## Étape 3 — Exécuter un script et récupérer l’erreur

Pour exécuter un programme Python depuis un autre programme, on utilise le module `subprocess` de Python. Ce module permet de lancer des processus externes et de contrôler leur exécution.

### Capturer la sortie et les erreurs
- **stdout** : La sortie standard est capturée en utilisant le paramètre `capture_output=True` dans `subprocess.run()`.
- **stderr** : Les erreurs standard sont également capturées avec le même paramètre. L'objet `CompletedProcess` retourné contient les attributs `.stdout` et `.stderr` pour accéder à ces données.
- Le paramètre `text=True` permet de traiter les sorties comme des chaînes de caractères au lieu d'octets.

### Pourquoi ce mécanisme est essentiel
Ce mécanisme permet à l'agent de débogage d'exécuter des scripts inconnus en toute sécurité, de détecter les erreurs sans que celles-ci interrompent le fonctionnement de l'agent lui-même, et de transmettre les informations d'erreur à un modèle d'IA pour obtenir des propositions de correction.

### Mini-exemple
Le script `script_launcher.py` démontre ce mécanisme : il lance `scripts/script_a.py` et affiche uniquement les erreurs détectées via `stderr`.

Exemple de code dans `script_launcher.py` :
```python
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
```

(Note : Pour utiliser l'environnement virtuel, remplacer `"python"` par le chemin vers `data_env/Scripts/python.exe`.)

## Étape 4 — Construire une prompt robuste pour un modèle d’IA

Pour transformer un modèle de langage (LLM) en agent spécialisé dans la correction de code, il est essentiel de structurer les interactions de manière précise en utilisant différents types de messages.

### Différence entre les types de messages
- **Message système (system)** : Définit le rôle, les règles et le comportement général de l'IA. Il est envoyé une fois au début pour configurer l'agent. Exemple : Le fichier `agent/context.txt` définit PYFIXER comme un agent spécialisé avec des règles strictes.
- **Message utilisateur (user)** : Contient les données spécifiques à traiter, comme le code et l'erreur. Exemple : Le fichier `agent/prompt.txt` fournit le code et l'erreur au format structuré.
- **Message assistant (assistant)** : La réponse générée par l'IA, qui doit respecter le format imposé (ici, un JSON strict).

### Pourquoi imposer des règles strictes
Les règles strictes garantissent que la réponse de l'IA est prévisible, parseable automatiquement et limitée aux modifications nécessaires. Cela évite les réponses verbeuses, les inventions inutiles et les erreurs de format qui pourraient casser le programme appelant.

### Format JSON imposé
Le format JSON obligatoire structure la réponse pour inclure uniquement les champs nécessaires : `diagnostic` (explication de l'erreur), `patch` (code corrigé), et `confidence` (niveau de confiance). Cela permet une exploitation automatique sans analyse de texte libre.

### Empêcher le modèle d’inventer trop de modifications
Les règles spécifient de modifier uniquement les lignes nécessaires, de ne pas réécrire tout le fichier, et de ne rien inventer (pas de nouvelles fonctions sauf si indispensable). Cela assure des correctifs minimaux et sûrs.

### Exemple de prompt pour l'agent PYFIXER
**Message système** (dans `agent/context.txt`) :
```
Tu es PYFIXER, un agent spécialisé dans l’analyse et la correction de code Python.
...
```

**Message utilisateur** (dans `agent/prompt.txt`) :
```
Voici le code du script Python et l'erreur qu'il génère.

Code :
{code}

Erreur :
{error}

Propose une correction au format JSON.
```

**Réponse attendue** : Un JSON strict comme :
```json
{
  "diagnostic": "Division par zéro dans la fonction division.",
  "patch": "def division(a, b):\n    if b == 0:\n        raise ValueError('Division par zéro')\n    return a / b\n\nresult = division(5, 0)\nprint(\"Résultat =\", result)",
  "confidence": 0.95
}
```
## Étape 5 — Lire, comprendre et valider un JSON de corrections

Pour traiter la réponse JSON fournie par le modèle d'IA, le programme doit suivre des étapes précises de validation et de gestion des erreurs. Voici les étapes nécessaires pour valider un JSON de correction provenant de l'IA :

1. **Lire le JSON** : Récupérer la chaîne de caractères représentant le JSON depuis la réponse de l'IA.

2. **Vérifier la validité syntaxique** : S'assurer que la chaîne est un JSON bien formé, sans erreurs de syntaxe qui empêcheraient le parsing.

3. **Vérifier la présence des champs obligatoires** : Contrôler que le JSON contient exactement les champs attendus : `diagnostic`, `patch` et `confidence`. Aucun champ supplémentaire n'est autorisé pour maintenir la rigueur.

4. **Valider les types et valeurs des champs** :
   - `diagnostic` doit être une chaîne de caractères décrivant l'erreur de manière claire et concise.
   - `patch` doit être une chaîne de caractères contenant la version corrigée du code Python.
   - `confidence` doit être un nombre flottant compris entre 0.0 et 1.0, indiquant le niveau de confiance de l'IA dans la correction.

5. **Gérer les cas particuliers** :
   - Si le JSON est invalide ou incomplet, rejeter la réponse et signaler une erreur à l'utilisateur.
   - Si le champ `confidence` est très bas (par exemple, inférieur à 0.5), considérer la correction comme peu fiable et demander une confirmation manuelle.
   - Si l'IA indique dans le `diagnostic` que le bug n'est pas dans le code (par exemple, problème d'environnement ou de dépendances), informer l'utilisateur que la correction automatique n'est pas applicable.

6. **Extraire et utiliser les données** : Une fois validé, extraire le `diagnostic` pour l'affichage, le `patch` pour l'application potentielle au code, et utiliser `confidence` pour décider du niveau d'automatisation (application automatique si confiance élevée, affichage seulement sinon).

Ces étapes assurent que seules les corrections fiables et correctement formatées sont traitées, évitant les applications erronées de patches invalides.

## Étape 6 — Modifier un fichier source à partir d’instructions

Un système de patch permet de modifier un fichier source de manière contrôlée en appliquant des corrections uniquement aux parties erronées, sans remplacer l'ensemble du fichier. Cela préserve le code existant et applique des changements minimaux. Voici le principe d'un système de patch en étapes claires :

1. **Créer une sauvegarde** : Avant toute modification, créer une copie de sauvegarde du fichier original pour permettre une restauration en cas d'erreur.

2. **Lire le fichier ligne par ligne** : Charger le contenu du fichier cible en mémoire, en le divisant en lignes pour une manipulation précise.

3. **Recevoir les instructions de modification** : Obtenir le code corrigé complet depuis la réponse de l'IA, puis identifier les différences avec le code original.

4. **Appliquer les modifications ciblées** :
   - **Comparer ligne par ligne** : Pour chaque ligne, vérifier si elle diffère entre l'original et la version corrigée.
   - **Supprimer les lignes exactes** : Retirer uniquement les lignes identifiées comme erronées.
   - **Insérer les nouvelles lignes** : Ajouter les corrections au bon endroit, en préservant l'ordre et la structure du reste du fichier.

5. **Vérifier l'intégrité** : S'assurer que le fichier modifié reste syntaxiquement correct et que le script peut toujours être exécuté sans erreurs introduites.

6. **Sauvegarder le résultat** : Écrire les modifications dans le fichier cible, en appliquant uniquement les changements nécessaires sans altérer les parties non concernées.

Ce système garantit que seules les parties avec des erreurs sont corrigées, évitant les modifications inutiles et préservant la stabilité du code. L'implémentation compare la version corrigée avec l'original pour appliquer des patches minimaux.

## Étape 7 — Créer une petite interface utilisateur

Une interface utilisateur permet à l'utilisateur d'interagir avec l'agent de débogage sans manipuler directement les fichiers ou la ligne de commande. Elle utilise Streamlit pour créer une application web simple.

### Comment une interface peut modifier un fichier de configuration
L'interface peut inclure des champs de saisie (text_input) pour permettre à l'utilisateur d'entrer ou de modifier des chemins, tels que le chemin du projet ou l'emplacement de l'environnement virtuel. Lorsque l'utilisateur soumet les modifications (via un bouton), l'interface écrit ces valeurs dans le fichier `config.json` en utilisant `json.dump()`. Cela met à jour la configuration de manière persistante.

### Comment ce fichier est relu par le programme
À chaque lancement de l'interface ou lors d'une action nécessitant la configuration, le programme relit le fichier `config.json` en utilisant `json.load()`. Cela permet de charger dynamiquement les paramètres mis à jour sans redémarrer l'application, assurant que les modifications sont prises en compte immédiatement.

### Conception d'une interface simple
Voici une description de l'interface proposée, utilisant Streamlit :

- **Titre** : "Agent Debugger - Analyse de script Python"

- **Section Configuration** :
  - Champ texte pour saisir/modifier le chemin du projet (`project_path`).
  - Champ texte pour saisir/modifier le chemin de l'interpréteur Python virtuel (`venv_path`).
  - Bouton "Sauvegarder Configuration" pour écrire dans `config.json`.

- **Section Analyse** :
  - Liste déroulante (selectbox) pour choisir un script à analyser depuis le dossier `scripts/`.
  - Bouton "Analyser et Corriger" pour lancer le processus d'analyse.

- **Section Résultats** :
  - Affichage de l'erreur détectée (stderr) dans une boîte de code.
  - Affichage des corrections proposées (contenu du JSON `last_patch.json`) dans une boîte de code.
  - Option pour appliquer la correction automatiquement (bouton supplémentaire, si confiance élevée).
<img width="4293" height="818" alt="Untitled diagram-2025-11-19-091246" src="https://github.com/user-attachments/assets/f8bf0e48-7cd3-4078-a7f5-8a854e39772b" />

Cette interface rend l'outil accessible et intuitif, permettant une configuration facile et un suivi visuel des erreurs et corrections.

## Étape 8 — Construire votre propre agent de debugging

Maintenant que vous connaissez toutes les briques, vous commencerez votre outil.
Vous devrez organiser votre projet en modules :

Faites un plan de votre projet :
nom des modules, rôle de chacun, données échangées.

### Modules et rôles
- **config.py** : Gère la configuration de l'agent. Lit et écrit le fichier `config.json` pour stocker les chemins du projet et de l'environnement virtuel. Rôle : Centraliser la gestion des paramètres persistants.
- **executor.py** : Responsable de l'exécution des scripts dans l'environnement virtuel. Utilise `subprocess` pour lancer le script et capturer stdout/stderr. Rôle : Exécuter les scripts en toute sécurité et récupérer les erreurs.
- **ai_analyzer.py** : Gère l'interaction avec le modèle d'IA. Envoie le code et l'erreur à l'IA, reçoit la réponse JSON. Rôle : Analyser les erreurs via l'IA et obtenir des propositions de correction.
- **patcher.py** : Applique les corrections au code source. Compare le code original avec la version corrigée et modifie uniquement les parties erronées. Rôle : Modifier les fichiers de manière contrôlée et sûre.
- **ui.py** : Interface utilisateur avec Streamlit. Permet de configurer, sélectionner des scripts, afficher les erreurs et corrections. Rôle : Fournir une interface intuitive pour l'utilisateur final.

### Données échangées
- **config.py** : Échange des dictionnaires JSON (chemins) avec ui.py et les autres modules pour la configuration.
- **executor.py** : Reçoit le chemin du script (string) et le chemin de l'interpréteur (string) ; retourne stdout (string), stderr (string).
- **ai_analyzer.py** : Reçoit le code (string) et l'erreur (string) ; retourne un JSON (dict) avec diagnostic, patch, confidence.
- **patcher.py** : Reçoit le chemin du fichier (string) et le patch (string) ; applique les modifications sans retour direct (confirmation via exceptions).
- **ui.py** : Coordonne les appels aux autres modules, affiche les résultats (strings, JSON) et gère les interactions utilisateur.

```
agent-debugger/
│
├── agent/
│   ├── agent.py
│   ├── apply_patch.py
│   ├── context.txt
│   ├── prompt.txt
│   ├── config.json
│   ├── last_patch.json
│
├── scripts/
│   ├── script_a.py
│   │
│   └── backups/
│       └── script_a.py.bak
│
├── data_env/                 (ton venv Python)
│   ├── Scripts/
│   │   ├── python.exe
│   │   └── ... (pip, activate, etc.)
│   └── Lib/
│       └── site-packages/    (packages installés)
│
├── .env                      (GROQ_API_KEY)
├── requirements.txt          (optionnel)
│
└── README.md                 (optionnel)
```

## Étape 9 — Comprendre les limites et risques

Un débuggeur automatisé pose des problèmes techniques et de sécurité. Voici 5 risques identifiés avec une solution pour chacun :

1. **Erreur du modèle IA** : L'IA peut proposer des corrections incorrectes ou inappropriées, conduisant à des bugs supplémentaires.
   - **Solution** : Implémenter une validation manuelle pour les corrections avec une confiance faible (< 0.7), et ajouter des tests automatiques pour vérifier la correction avant application.

2. **Mauvaise interprétation du code** : L'IA peut mal comprendre le contexte du code, les variables ou la logique, menant à des modifications inadéquates.
   - **Solution** : Enrichir le prompt avec plus de contexte (commentaires, structure du projet), et limiter les modifications aux lignes directement liées à l'erreur.

3. **Application automatique dangereuse** : L'application automatique de corrections peut casser le code existant ou introduire des vulnérabilités.
   - **Solution** : Toujours créer des sauvegardes avant modification, et exiger une confirmation utilisateur pour l'application automatique, en affichant un aperçu des changements.

4. **Dépendances manquantes** : Le script peut nécessiter des packages non installés dans l'environnement virtuel, causant des erreurs d'importation.
   - **Solution** : Analyser les imports du script et vérifier/installer les dépendances manquantes dans le venv avant exécution, en utilisant pip.

5. **Chemins invalides** : Les chemins configurés (projet, venv) peuvent être incorrects ou inexistants, empêchant l'exécution.
   - **Solution** : Valider l'existence et l'accessibilité des chemins au démarrage, afficher des messages d'erreur clairs, et permettre la reconfiguration via l'interface.

