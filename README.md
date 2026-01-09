# quant-trading-dashboard
Projet de dashboard de trading quantitatif - (python, Linux) - ESILV

Un tableau de bord financier interactif construit avec Python et Streamlit. Cette application permet aux utilisateurs d'analyser des actifs individuels, de construire et d'optimiser des portefeuilles d'investissement, et de générer des rapports de marché automatisés.

## Fonctionnalités Principales

### 1. Analyse d'Actif Unique (Single Asset)
* Visualisation des prix historiques et indicateurs techniques.
* Comparaison de stratégies (Buy & Hold vs Moyennes Mobiles vs MACD).
* Prédiction de prix future via Machine Learning (Régression Linéaire, Random Forest, ARIMA).
* Intervalle de confiance et métriques de performance.

### 2. Gestion de Portefeuille (Portfolio Simulation)
* **Optimisation :** Calcul automatique des pondérations (Max Sharpe, Min Volatility, Equal Weight).
* **Simulation Monte Carlo :** Génération de 1000 scénarios pour visualiser la frontière efficiente.
* **Backtesting :** Simulation de performance historique avec rééquilibrage et Stop-Loss.
* **Analyse :** Matrice de corrélation, volatilité annualisée, Ratio de Sharpe et Drawdown.

### 3. Rapports de Marché (Reports)
* Base de données SQL persistante stockant l'historique des prix.
* Génération automatique de rapports horaires et journaliers.
* Visualisation des données "Snapshot" (Volatilité 24h, Prix de clôture).

### 4. Communauté
* Partage de portefeuilles avec la communauté.
* Flux d'activité des stratégies publiées par d'autres utilisateurs.

## Architecture du Projet (MVC)

Le projet suit une structure modulaire pour assurer la maintenabilité :

```text
├── src/
│   ├── app_dashboard.py     # Point d'entrée principal
│   ├── data/                # Gestion des données (Loader, API Yahoo, SQLite)
│   ├── logic/               # Cœur mathématique (Optimisation, Métriques, ML)
│   ├── ui/                  # Vues Streamlit et Composants graphiques
│   └── jobs/                # Tâches d'arrière-plan (Scheduler)
├── assets/                  # Fichiers statiques (CSV)
└── tests/                   # Tests unitaires