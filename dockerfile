FROM python:3.11-slim-bookworm

WORKDIR /app

# 1. Installer Cron et les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 2. Copier les requirements et installer
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# 3. Copier tout le code
COPY . .

# 4. Configurer Cron
COPY crontab /etc/cron.d/scheduler-cron
RUN chmod 0644 /etc/cron.d/scheduler-cron
RUN crontab /etc/cron.d/scheduler-cron
RUN touch /var/log/cron.log

# 5. Configurer le script de démarrage
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 6. Ouvrir le port
EXPOSE 8080

# 7. Lancement
CMD ["/start.sh"]
