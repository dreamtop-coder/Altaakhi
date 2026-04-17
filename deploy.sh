#!/usr/bin/env bash
# Idempotent deploy script for Ubuntu 22.04+ (placeholders; edit before run)
# Usage: bash deploy.sh    or    DOMAIN=example.com REPO_URL=... bash deploy.sh --noninteractive --dry-run

set -euo pipefail

#########################################
# Defaults / placeholders (override via env or interactive prompt)
DOMAIN="yourdomain.com"
REPO_URL="https://github.com/your-username/your-repo.git"
APP_USER="workshop"
APP_DIR="/srv/workshop-app"
DB_NAME="workshop_prod"
DB_USER="workshop_user"
DB_PASS="strongpass"
SECRET_KEY="change-me-in-production"
NONINTERACTIVE=0
DRY_RUN=false
ENABLE_SSL=false
EMAIL="admin@yourdomain.com"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --noninteractive) NONINTERACTIVE=1; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --enable-ssl) ENABLE_SSL=true; shift ;;
    --email) EMAIL="$2"; shift 2 ;;
    --domain) DOMAIN="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    *) shift ;;
  esac
done

prompt_if_empty() {
  local varname="$1"; local prompt_text="$2"
  local val
  val="${!varname:-}"
  if [[ -z "$val" && $NONINTERACTIVE -eq 0 ]]; then
    read -rp "$prompt_text: " val
    export "$varname"="$val"
  fi
}

# Interactive prompts (unless noninteractive)
prompt_if_empty DOMAIN "Domain (example.com)"
prompt_if_empty REPO_URL "Git repo URL"
prompt_if_empty APP_USER "App system user"
prompt_if_empty APP_DIR "App directory"
prompt_if_empty DB_NAME "Postgres DB name"
prompt_if_empty DB_USER "Postgres DB user"
prompt_if_empty DB_PASS "Postgres DB password"
prompt_if_empty SECRET_KEY "Django SECRET_KEY (or leave placeholder)"

echo "Deploy settings:" 
echo "  DOMAIN=$DOMAIN"
echo "  REPO_URL=$REPO_URL"
echo "  APP_USER=$APP_USER"
echo "  APP_DIR=$APP_DIR"
echo "  DB_NAME=$DB_NAME"
echo "  DB_USER=$DB_USER"
echo "  ENABLE_SSL=$ENABLE_SSL"
echo "  DRY_RUN=$DRY_RUN"

#########################################
# Helpers
run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] $*"
  else
    eval "$*"
  fi
}

#########################################
# Basic system check
command -v git >/dev/null 2>&1 || { echo >&2 "git is required. Install packages first."; exit 1; }

#########################################
# 1) Create app user (idempotent)
if id "$APP_USER" &>/dev/null; then
  echo "User $APP_USER already exists"
else
  echo "Creating user $APP_USER"
  run_cmd "sudo adduser --disabled-password --gecos \"\" $APP_USER"
fi

#########################################
# 2) Install OS packages (idempotent apt-get)
if [[ $NONINTERACTIVE -eq 0 ]]; then
  read -rp "Install system packages (apt) if missing? [y/N]: " _installpkgs
  _installpkgs=${_installpkgs:-N}
else
  _installpkgs=Y
fi
if [[ "${_installpkgs^^}" == "Y" ]]; then
  run_cmd "sudo apt update"
  run_cmd "sudo apt install -y python3-pip python3-venv build-essential libpq-dev nginx postgresql postgresql-contrib"
fi

#########################################
# 3) PostgreSQL: create role+db if missing (idempotent)
echo "Configuring PostgreSQL database and role (may require sudo)"
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" || true)
if [[ "$DB_EXISTS" != "1" ]]; then
  echo "Creating database $DB_NAME and role $DB_USER"
  run_cmd "sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\" || true"
  run_cmd "sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""
else
  echo "Database $DB_NAME already exists"
fi

#########################################
# 4) Clone or update repo (idempotent)
if [[ ! -d "$APP_DIR" ]]; then
  echo "Cloning repository into $APP_DIR"
  run_cmd "sudo mkdir -p \"$(dirname \"$APP_DIR\")\""
  run_cmd "sudo git clone $REPO_URL $APP_DIR"
  run_cmd "sudo chown -R $APP_USER:$APP_USER $APP_DIR"
else
  echo "Repository exists in $APP_DIR — pulling latest"
  run_cmd "sudo -u $APP_USER bash -c 'cd \"$APP_DIR\" && git pull || true'"
fi

#########################################
# 5) Python virtualenv & install requirements
run_cmd "sudo -u $APP_USER bash -c 'cd \"$APP_DIR\" && python3 -m venv .venv'"
echo "Installing Python packages inside virtualenv (this may take a while)"
run_cmd "sudo -u $APP_USER bash -c 'source \"$APP_DIR\"/.venv/bin/activate && pip install -U pip && pip install -r \"$APP_DIR\"/requirements.txt'"

