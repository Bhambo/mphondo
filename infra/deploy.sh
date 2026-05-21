#!/usr/bin/env bash
# =============================================================
# Mphondo v3 — Deploy script (ejecutar directamente en la RPi)
# Ruta en RPi: /mnt/data/projects/mphondo/src/infra/deploy.sh
#
# Uso:
#   ./deploy.sh                   # deploy completo
#   ./deploy.sh --skip-frontend   # solo API
#   ./deploy.sh --skip-api        # solo frontend
# =============================================================
set -euo pipefail

SRC=/mnt/data/projects/mphondo/src
INFRA=/mnt/data/projects/mphondo/infra
WEB=/mnt/data/projects/mphondo/frontend-web
LOG_DIR=/mnt/data/logs

SKIP_FRONTEND=false
SKIP_API=false
for arg in "$@"; do
  case $arg in
    --skip-frontend) SKIP_FRONTEND=true ;;
    --skip-api)      SKIP_API=true ;;
  esac
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
step()  { echo -e "\n${GREEN}▶ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠  $*${NC}"; }
fail()  { echo -e "${RED}✗ $*${NC}"; exit 1; }

mkdir -p "$LOG_DIR" "$WEB"
LOGFILE="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOGFILE") 2>&1

echo "================================================="
echo "  DEPLOY  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================="

# ── 1. Actualizar código fuente ───────────────────────────────
step "[1/5] git pull origin main"
git -C "$SRC" pull origin main

# ── 2. Sincronizar archivos infra (sin .env ni postgres-init) ─
step "[2/5] rsync infra -> live"
rsync -a --delete \
  --exclude='.env' \
  --exclude='postgres-init' \
  "$SRC/infra/" "$INFRA/"

# postgres-init solo se copia si aún no existe en live
[ -d "$INFRA/postgres-init" ] || cp -r "$SRC/infra/postgres-init" "$INFRA/"

# ── 3. Build imagen API (ARM64 nativo, solo si cambió backend/) ──
if [ "$SKIP_API" = false ]; then
  # Detectar si hay cambios en backend/ desde el último build
  LAST_BUILD_FILE="$INFRA/.last-api-build-commit"
  LAST_BUILD=$(cat "$LAST_BUILD_FILE" 2>/dev/null || echo "none")
  CURRENT=$(git -C "$SRC" rev-parse HEAD)
  BACKEND_CHANGED=$(git -C "$SRC" diff --name-only "$LAST_BUILD" "$CURRENT" 2>/dev/null | grep "^backend/" || true)

  if [ "$LAST_BUILD" = "none" ] || [ -n "$BACKEND_CHANGED" ]; then
    step "[3/5] docker build mphondo-api:local (cambios en backend detectados)"
    docker build \
      --platform linux/arm64 \
      --tag mphondo-api:local \
      "$SRC/backend/"
    echo "$CURRENT" > "$LAST_BUILD_FILE"
    echo "  imagen OK: $(docker images mphondo-api:local --format '{{.Size}}')"
  else
    warn "[3/5] Sin cambios en backend/ — omitiendo docker build"
  fi
else
  warn "[3/5] --skip-api: omitido"
fi

# ── 4. Reiniciar API y worker ─────────────────────────────────
step "[4/5] docker compose up api worker"
docker compose -f "$INFRA/docker-compose.yml" --env-file "$INFRA/.env" \
  up -d --no-deps --pull never api worker
echo "  contenedores actualizados"

# ── 5. Build + deploy frontend web ───────────────────────────
if [ "$SKIP_FRONTEND" = false ]; then
  # Detectar si hay cambios en frontend/ desde el último build
  LAST_FE_FILE="$INFRA/.last-fe-build-commit"
  LAST_FE=$(cat "$LAST_FE_FILE" 2>/dev/null || echo "none")
  CURRENT=$(git -C "$SRC" rev-parse HEAD)
  FRONTEND_CHANGED=$(git -C "$SRC" diff --name-only "$LAST_FE" "$CURRENT" 2>/dev/null | grep "^frontend/" || true)

  if [ "$LAST_FE" = "none" ] || [ -n "$FRONTEND_CHANGED" ]; then
    step "[5/5] expo export --platform web (cambios en frontend detectados)"
    warn "NOTA: expo export requiere mucha RAM. Considera hacer el build en Windows y subir via scp."
    warn "      Saltando build en RPi — usar deploy manual para frontend."
    # El frontend se actualiza manualmente desde Windows:
    #   npx expo export --platform web --output-dir ./dist-web --clear
    #   scp -r dist-web/* claude@172.16.75.134:/mnt/data/projects/mphondo/frontend-web/
    echo "$CURRENT" > "$LAST_FE_FILE"
  else
    warn "[5/5] Sin cambios en frontend/ — omitiendo expo export"
  fi

  # Recargar Caddy
  docker exec mphondo-caddy caddy reload \
    --config /etc/caddy/Caddyfile --adapter caddyfile \
    && echo "  caddy recargado" \
    || { warn "caddy reload falló, reiniciando..."; \
         docker compose -f "$INFRA/docker-compose.yml" \
           --env-file "$INFRA/.env" restart caddy; }
else
  warn "[5/5] --skip-frontend: omitido"
fi

# ── Resumen ────────────────────────────────────────────────────
echo ""
echo "================================================="
echo "  DEPLOY OK  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Log: $LOGFILE"
echo "================================================="
