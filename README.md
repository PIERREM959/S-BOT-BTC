# S Bot BTC

Bot fictif qui achète du BTC toutes les 15 minutes, applique un trailing stop, et envoie un email lors des ventes.

## ✅ Fonctionnalités
- Achat automatique (par défaut 0.01 BTC toutes les 5 minutes)
- Trailing Stop dynamique (0.2%)
- ET ACHAT SEULEMENT SI COURS > MM30
- si cours < MM30 STANDBY
- VENTE SEULEMENT AU TRALING STOP
- Solde fictif (100000 USD)
- Envoi d'un email après chaque vente
- Logs en temps réel avec heartbeat

---

## ✅ Déploiement sur Render (Background Worker)
1. Poussez votre code sur GitHub.
2. Sur Render :
   - Créez un **Background Worker**
   - **Build Command** :
     ```
     pip install -r requirements.txt
     ```
   - **Start Command** :
     ```
     python s_bot_btc.py
     ```
   - Ajoutez les variables d'environnement :
     ```
     EMAIL_ADDRESS = votre_email
     EMAIL_PASSWORD = votre_mot_de_passe_app
     TO_EMAIL = destinataire_email
     ```
3. Cliquez sur **Create Background Worker**.

---

## ✅ Ajuster les paramètres
Dans `s_bot_btc.py`, vous pouvez modifier :
```python
investment_amount = 0.001  # BTC par achat
trailing_stop_percentage = 0.3  # pourcentage du trailing stop
sleep_time = 900  # intervalle en secondes (15 minutes)
