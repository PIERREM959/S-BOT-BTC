import yfinance as yf
import time
import smtplib
from email.message import EmailMessage

# ===== Paramètres ajustables =====
investment_amount = 0.001  # BTC à acheter toutes les 15 min
trailing_stop_percentage = 0.3  # en %
usd_balance = 10000.0
btc_balance = 0.0
btc_buy_price = None
trailing_stop_price = None

import os

# Email config (à remplacer par tes infos)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def get_btc_price():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="1d", interval="1m")  # Utilise period=1d pour avoir des données
    if data.empty:
        print("⚠️ Pas de données reçues, on réessaie dans 1 min...")
        time.sleep(60)
        return get_btc_price()  # On retente
    return data["Close"].iloc[-1]


def buy_btc(price):
    global usd_balance, btc_balancedef get_btc_price():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="1d", interval="1m")  # Utilise period=1d pour avoir des données
    if data.empty:
        print("⚠️ Pas de données reçues, on réessaie dans 1 min...")
        time.sleep(60)
        return get_btc_price()  # On retente
    return data["Close"].iloc[-1]

    cost = investment_amount * price
    if usd_balance >= cost:
        usd_balance -= cost
        btc_balance += investment_amount
        print(f"Achat : {investment_amount} BTC à {price:.2f} USD")
        return True
    else:
        print("Solde insuffisant pour acheter.")
        return False

def sell_all_btc(price):
    global usd_balance, btc_balance
    if btc_balance > 0:
        usd_balance += btc_balance * price
        print(f"Vente : {btc_balance:.6f} BTC à {price:.2f} USD")
        send_email(
            "Vente exécutée - S Bot BTC",
            f"Vente effectuée à {price:.2f} USD\n"
            f"Solde USD: {usd_balance:.2f}\nSolde BTC: 0.0"
        )
        btc_balance = 0.0

# ===== Main Loop =====
while True:
    price = get_btc_price()
    print(f"Prix actuel BTC : {price:.2f} USD")

    # Achat toutes les 15 minutes
    if buy_btc(price):
        if trailing_stop_price is None:
            trailing_stop_price = price * (1 - trailing_stop_percentage / 100)
        btc_buy_price = price

    # Mise à jour du trailing stop si le prix monte
    if btc_balance > 0 and price > btc_buy_price:
        new_stop = price * (1 - trailing_stop_percentage / 100)
        if new_stop > trailing_stop_price:
            trailing_stop_price = new_stop
            print(f"Nouveau trailing stop : {trailing_stop_price:.2f} USD")

    # Vérifie si on touche le trailing stop
    if btc_balance > 0 and price <= trailing_stop_price:
        sell_all_btc(price)
        trailing_stop_price = None
        btc_buy_price = None

    print(f"Solde USD: {usd_balance:.2f}, BTC: {btc_balance:.6f}")
    time.sleep(900)  # Pause 15 minutes

