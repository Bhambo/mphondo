#!/usr/bin/env bash
# =============================================================
# Mphondo v3 — Script de setup Raspberry Pi 4
# Ubuntu Server 24.04 LTS (arm64)
# =============================================================
# Ejecutar como root o con sudo:
#   chmod +x setup-rpi.sh
#   sudo ./setup-rpi.sh
#
# Qué hace:
#   1. Actualiza el sistema y configura hostname
#   2. Instala Docker Engine + Compose v2
#   3. Instala y configura Tailscale
#   4. Instala Caddy (con soporte Tailscale TLS)
#   5. Configura UFW (firewall — sólo Tailscale)
#   6. Configura swap (2GB para el RPi)
#   7. Activa SSD externo como almacenamiento principal
#   8. Clona el repositorio y prepara el entorno
#   9. Configura backups automáticos con borgmatic
# =============================================================

set -euo pipefail

HOSTNAME_NEW="mphondo-rpi"
DATA_DIR="/opt/mphondo"
BACKUP_DIR="/mnt/backup"
REPO_URL="https://github.com/${GITHUB_REPOSITORY:-bhambo/mphondo}.git"

# Colores para output
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Ejecutar como root: sudo ./setup-rpi.sh"

# =============================================================
# 1. Actualización del sistema
# =============================================================
info "Actualizando sistema..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
  curl wget git unzip htop \
  ufw fail2ban \
  ca-certificates gnupg lsb-release \
  python3-pip python3-venv \
  borgmatic \
  logrotate

# Hostname
hostnamectl set-hostname "$HOSTNAME_NEW"
info "Hostname configurado: $HOSTNAME_NEW"

# =============================================================
# 2. Swap de 2GB (RPi no tiene swap por defecto en Ubuntu)
# =============================================================
if [[ ! -f /swapfile ]]; then
  info "Configurando swap 2GB..."
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  # Reducir swappiness para el RPi
  sysctl vm.swappiness=10
  echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# =============================================================
# 3. Docker Engine
# =============================================================
if ! command -v docker &>/dev/null; then
  info "Instalando Docker Engine..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  # Añadir usuario actual al grupo docker (si no es root)
  SUDO_USER_NAME="${SUDO_USER:-ubuntu}"
  usermod -aG docker "$SUDO_USER_NAME" 2>/dev/null || true
  info "Docker instalado: $(docker --version)"
else
  info "Docker ya instalado: $(docker --version)"
fi

# =============================================================
# 4. Tailscale
# =============================================================
if ! command -v tailscale &>/dev/null; then
  info "Instalando Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
  systemctl enable tailscaled
  systemctl start tailscaled
  info "Tailscale instalado. Ejecuta manualmente:"
  info "  sudo tailscale up --advertise-exit-node=false"
  info "  Luego anota el hostname MagicDNS para el .env"
else
  info "Tailscale ya instalado"
fi

# =============================================================
# 5. Caddy (con soporte Tailscale)
# =============================================================
if ! command -v caddy &>/dev/null; then
  info "Instalando Caddy..."
  apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
    gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
    tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy
  systemctl enable caddy
  info "Caddy instalado: $(caddy version)"
else
  info "Caddy ya instalado"
fi

# =============================================================
# 6. UFW — Firewall
# =============================================================
info "Configurando UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
# SSH sólo desde red local (seguridad extra)
ufw allow from 192.168.0.0/16 to any port 22 comment "SSH local"
# HTTP/HTTPS para Caddy (Tailscale ya filtra, pero Caddy necesita escuchar)
ufw allow 80/tcp  comment "HTTP (redirect)"
ufw allow 443/tcp comment "HTTPS (Caddy)"
# Tailscale
ufw allow in on tailscale0 comment "Tailscale"
ufw --force enable
info "UFW activo: $(ufw status verbose | head -3)"

# =============================================================
# 7. Fail2ban
# =============================================================
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# =============================================================
# 8. Montar SSD externo (si existe /dev/sda)
# =============================================================
if lsblk /dev/sda &>/dev/null; then
  info "SSD detectado en /dev/sda"
  SSD_PART="/dev/sda1"
  if ! blkid "$SSD_PART" &>/dev/null; then
    warn "Partición $SSD_PART no formateada. Formatea manualmente:"
    warn "  sudo parted /dev/sda mklabel gpt"
    warn "  sudo parted /dev/sda mkpart primary ext4 0% 100%"
    warn "  sudo mkfs.ext4 /dev/sda1"
  else
    mkdir -p "$DATA_DIR"
    SSD_UUID=$(blkid -s UUID -o value "$SSD_PART")
    if ! grep -q "$SSD_UUID" /etc/fstab; then
      echo "UUID=$SSD_UUID  $DATA_DIR  ext4  defaults,noatime  0  2" >> /etc/fstab
      mount -a
      info "SSD montado en $DATA_DIR"
    fi
  fi
