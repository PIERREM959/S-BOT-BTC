import yfinance as yf
import time
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from colorama import Fore, init
import pandas as pd
import matplotlib.pyplot as plt

init(autoreset=True)

# ===== Paramètres ajustables =====
investment_amount = 0.01  # BTC par achat
trailing_stop_percentage = 0.4  # en %
sleep_time = 900  # 15 minutes
usd_balance = 100000.0
btc_balance = 0.0
highest_price = None
trailing_stop_price = None
csv_file = "sbot_performance.csv"

# Variables pour tendance
previous_mm50 = None

# ===== Variables d'environnement (Render) =====
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# ===== Envoi email =====
def send_email(subject, body, attachment=None):
    if EMAIL_ADDRESS and EMAIL_PASSWORD and TO_EMAIL:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = TO_EMAIL
            msg.set_content(body)

            if attachment and os.path.exists(attachment):
                with open(attachment, "rb") as f:
                    msg.add_attachment(f.read(), maintype="image", subtype="png", filename="rapport.png")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

            print(Fore.GREEN + "✅ Email envoyé avec succès.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur email : {e}")
    else:
        print(Fore.YELLOW + "⚠️ EMAIL non configuré, email ignoré.")

# ===== Initialiser CSV =====
if not os.path.exists(csv_file):
    with open(csv_file, "w") as f:
        f.write("Date & Heure,Action,Prix BTC,Quantité BTC,Solde USD,Solde BTC,Valeur Totale USD\n")

def save_transaction(action, price):
    total_value = usd_balance + btc_balance * price
    with open(csv_file, "a") as f:
        f.write(f"{datetime.now()},{action},{price},{investment_amount if action=='Achat' else 0},{usd_balance},{btc_balance},{total_value}\n")

# ===== Analyse quotidienne =====
def generate_daily_report():
    if not os.path.exists(csv_file):
        return

    df = pd.read_csv(csv_file)
    if df.empty:
        return

    initial_value = df["Valeur Totale USD"].iloc[0]
    final_value = df["Valeur Totale USD"].iloc[-1]
    profit = final_value - initial_value
    profit_pct = (profit / initial_value) * 100

    nb_achats = df[df["Action"] == "Achat"].shape[0]
    nb_ventes = df[df["Action"] == "Vente"].shape[0]

    # Graphique
    plt.figure(figsize=(8, 5))
    plt.plot(df["Date & Heure"], df["Valeur Totale USD"], color="blue", marker="o")
    plt.title("Évolution du Portefeuille")
    plt.xticks(rotation=45)
    plt.tight_layout()
    chart_path = "rapport.png"
    plt.savefig(chart_path)
    plt.close()

    report_text = (
        f"Rapport quotidien S-BOT-BTC\n\n"
        f"Valeur initiale : {initial_value:.2f} USD\n"
        f"Valeur finale   : {final_value:.2f} USD\n"
        f"Profit/Perte    : {profit:.2f} USD ({profit_pct:.2f}%)\n"
        f"Achats : {nb_achats}, Ventes : {nb_ventes}\n"
    )

    send_email("Rapport quotidien S-BOT-BTC", report_text, chart_path)

# ===== Récup prix BTC + MM50 =====
def get_price_and_mm50():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="15d", interval="15m")
    if data.empty or len(data) < 50:
        print(Fore.YELLOW + "⚠️ Pas assez de données pour MM50, retry...")
        time.sleep(10)
        return get_price_and_mm50()

    close_prices = data["Close"].iloc[-50:]
    price = close_prices.iloc[-1]
    mm50 = close_prices.mean()
    return price, mm50

# ===== Achat BTC =====
def buy_btc(price):
    global usd_balance, btc_balance
    cost = investment_amount * price
    if usd_balance >= cost:
        usd_balance -= cost
        btc_balance += investment_amount
        save_transaction("Achat", price)
        print(Fore.GREEN + f"🟢 Achat : {investment_amount} BTC à {price:.2f} USD")
    else:
        print(Fore.RED + "⏸ Achat suspendu : Solde USD insuffisant.")

# ===== Vente BTC =====
def sell_all_btc(price):
    global usd_balance, btc_balance, highest_price, trailing_stop_price
    if btc_balance > 0:
        usd_balance += btc_balance * price
        save_transaction("Vente", price)
        print(Fore.RED + f"🔴 Vente : {btc_balance:.6f} BTC à {price:.2f} USD")
        send_email(
            "Vente exécutée - S Bot BTC",
            f"Vente à {price:.2f} USD\nSolde USD: {usd_balance:.2f}\nSolde BTC: 0.0"
        )
        btc_balance = 0.0
        highest_price = None
        trailing_stop_price = None

# ===== Variables pour email et rapport =====
last_email_time = time.time()
last_report_time = time.time()

# ===== Logs init =====
print(Fore.CYAN + "🚀 S-BOT-BTC avec Détection Tendance + Contrôle Budget + Rapport Auto")
print(Fore.CYAN + f"💰 Solde initial USD : {usd_balance}, Achat toutes les {sleep_time}s")
print(Fore.CYAN + f"Trailing Stop : {trailing_stop_percentage}% | MM50 active")
print(Fore.CYAN + "=========================================\n")

# ===== Boucle principale =====
while True:
    global previous_mm50
    price, mm50 = get_price_and_mm50()

    # Détection de tendance
    tendance = "Inconnue"
    if previous_mm50 is not None:
        if mm50 > previous_mm50:
            tendance = "Haussière"
        else:
            tendance = "Baissière"
    previous_mm50 = mm50

    print(Fore.CYAN + f"\n📈 Prix BTC : {price:.2f} USD | MM50 : {mm50:.2f} USD | Tendance : {tendance}")

    # Achat uniquement si tendance haussière
    if tendance == "Haussière":
        print(Fore.GREEN + "✅ Tendance haussière : Achat autorisé.")
        if usd_balance >= investment_amount * price:
            buy_btc(price)
        else:
            print(Fore.RED + "⏸ Achat suspendu : Solde USD insuffisant.")
    else:
        print(Fore.YELLOW + "⏸ Tendance baissière : Pas d'achat (standby).")

    # Mise à jour trailing stop
    if highest_price is None or price > highest_price:
        highest_price = price
        trailing_stop_price = highest_price * (1 - trailing_stop_percentage / 100)
        print(Fore.BLUE + f"🛡️ Nouveau trailing stop : {trailing_stop_price:.2f} USD")

    # Vente si prix <= trailing stop
    if btc_balance > 0 and price <= trailing_stop_price:
        sell_all_btc(price)

    # Logs
    print(Fore.YELLOW + f"💰 Solde USD: {usd_balance:.2f} | BTC: {btc_balance:.6f}")
    print(Fore.MAGENTA + f"📊 Plus haut prix: {highest_price:.2f} | Stop: {trailing_stop_price:.2f}")

    # Email toutes les heures
    if time.time() - last_email_time >= 3600:
        send_email(
            "Rapport horaire - S Bot BTC",
            f"[{datetime.now()}]\nSolde USD: {usd_balance:.2f}\nSolde BTC: {btc_balance:.6f}\nPrix actuel: {price:.2f}\nMM50: {mm50:.2f}\nTendance: {tendance}"
        )
        last_email_time = time.time()

    # Rapport quotidien toutes les 24h
    if time.time() - last_report_time >= 86400:  # 24 heures
        generate_daily_report()
        last_report_time = time.time()

    time.sleep(sleep_time)
