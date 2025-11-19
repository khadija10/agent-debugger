#from test import compute
#print(compute(5))
# ============================
#   GROS SCRIPT AVEC 12 ERREURS
# ============================

from math import squarert   # ERREUR 1 : ImportError (mauvais nom : sqrt)

# ERREUR 2 : variable globale non définie
GLOBAL_LIMIT = max_value

def load_numbers():
    # ERREUR 3 : indentation cassée
numbers = [10, 5, 0, 25, "30", -5]
    return numbers


def compute_ratio(a, b):
    # ERREUR 4 : division par zéro possible
    return a / b


def clean_numbers(values):
    cleaned = []
    for v in values:
        # ERREUR 5 : transformation incorrecte
        cleaned.append(int(v) + "1")   # int + str => TypeError
    return cleaned


def summarize(values):
    total = 0
    count = len(valuez)   # ERREUR 6 : typo variable
    for v in values:
        total += v

    avg = total / counnt   # ERREUR 7 : variable inconnue
    return avg


def find_max(values):
    # ERREUR 8 : {} au lieu de []
    maximum = values{0}
    for v in values:
        if v > maximum:
            maximum = v
    return maximum


def print_results(values):
    ratio = compute_ratio(values[0], values[2])  # b = 0 => ZeroDivisionError

    # ERREUR 9 : mauvaise fonction
    result = format_value(ratio)

    print("Ratio:", result)
    print("Max:", find_max(values))
    print("Average:", summarize(values))

    # ERREUR 10 : boucle infinie involontaire
    i = 0
    while i < 10:
        print("Boucle:", i)
        # i jamais augmenté => boucle infinie


def main():
    nums = load_numbers()
    cleaned = clean_numbers(nums)
    print_results(cleaned)

    # ERREUR 11 : appel de fonction avec mauvais nombre d’arguments
    final = compute_ratio(10)

    # ERREUR 12 : code mort non défini
    print("Result final:", final_value)


if __name__ == "__main__":
    main()