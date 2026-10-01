#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required." >&2
  exit 1
fi

wait_http() {
  local url="$1"
  local i code
  for i in $(seq 1 60); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)"
    case "$code" in
      200|301|302|303) return 0 ;;
    esac
    sleep 3
  done
  echo "Timed out waiting for ${url}" >&2
  return 1
}

capture() {
  local url="$1"
  local dest="$2"
  local i
  for i in $(seq 1 20); do
    if curl -fsS "$url" -o "$dest"; then
      return 0
    fi
    sleep 3
  done
  echo "Could not capture ${url}" >&2
  return 1
}

install_wp() {
  local service="$1"
  local url="$2"
  local title="$3"
  docker compose exec -T "$service" bash -s <<EOF
set -euo pipefail
if [ ! -s /tmp/wp-cli.phar ]; then
  php -r 'copy("https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar", "/tmp/wp-cli.phar");' \
    || { apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl && curl -fsSL -o /tmp/wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar; }
fi
cd /var/www/html
if ! php /tmp/wp-cli.phar core is-installed --allow-root >/dev/null 2>&1; then
  php /tmp/wp-cli.phar core install --allow-root \
    --url="${url}" \
    --title="${title}" \
    --admin_user="archivist" \
    --admin_password="local-archivist" \
    --admin_email="archivist@localhost.invalid" \
    --skip-email
fi
EOF
}

docker compose up -d --build

echo "Waiting for the database seed..."
ready=0
for _ in $(seq 1 40); do
  if docker compose exec -T db mysql -uroot -plocal-root -N -e "SELECT COUNT(*) FROM fieldnote.fn_titles" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 3
done
if [ "$ready" -ne 1 ]; then
  echo "Database did not finish seeding. If this volume was created earlier, reset it with: docker compose down -v" >&2
  exit 1
fi

wait_http "http://localhost:8081/wp-login.php"
wait_http "http://localhost:8082/wp-login.php"
wait_http "http://localhost:8083/wp-login.php"
install_wp fieldnote "http://localhost:8081" "Fieldnote"
install_wp ashford "http://localhost:8082" "Ashford Registry"
install_wp lumen "http://localhost:8083" "Lumen Floor"

wait_http "http://localhost:8084/track"
wait_http "http://localhost:8085/apply"
wait_http "http://localhost:8086/holdings"
wait_http "http://localhost:8087/reading-room"

mkdir -p snapshots
capture "http://localhost:8081/catalog?q=harbor&page=1" snapshots/fieldnote-catalog.html
capture "http://localhost:8082/directory" snapshots/ashford-directory.html
capture "http://localhost:8083/console" snapshots/lumen-console.html
capture "http://localhost:8084/track?limit=8" snapshots/waybill-track.html
capture "http://localhost:8085/apply" snapshots/halden-apply.html
capture "http://localhost:8086/holdings?page=1" snapshots/stockwell-holdings.html
capture "http://localhost:8087/reading-room?gloss=Marginal%20note%20in%20a%20later%20hand.&shelf=west-cloister&leaf=2" snapshots/vellum-reading-room.html

jar="$(mktemp)"
curl -sS -c "$jar" -b "$jar" -o /dev/null \
  --data-urlencode "advisor=Professor Hale" \
  --data-urlencode "program=history" \
  --data-urlencode "pages=24" \
  "http://localhost:8085/apply/profile"
curl -sS -c "$jar" -b "$jar" -o /dev/null \
  --data-urlencode "statement=A short study of the harbor customary." \
  --data-urlencode "copies=2" \
  "http://localhost:8085/apply/materials"
curl -fsS -b "$jar" "http://localhost:8085/apply/review" -o snapshots/halden-review.html
rm -f "$jar"
grep -q "Professor Hale" snapshots/halden-review.html

echo "Services are up."
echo "  Fieldnote          http://localhost:8081/catalog"
echo "  Ashford Registry   http://localhost:8082/directory"
echo "  Lumen Floor        http://localhost:8083/console"
echo "  Waybill Desk       http://localhost:8084/track"
echo "  Halden Seminar     http://localhost:8085/apply"
echo "  Stockwell Register http://localhost:8086/holdings"
echo "  Vellum Room        http://localhost:8087/reading-room"
echo "WordPress desk login is archivist / local-archivist."
echo "Frozen pages are in snapshots/."