else
  warn "No se detectó SSD en /dev/sda — usando tarjeta SD (no recomendado para producción)"
  DATA_DIR="/opt/mphondo"
fi

mkdir -p "$DATA_DIR" "$BACKUP_DIR"

# =============================================================
# 9. Estructura de datos y repositorio
# =============================================================
info "Preparando directorio de datos..."
mkdir -p \
  "$DATA_DIR/postgres" \
  "$DATA_DIR/redis" \
  "$DATA_DIR/uploads" \
  "$DATA_DIR/storage" \
  "$DATA_DIR/prometheus" \
  "$DATA_DIR/grafana" \
  "$DATA_DIR/logs/caddy"

# Clonar repositorio si no existe
if [[ ! -d "$DATA_DIR/app" ]]; then
  info "Clonando repositorio..."
  git clone "$REPO_URL" "$DATA_DIR/app" || warn "Repositorio no disponible aún — clona manualmente"
else
  info "Repositorio ya presente en $DATA_DIR/app"
fi

# =============================================================
# 10. Borgmatic — backups automáticos
# =============================================================
info "Configurando borgmatic..."
mkdir -p /etc/borgmatic /root/.config/borg

cat > /etc/borgmatic/config.yaml <<EOF
repositories:
  - path: $BACKUP_DIR/borg-local
    label: local
  # Descomenta y configura Backblaze B2 cuando tengas la cuenta:
  # - path: ssh://ACCOUNT_ID@ACCOUNT_ID.repo.borgbase.com/./repo
  #   label: remote

source_directories:
  - $DATA_DIR/postgres
  - $DATA_DIR/uploads
  - $DATA_DIR/storage
  - $DATA_DIR/app/infra

exclude_patterns:
  - '*.tmp'
  - '*/node_modules'

compression: lz4

retention:
  keep_daily:   30
  keep_weekly:  12
  keep_monthly: 12

checks:
  - name: repository
  - name: archives
    frequency: 2 weeks

hooks:
  before_backup:
    - docker exec mphondo-db pg_dump -U mphondo mphondo -F c -f /tmp/mphondo_backup.dump
    - docker cp mphondo-db:/tmp/mphondo_backup.dump $DATA_DIR/postgres/mphondo_latest.dump
  on_error:
    - echo "Borgmatic error en \$(hostname) - \$(date)" | curl -d @- ${NTFY_URL:-https://ntfy.sh}/${NTFY_TOPIC:-mphondo-alerts}
EOF

# Cron para borgmatic (1:30 AM diario)
echo "30 1 * * * root borgmatic --verbosity -1 2>&1 | logger -t borgmatic" > /etc/cron.d/borgmatic

# Cron para pg_dump cada 6h (respaldo intermedio)
cat >> /etc/cron.d/mphondo-pgdump <<'EOF'
0 */6 * * * root docker exec mphondo-db pg_dump -U mphondo mphondo -F c \
  -f /tmp/mphondo_6h.dump && \
  docker cp mphondo-db:/tmp/mphondo_6h.dump /opt/mphondo/postgres/mphondo_$(date +\%H).dump \
  2>&1 | logger -t mphondo-pgdump
EOF

# =============================================================
# 11. Logrotate para Caddy
# =============================================================
cat > /etc/logrotate.d/caddy <<'EOF'
/opt/mphondo/logs/caddy/*.log {
  daily
  rotate 14
  compress
  delaycompress
  missingok
  notifempty
  sharedscripts
  postrotate
    systemctl reload caddy 2>/dev/null || true
  endscript
}
EOF

# =============================================================
# Resumen final
# =============================================================
echo ""
echo "============================================="
echo " Mphondo v3 — Setup RPi completado"
echo "============================================="
echo ""
info "Pasos manuales pendientes:"
echo "  1. sudo tailscale up"
echo "     → anota el hostname MagicDNS (ej: mphondo.tail1234.ts.net)"
echo ""
echo "  2. cd $DATA_DIR/app/infra"
echo "     cp .env.example .env"
echo "     nano .env   # rellenar todas las variables"
echo ""
echo "  3. Inicializar repositorio Borg:"
echo "     borg init --encryption=repokey-blake2 $BACKUP_DIR/borg-local"
echo ""
echo "  4. Arrancar servicios:"
echo "     docker compose up -d"
echo ""
echo "  5. Ejecutar schema inicial (primera vez):"
echo "     docker exec -i mphondo-db psql -U mphondo mphondo < backend/alembic/versions/001_initial_schema.sql"
echo ""
echo "  6. Verificar todo OK:"
echo "     docker compose ps"
echo "     curl https://<TU_HOST_TAILSCALE>/health"
echo "============================================="
