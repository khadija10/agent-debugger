def load_file(path):
    # path devrait être un string → générera une erreur
    with open(path) as f:
        content = f.read()

    # Erreur volontaire : variable pas définie
    return contenu