#########################################
# 6) Create .env file (idempotent) — DO NOT include secrets in repo
ENVFILE="$APP_DIR/.env"
if [[ -f "$ENVFILE" ]]; then
  echo ".env already exists at $ENVFILE — backing up to ${ENVFILE}.bak"
  run_cmd "sudo cp $ENVFILE ${ENVFILE}.bak"
fi
echo "Creating .env with placeholders at $ENVFILE"
if [[ "$DRY_RUN" == "true" ]]; then
  cat <<EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN
DATABASE_URL=postgres://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
EOF
else
  sudo tee "$ENVFILE" >/dev/null <<EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN
DATABASE_URL=postgres://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
EOF
  sudo chown "$APP_USER":"$APP_USER" "$ENVFILE"
  sudo chmod 600 "$ENVFILE"
fi

#########################################
# 7) Django migrations & collectstatic
echo "Running migrations and collectstatic"
run_cmd "sudo -u $APP_USER bash -c 'source \"$APP_DIR\"/.venv/bin/activate && cd \"$APP_DIR\" && python manage.py migrate --noinput'"
run_cmd "sudo -u $APP_USER bash -c 'source \"$APP_DIR\"/.venv/bin/activate && cd \"$APP_DIR\" && python manage.py collectstatic --noinput'"

#########################################
# 8) systemd service for Gunicorn (idempotent write)
GUNICORN_UNIT="/etc/systemd/system/gunicorn.service"
echo "Writing systemd unit to $GUNICORN_UNIT (will overwrite with backup)"
run_cmd "sudo cp -n $GUNICORN_UNIT ${GUNICORN_UNIT}.bak 2>/dev/null || true"
CPU_CORES=$(nproc)
WORKERS=$((CPU_CORES * 2 + 1))
echo "Detected CPU cores: $CPU_CORES -> gunicorn workers: $WORKERS"

if [[ "$DRY_RUN" == "true" ]]; then
  cat <<EOF
[Unit]
Description=Gunicorn daemon for workshop
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENVFILE
ExecStart=$APP_DIR/.venv/bin/gunicorn workshop.wsgi:application \
    --name workshop_gunicorn \
    --workers $WORKERS \
    --bind unix:/run/gunicorn.sock \
    --access-logfile - \
    --error-logfile -

Restart=always

[Install]
WantedBy=multi-user.target
EOF
else
  sudo tee "$GUNICORN_UNIT" >/dev/null <<EOF
[Unit]
Description=Gunicorn daemon for workshop
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENVFILE
ExecStart=$APP_DIR/.venv/bin/gunicorn workshop.wsgi:application \
    --name workshop_gunicorn \
    --workers $WORKERS \
    --bind unix:/run/gunicorn.sock \
    --access-logfile - \
    --error-logfile -

Restart=always

[Install]
WantedBy=multi-user.target
EOF
  run_cmd "sudo systemctl daemon-reload"
  run_cmd "sudo systemctl enable --now gunicorn || sudo systemctl restart gunicorn || true"
fi

#########################################
# 9) Nginx site (idempotent)
NGINX_SITE="/etc/nginx/sites-available/workshop"
echo "Writing Nginx config to $NGINX_SITE"
if [[ "$DRY_RUN" == "true" ]]; then
  cat <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /static/ {
        alias $APP_DIR/staticfiles/;
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    client_max_body_size 20M;
}
EOF
else
  sudo tee "$NGINX_SITE" >/dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /static/ {
        alias $APP_DIR/staticfiles/;
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }

    client_max_body_size 20M;
}
EOF
  run_cmd "sudo ln -sf $NGINX_SITE /etc/nginx/sites-enabled/workshop"
  run_cmd "sudo nginx -t"
  run_cmd "sudo systemctl restart nginx"
fi

#########################################
# 10) Certbot automation (optional)
if [[ "$ENABLE_SSL" == "true" ]]; then
  if ! command -v certbot &> /dev/null; then
    run_cmd "sudo apt install -y certbot python3-certbot-nginx"
  fi
  echo "Requesting certificates for $DOMAIN"
  run_cmd "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL"
else
  echo "SSL not enabled (ENABLE_SSL=false) — skipping certbot"
fi

#########################################
# 11) Final ownership/fixups
run_cmd "sudo chown -R $APP_USER:www-data $APP_DIR"
run_cmd "sudo chmod -R 750 $APP_DIR"

#########################################
# 12) Health check
echo "Performing health check against http://$DOMAIN/health/"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY RUN] curl -f http://$DOMAIN/health/"
else
  if curl -fsS "http://$DOMAIN/health/" >/dev/null 2>&1; then
    echo "Health check OK"
  else
    echo "Health check failed — check gunicorn/nginx logs"
  fi
fi

echo "Deploy finished. Perform smoke tests in the browser and check logs:" 
echo "  sudo journalctl -u gunicorn -f" 
echo "  sudo tail -f /var/log/nginx/error.log"

echo "If you need to re-run, update variables at top or re-export env and run again."

exit 0
