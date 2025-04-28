#approximation courbe modèle strava
# https://medium.com/strava-engineering/an-improved-gap-model-8b07ae8886c3

import numpy as np
import matplotlib.pyplot as plt

# 1. Points extraits à la main du graphique (pente en %)
pente = np.array([-32, -28, -24, -20.5, -17.5, -15, -12.5, -10, -8.7, -7, -3, 0, 2, 3.8, 5.7, 7, 8.3, 10, 12, 14.5, 17.5, 20, 24, 28, 32])
ajustement = np.array([1.6, 1.4, 1.2, 1.1, 1, 0.93, 0.9, 0.87, 0.87, 0.89, 0.94, 1, 1.07, 1.12, 1.21, 1.29, 1.38, 1.5, 1.6, 1.8, 2.05, 2.3, 2.6, 2.95, 3.35])

# 2. Normaliser la pente entre -0.32 et +0.32
pente_normalisee = pente / 100

# 3. Fit d'un polynôme de degré 3 sur pente_normalisee
coeffs = np.polyfit(pente_normalisee, ajustement, deg=3)

# 4. Créer la fonction approchante
pente_lisse = np.linspace(-0.32, 0.32, 300)
ajustement_fit = np.polyval(coeffs, pente_lisse)

# 5. Plot
plt.figure(figsize=(8,5))
plt.plot(pente_normalisee, ajustement, 'o', label="Données extraites (Strava)")
plt.plot(pente_lisse, ajustement_fit, '-', label="Fit polynôme degré 3")
plt.xlabel('Pente (fraction)')
plt.ylabel('Facteur d\'ajustement allure')
plt.legend()
plt.grid(True)
plt.show()

# 6. Affiche les nouveaux coefficients
print("Nouveaux coefficients du polynôme (degré 3) :", coeffs)

