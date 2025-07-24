import yfinance as yf
import time
import smtplib
from email.message import EmailMessage
import os

# ===== Paramètres ajustables =====
investment_amount = 0.001  # BTC à acheter toutes les 5 min
trailing_stop_percentage = 0.05  # en %
sleep_time = 30  # 30 (en secondes)
usd_balance = 10000.0
btc_balance = 0.0
btc_buy_price = None
trailing_stop_price = None

# ===== Variables d'environnement =====
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# ===== Fonction pour envoyer un email =====
def send_email(subject, body):
    if EMAIL_ADDRESS and EMAIL_PASSWORD and TO_EMAIL:
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = TO_EMAIL
            msg.set_content(body)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

            print("✅ Email envoyé avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email : {e}")
    else:
        print("⚠️ Variables EMAIL non définies, email non envoyé.")

# ===== Fonction pour obtenir le prix BTC =====
def get_btc_price():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="1d", interval="1m")  # 1 minute sur 1 jour
    if data.empty:
        print("⚠️ Pas de données reçues, on réessaie dans 1 min...")
        time.sleep(60)
        return get_btc_price()  # On réessaie
    return data["Close"].iloc[-1]

# ===== Achat BTC =====
def buy_btc(price):
    global usd_balance, btc_balance
    cost = investment_amount * price
    if usd_balance >= cost:
        usd_balance -= cost
        btc_balance += investment_amount
        print(f"🟢 Achat : {investment_amount} BTC à {price:.2f} USD")
        return True
    else:
        print("❌ Solde insuffisant pour acheter.")
        return False

# ===== Vente BTC =====
def sell_all_btc(price):
    global usd_balance, btc_balance
    if btc_balance > 0:
        usd_balance += btc_balance * price
        print(f"🔴 Vente : {btc_balance:.6f} BTC à {price:.2f} USD")
        send_email(
            "Vente exécutée - S Bot BTC",
            f"Vente effectuée à {price:.2f} USD\n"
            f"Solde USD: {usd_balance:.2f}\nSolde BTC: 0.0"
        )
        btc_balance = 0.0

# ===== Boucle principale =====
while True:
    price = get_btc_price()
    print(f"📈 Prix actuel BTC : {price:.2f} USD")

    # Achat toutes les 5 minutes
    if buy_btc(price):
        if trailing_stop_price is None:
            trailing_stop_price = price * (1 - trailing_stop_percentage / 100)
        btc_buy_price = price

    # Mise à jour du trailing stop si le prix monte
    if btc_balance > 0 and price > btc_buy_price:
        new_stop = price * (1 - trailing_stop_percentage / 100)
        if new_stop > trailing_stop_price:
            trailing_stop_price = new_stop
            print(f"🛡️ Nouveau trailing stop : {trailing_stop_price:.2f} USD")

    # Vérifie si on touche le trailing stop
    if btc_balance > 0 and price <= trailing_stop_price:
        sell_all_btc(price)
        trailing_stop_price = None
        btc_buy_price = None

    print(f"💰 Solde USD: {usd_balance:.2f}, BTC: {btc_balance:.6f}")

    # Heartbeat pendant la pause
    for i in range(int(sleep_time / 60), 0, -1):
        print(f"⏳ Bot en veille, prochaine action dans {i} minute(s)...")
        time.sleep(60)
