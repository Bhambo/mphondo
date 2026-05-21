#!/usr/bin/env python3
"""
Webhook listener para GitHub push events.
Recibe POST de GitHub, verifica HMAC-SHA256, lanza deploy.sh.

Configuración:
  WEBHOOK_SECRET  — mismo secret configurado en GitHub
  WEBHOOK_PORT    — puerto (default 9000)
  DEPLOY_SCRIPT   — ruta al deploy.sh (default /mnt/data/projects/mphondo/src/infra/deploy.sh)
"""
import hashlib
import hmac
import http.server
import json
import logging
import os
import subprocess
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("webhook")

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").encode()
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "9000"))
DEPLOY_SCRIPT = os.environ.get(
    "DEPLOY_SCRIPT",
    "/mnt/data/projects/mphondo/src/infra/deploy.sh",
)


def verify_signature(body: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        log.warning("WEBHOOK_SECRET not set — skipping signature check")
        return True
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def run_deploy() -> None:
    log.info("Starting deploy: %s", DEPLOY_SCRIPT)
    try:
        result = subprocess.run(
            ["/bin/bash", DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if result.returncode == 0:
            log.info("Deploy OK\n%s", result.stdout[-2000:])
        else:
            log.error("Deploy FAILED (rc=%d)\n%s", result.returncode, result.stderr[-2000:])
    except subprocess.TimeoutExpired:
        log.error("Deploy timed out after 900s")
    except Exception as exc:
        log.error("Deploy exception: %s", exc)


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: N802
        log.info(fmt, *args)

    def do_POST(self):  # noqa: N802
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        sig = self.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(body, sig):
            log.warning("Bad signature from %s", self.client_address)
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Bad signature")
            return

        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        ref = event.get("ref", "")
        gh_event = self.headers.get("X-GitHub-Event", "")
        log.info("Received %s event, ref=%s", gh_event, ref)

        # Solo deployar en push a main
        if gh_event == "push" and ref == "refs/heads/main":
            self.send_response(202)
            self.end_headers()
            self.wfile.write(b"Deploying")
            thread = threading.Thread(target=run_deploy, daemon=True)
            thread.start()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Ignored")


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    log.info("Webhook listening on port %d", WEBHOOK_PORT)
    log.info("Deploy script: %s", DEPLOY_SCRIPT)
    server.serve_forever()
