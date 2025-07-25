import yfinance as yf
import time
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)  # Reset couleurs après chaque print

# ===== Paramètres ajustables =====
investment_amount = 0.01  # BTC par achat
trailing_stop_percentage = 0.4  # en % (0,4%)
sleep_time = 900  # 15 minutes
usd_balance = 100000.0  # Capital initial
btc_balance = 0.0
highest_price = None
trailing_stop_price = None

# ===== Suivi tendance =====
previous_mm50 = None  # Pour détecter la tendance

# ===== Variables d'environnement (Render) =====
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")


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

            print(Fore.GREEN + "✅ Email envoyé avec succès.")
        except Exception as e:
            print(Fore.RED + f"❌ Erreur email : {e}")
    else:
        print(Fore.YELLOW + "⚠️ EMAIL non configuré, email ignoré.")


# ===== Récup prix BTC + MM50 =====
def get_price_and_mm50():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="7d", interval="15m")
    if data.empty or len(data) < 50:
        print(Fore.YELLOW + "⚠️ Pas assez de données pour MM50, retry...")
        time.sleep(10)
        return get_price_and_mm50()

    close_prices = data["Close"].iloc[-50:]
    price = close_prices.iloc[-1]
    mm50 = close_prices.mean()
    return price, mm50


# ===== Détection tendance avec couleur =====
def check_trend(current_mm50):
    global previous_mm50
    trend = "Neutre"
    color = Fore.YELLOW
    if previous_mm50 is not None:
        if current_mm50 > previous_mm50:
            trend = "Hausse"
            color = Fore.GREEN
        elif current_mm50 < previous_mm50:
            trend = "Baisse"
            color = Fore.RED
    previous_mm50 = current_mm50
    return trend, color


# ===== Achat BTC =====
def buy_btc(price):
    global usd_balance, btc_balance
    cost = investment_amount * price
    if usd_balance >= cost:
        usd_balance -= cost
        btc_balance += investment_amount
        print(Fore.GREEN + f"🟢 Achat : {investment_amount} BTC à {price:.2f} USD")
    else:
        print(Fore.RED + "⏸ Achat suspendu : Solde USD insuffisant.")


# ===== Vente BTC =====
def sell_all_btc(price):
    global usd_balance, btc_balance, highest_price, trailing_stop_price
    if btc_balance > 0:
        usd_balance += btc_balance * price
        print(Fore.RED + f"🔴 Vente : {btc_balance:.6f} BTC à {price:.2f} USD")
        send_email(
            "Vente exécutée - S Bot BTC",
            f"Vente à {price:.2f} USD\nSolde USD: {usd_balance:.2f}\nSolde BTC: 0.0"
        )
        btc_balance = 0.0
        highest_price = None
        trailing_stop_price = None


# ===== Variables email horaire =====
last_email_time = time.time()

# ===== Logs init =====
print(Fore.CYAN + "🚀 S-BOT-BTC avec MM50 + Détection Tendance démarré")
print(Fore.CYAN + f"💰 Solde initial USD : {usd_balance}, Achat toutes les {sleep_time}s")
print(Fore.CYAN + f"Trailing Stop : {trailing_stop_percentage}% | MM50 active + Filtrage tendance")
print(Fore.CYAN + "=========================================\n")

# ===== Boucle principale =====
while True:
    price, mm50 = get_price_and_mm50()
    trend, color = check_trend(mm50)

    print(Fore.CYAN + f"\n📈 Prix actuel BTC : {price:.2f} USD | MM50 : {mm50:.2f} USD | Tendance : {color}{trend}")

    # Achat uniquement si Prix > MM50 ET tendance haussière
    if price > mm50 and trend == "Hausse":
        print(Fore.GREEN + "✅ Condition remplie : Achat autorisé.")
        if usd_balance >= investment_amount * price:
            buy_btc(price)
        else:
            print(Fore.RED + "⏸ Achat suspendu : Solde USD insuffisant.")
    else:
        print(Fore.YELLOW + "⏸ Condition non remplie : Pas d'achat (standby).")

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
            f"[{datetime.now()}]\nSolde USD: {usd_balance:.2f}\nSolde BTC: {btc_balance:.6f}\nPrix actuel: {price:.2f}\nMM50: {mm50:.2f}\nTendance: {trend}"
        )
        last_email_time = time.time()

    time.sleep(sleep_time)
