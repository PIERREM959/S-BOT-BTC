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
trailing_stop_percentage = 0.5  # en % (0,5%)
sleep_time = 300  # 5 minutes
usd_balance = 100000.0  # Capital initial
btc_balance = 0.0
highest_price = None
trailing_stop_price = None

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

# ===== Récup prix BTC + MM30 =====
def get_price_and_mm30():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="1d", interval="5m")
    if data.empty or len(data) < 30:
        print(Fore.YELLOW + "⚠️ Pas assez de données pour MM30, retry...")
        time.sleep(10)
        return get_price_and_mm30()

    close_prices = data["Close"].iloc[-30:]
    price = close_prices.iloc[-1]
    mm30 = close_prices.mean()
    return price, mm30

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
print(Fore.CYAN + "🚀 S-BOT-BTC avec MM30 + Contrôle Budget démarré")
print(Fore.CYAN + f"💰 Solde initial USD : {usd_balance}, Achat toutes les {sleep_time}s")
print(Fore.CYAN + f"Trailing Stop : {trailing_stop_percentage}% | MM30 active")
print(Fore.CYAN + "=========================================\n")

# ===== Boucle principale =====
while True:
    price, mm30 = get_price_and_mm30()
    print(Fore.CYAN + f"\n📈 Prix actuel BTC : {price:.2f} USD | MM30 : {mm30:.2f} USD")

    # Achat uniquement si Prix > MM30
    if price > mm30:
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
            f"[{datetime.now()}]\nSolde USD: {usd_balance:.2f}\nSolde BTC: {btc_balance:.6f}\nPrix actuel: {price:.2f}\nMM30: {mm30:.2f}"
        )
        last_email_time = time.time()

    time.sleep(sleep_time)
