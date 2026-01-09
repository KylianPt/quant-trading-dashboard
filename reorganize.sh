#!/bin/bash

echo "📂 Création des nouveaux dossiers..."
# Création de l'arborescence (-p permet de ne pas planter si le dossier existe déjà)
mkdir -p src/data
mkdir -p src/logic
mkdir -p src/ui
mkdir -p src/jobs
mkdir -p assets

echo "🚚 Déplacement des fichiers DATA..."
mv src/database.py src/data/
mv src/data_loader.py src/data/
mv src/fetch_live_data.py src/data/
mv src/mock_generator.py src/data/
mv src/data_single_asset.py src/data/

echo "🚚 Déplacement des fichiers LOGIC..."
mv src/metrics.py src/logic/
mv src/optimization.py src/logic/
mv src/prediction.py src/logic/
mv src/portfolio_logic.py src/logic/
mv src/portfolio_manager.py src/logic/
mv src/strategies_single.py src/logic/
mv src/single_logic.py src/logic/

echo "🚚 Déplacement des fichiers UI (Vues & Composants)..."
mv src/views_portfolio.py src/ui/
mv src/views_single.py src/ui/
mv src/views_reports.py src/ui/
mv src/ui_components.py src/ui/
mv src/single_components.py src/ui/

echo "🚚 Déplacement des fichiers JOBS (Scripts de fond)..."
mv src/job_scheduler.py src/jobs/
mv src/daily_report.py src/jobs/

echo "🚚 Déplacement des CSV vers assets/..."
mv src/*.csv assets/ 2>/dev/null || echo "⚠️ Pas de CSV trouvés ou déjà déplacés."

echo "✨ Création des fichiers __init__.py pour Python..."
touch src/data/__init__.py
touch src/logic/__init__.py
touch src/ui/__init__.py
touch src/jobs/__init__.py

echo "✅ Rangement terminé !"
echo "⚠️  N'oublie pas de lancer le script Python 'fix_imports.py' que je t'ai donné juste avant pour corriger les liens dans le code !"