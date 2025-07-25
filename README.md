# S-BOT-BTC (Render + Analyse)

## ✅ Fonctionnalités
- Achat toutes les 15 min si Prix > MM50
- Trailing Stop dynamique (0,4%)
- Solde fictif en USD & BTC
- Envoi email (vente + rapport horaire)
- Suivi CSV des performances
- Script d'analyse avec graphique

---

## ✅ Déploiement sur Render
1. Créez un **Background Worker** sur Render.
2. Ajoutez les fichiers `s_bot_btc.py` et `requirements.txt`.
3. Configurez les **Variables d'environnement** :
   - `EMAIL_ADDRESS`
   - `EMAIL_PASSWORD`
   - `TO_EMAIL`
4. Déployez !

---

## ✅ Analyse des performances
- Téléchargez `sbot_performance.csv` depuis Render.
- Exécutez `analyse_sbot.py` en local :
```bash
python analyse_sbot.py
