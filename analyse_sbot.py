import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ===== Charger le CSV =====
csv_file = "sbot_performance.csv"
df = pd.read_csv(csv_file)

# Convertir la colonne Date & Heure en datetime
df["Date & Heure"] = pd.to_datetime(df["Date & Heure"], format="%Y-%m-%d %H:%M:%S")

# Convertir les colonnes numériques
df["Prix BTC"] = df["Prix BTC"].astype(float)
df["Quantité BTC"] = df["Quantité BTC"].astype(float)
df["Solde USD"] = df["Solde USD"].astype(float)
df["Solde BTC"] = df["Solde BTC"].astype(float)
df["Valeur Totale USD"] = df["Valeur Totale USD"].astype(float)

# ===== Stats générales =====
initial_value = df["Valeur Totale USD"].iloc[0]
final_value = df["Valeur Totale USD"].iloc[-1]
profit = final_value - initial_value
profit_pct = (profit / initial_value) * 100

nb_achats = df[df["Action"] == "Achat"].shape[0]
nb_ventes = df[df["Action"] == "Vente"].shape[0]

print("\n===== Résultats =====")
print(f"Valeur initiale : {initial_value:.2f} USD")
print(f"Valeur finale   : {final_value:.2f} USD")
print(f"Profit / Perte  : {profit:.2f} USD ({profit_pct:.2f}%)")
print(f"Nombre d'achats : {nb_achats}")
print(f"Nombre de ventes: {nb_ventes}")

# ===== Meilleure et pire vente =====
if not df.empty and nb_ventes > 0:
    meilleur_trade = df[df["Action"] == "Vente"].sort_values("Prix BTC", ascending=False).head(1)
    pire_trade = df[df["Action"] == "Vente"].sort_values("Prix BTC", ascending=True).head(1)

    print("\n===== Meilleure Vente =====")
    print(meilleur_trade[["Date & Heure", "Prix BTC", "Quantité BTC"]])

    print("\n===== Pire Vente =====")
    print(pire_trade[["Date & Heure", "Prix BTC", "Quantité BTC"]])

# ===== Graphique évolution valeur totale =====
plt.figure(figsize=(10, 6))
plt.plot(df["Date & Heure"], df["Valeur Totale USD"], marker="o", color="blue")
plt.title("Évolution de la valeur totale (USD)")
plt.xlabel("Date")
plt.ylabel("Valeur Totale USD")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
