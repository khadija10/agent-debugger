import math_tools
import file_loader
from utils import helpers

def start():
print("=== Application Demo ===")

    # Erreur : variable non définie
    result1 = math_tools.divide(10, 0)

    # Erreur : mauvaise signature de fonction
    data = file_loader.load_file(12345)

    # Erreur : fonction inexistante
    cleaned = helpers.clean_txt(data)

    print("Résultats :", result1, cleaned)

if __name__ = "__main__":
    star()
