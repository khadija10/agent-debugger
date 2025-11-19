def clean_text(txt):
    # Erreur volontaire : txt peut être None
    return txt.strip().lower()

def format_output(x):
    # Erreur volontaire : mauvaise f-string
    return f"Value is {value}"
