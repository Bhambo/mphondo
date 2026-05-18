#!/usr/bin/env bash
# =============================================================
# Mphondo v3 — Deploy script
# Ejecutar desde tu máquina local:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Requisitos:
#   - SSH access to claude@172.16.75.134
#   - .env rellenado en ./infra/.env
# =============================================================

set -euo pipefail

RPI_HOST="claude@172.16.75.134"
RPI_DIR="/srv/projects/mphondo"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"  # raíz del repo

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Verificar que .env existe ──────────────────────────────────────────────
[[ -f "$LOCAL_DIR/infra/.env" ]] || error ".env no encontrado en infra/. Copia .env.example y rellena los valores."

# ── Verificar SSH ──────────────────────────────────────────────────────────
info "Verificando conexión SSH a $RPI_HOST..."
ssh -o ConnectTimeout=10 -o BatchMode=yes "$RPI_HOST" "echo ok" 2>/dev/null \
  || error "No se puede conectar a $RPI_HOST. Verifica SSH y credenciales."

# ── Crear estructura en RPi si no existe ──────────────────────────────────
info "Preparando estructura de directorios..."
ssh "$RPI_HOST" "mkdir -p $RPI_DIR/{infra/{supabase,monitoring/{grafana/{dashboards,datasources},prometheus.yml},postgres-init},backend,logs}"

# ── Sincronizar infra ──────────────────────────────────────────────────────
info "Sincronizando infra/..."
rsync -avz --delete \
  --exclude='.env' \
  "$LOCAL_DIR/infra/" "$RPI_HOST:$RPI_DIR/infra/"

# ── Copiar .env (nunca en git) ──────────────────────────────────────────────
info "Copiando .env..."
scp "$LOCAL_DIR/infra/.env" "$RPI_HOST:$RPI_DIR/infra/.env"

# ── Copiar schema SQL ──────────────────────────────────────────────────────
info "Copiando schema SQL..."
scp "$LOCAL_DIR/backend/alembic/versions/001_initial_schema.sql" \
    "$RPI_HOST:$RPI_DIR/backend/001_initial_schema.sql"

# ── Pull imagen Docker (si existe en GHCR) ────────────────────────────────
info "Verificando imagen API en GHCR..."
GITHUB_REPO=$(grep GITHUB_REPOSITORY "$LOCAL_DIR/infra/.env" | cut -d'=' -f2 || echo "bhambo/mphondo")
GHCR_TOKEN=$(grep GHCR_TOKEN "$LOCAL_DIR/infra/.env" | cut -d'=' -f2 || true)

if [[ -n "$GHCR_TOKEN" ]]; then
  ssh "$RPI_HOST" "echo $GHCR_TOKEN | docker login ghcr.io -u bhambo --password-stdin 2>/dev/null || true"
fi

# ── Arrancar/reiniciar servicios ──────────────────────────────────────────
info "Desplegando con docker compose..."
ssh "$RPI_HOST" "
  cd $RPI_DIR/infra && \
  docker compose pull --quiet 2>/dev/null || true && \
  docker compose up -d --remove-orphans
"

# ── Ejecutar schema SQL (primera vez) ─────────────────────────────────────
info "Comprobando si el schema ya está aplicado..."
SCHEMA_APPLIED=$(ssh "$RPI_HOST" "
  docker exec mphondo-db psql -U mphondo mphondo -tAc \
  \"SELECT COUNT(*) FROM information_schema.tables WHERE table_name='accounts'\" \
  2>/dev/null || echo 0
")

if [[ "$SCHEMA_APPLIED" == "0" ]]; then
  info "Aplicando schema SQL inicial..."
  ssh "$RPI_HOST" "
    docker exec -i mphondo-db psql -U mphondo mphondo \
    < $RPI_DIR/backend/001_initial_schema.sql
  "
  info "Schema aplicado correctamente."
else
  info "Schema ya existente — no se vuelve a aplicar."
fi

# ── Verificar salud ────────────────────────────────────────────────────────
info "Esperando que la API arranque (max 60s)..."
for i in {1..12}; do
  sleep 5
  HEALTH=$(ssh "$RPI_HOST" "curl -sf http://localhost:8000/api/health 2>/dev/null || echo 'NOT_UP'")
  if [[ "$HEALTH" == *'"status":"ok"'* ]]; then
    info "API healthy: $HEALTH"
    break
  fi
  echo "  Intento $i/12..."
done

info "docker compose ps:"
ssh "$RPI_HOST" "cd $RPI_DIR/infra && docker compose ps"

echo ""
echo "============================================="
echo " Mphondo v3 — Deploy completado"
echo "============================================="
info "Endpoints disponibles (vía Tailscale):"
echo "  API:      https://<tu-host>.ts.net/api/docs"
echo "  Grafana:  https://<tu-host>.ts.net/grafana"
echo "  Health:   https://<tu-host>.ts.net/health"
echo "============================================="
