import yfinance as yf
import time
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
import csv
from colorama import Fore, init

init(autoreset=True)

# ===== Paramètres ajustables =====
investment_amount = 0.01  # BTC par achat
trailing_stop_percentage = 0.4  # en % (0,4%)
sleep_time = 900  # 15 minutes
usd_balance = 100000.0  # Capital initial
btc_balance = 0.0
highest_price = None
trailing_stop_price = None
csv_file = "sbot_performance.csv"

# ===== Variables d'environnement (Render) =====
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# ===== Fonction pour logs avec timestamp =====
def log(msg, color=Fore.WHITE):
    print(color + f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ===== Envoi email =====
def send_email(subject, body):
    if EMAIL_ADDRESS and EMAIL_PASSWORD and TO_EMAIL:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = TO_EMAIL
            msg.set_content(body)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

            log("✅ Email envoyé avec succès.", Fore.GREEN)
        except Exception as e:
            log(f"❌ Erreur email : {e}", Fore.RED)
    else:
        log("⚠️ EMAIL non configuré, email ignoré.", Fore.YELLOW)

# ===== Création du fichier CSV si inexistant =====
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date & Heure", "Action", "Prix BTC", "Quantité BTC", "Solde USD", "Solde BTC", "Valeur Totale USD", "Commentaire"])

# ===== Récup prix BTC + MM50 =====
def get_price_and_mm50():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="14d", interval="15m")
    if data.empty or len(data) < 50:
        log("⚠️ Pas assez de données pour MM50, retry...", Fore.YELLOW)
        time.sleep(10)
        return get_price_and_mm50()

    close_prices = data["Close"].iloc[-50:]
    price = close_prices.iloc[-1]
    mm50 = close_prices.mean()
    return price, mm50

# ===== Écriture CSV =====
def write_to_csv(action, price, qty, comment):
    total_value = usd_balance + (btc_balance * price)
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action,
            f"{price:.2f}",
            f"{qty:.6f}",
            f"{usd_balance:.2f}",
            f"{btc_balance:.6f}",
            f"{total_value:.2f}",
            comment
        ])

# ===== Achat BTC =====
def buy_btc(price):
    global usd_balance, btc_balance
    cost = investment_amount * price
    if usd_balance >= cost:
        usd_balance -= cost
        btc_balance += investment_amount
        log(f"🟢 Achat : {investment_amount} BTC à {price:.2f} USD", Fore.GREEN)
        write_to_csv("Achat", price, investment_amount, "Condition MM50 remplie")
    else:
        log("⏸ Achat suspendu : Solde USD insuffisant.", Fore.RED)

# ===== Vente BTC =====
def sell_all_btc(price):
    global usd_balance, btc_balance, highest_price, trailing_stop_price
    if btc_balance > 0:
        usd_balance += btc_balance * price
        log(f"🔴 Vente : {btc_balance:.6f} BTC à {price:.2f} USD", Fore.RED)
        write_to_csv("Vente", price, btc_balance, "Trailing Stop atteint")
        send_email(
            "Vente exécutée - S Bot BTC",
            f"Vente à {price:.2f} USD\nSolde USD: {usd_balance:.2f}\nSolde BTC: 0.0"
        )
        btc_balance = 0.0
        highest_price = None
        trailing_stop_price = None

# ===== Logs init =====
log("🚀 S-BOT-BTC avec MM50 + Contrôle Budget + Suivi CSV démarré", Fore.CYAN)
log(f"💰 Solde initial USD : {usd_balance}, Achat toutes les {sleep_time}s", Fore.CYAN)
log(f"Trailing Stop : {trailing_stop_percentage}% | MM50 active", Fore.CYAN)
log("=========================================", Fore.CYAN)

# ===== Variables email horaire =====
last_email_time = time.time()

# ===== Boucle principale =====
while True:
    price, mm50 = get_price_and_mm50()
    log(f"📈 Prix BTC : {price:.2f} USD | MM50 : {mm50:.2f} USD", Fore.CYAN)

    # Affichage tendance
    if price > mm50:
        log("📊 Tendance : Haussière (Prix > MM50)", Fore.GREEN)
    else:
        log("📊 Tendance : Baissière (Prix < MM50)", Fore.RED)

    # Achat si condition remplie
    if price > mm50:
        if usd_balance >= investment_amount * price:
            buy_btc(price)
        else:
            log("⏸ Achat suspendu : Solde USD insuffisant.", Fore.RED)
    else:
        log("⏸ Pas d'achat (Prix < MM50)", Fore.YELLOW)

    # Mise à jour trailing stop
    if highest_price is None or price > highest_price:
        highest_price = price
        trailing_stop_price = highest_price * (1 - trailing_stop_percentage / 100)
        log(f"🛡️ Nouveau trailing stop : {trailing_stop_price:.2f} USD", Fore.BLUE)

    # Vente si prix <= trailing stop
    if btc_balance > 0 and price <= trailing_stop_price:
        sell_all_btc(price)

    # Logs résumé
    log(f"💰 Solde USD: {usd_balance:.2f} | BTC: {btc_balance:.6f}", Fore.YELLOW)
    log(f"📊 Plus haut prix: {highest_price:.2f} | Stop: {trailing_stop_price:.2f}", Fore.MAGENTA)

    # Email toutes les heures
    if time.time() - last_email_time >= 3600:
        send_email(
            "Rapport horaire - S Bot BTC",
            f"[{datetime.now()}]\nSolde USD: {usd_balance:.2f}\nSolde BTC: {btc_balance:.6f}\nPrix actuel: {price:.2f}\nMM50: {mm50:.2f}"
        )
        last_email_time = time.time()

    time.sleep(sleep_time)
