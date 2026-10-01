$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required."
}

function Wait-Http([string]$Url) {
    for ($i = 0; $i -lt 60; $i++) {
        $code = curl.exe -s -o NUL -w "%{http_code}" $Url
        if ($code -match "^(200|301|302|303)$") {
            return
        }
        Start-Sleep -Seconds 3
    }
    throw "Timed out waiting for $Url"
}

function Save-Page([string]$Url, [string]$Dest) {
    for ($i = 0; $i -lt 20; $i++) {
        curl.exe -fsS $Url -o $Dest
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 3
    }
    throw "Could not capture $Url"
}

function Install-WpSite([string]$Service, [string]$Url, [string]$Title) {
    $script = @"
set -euo pipefail
if [ ! -s /tmp/wp-cli.phar ]; then
  php -r 'copy("https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar", "/tmp/wp-cli.phar");' \
    || { apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl && curl -fsSL -o /tmp/wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar; }
fi
cd /var/www/html
if ! php /tmp/wp-cli.phar core is-installed --allow-root >/dev/null 2>&1; then
  php /tmp/wp-cli.phar core install --allow-root \
    --url="$Url" \
    --title="$Title" \
    --admin_user="archivist" \
    --admin_password="local-archivist" \
    --admin_email="archivist@localhost.invalid" \
    --skip-email
fi
"@
    $script = ($script -replace "`r", "").Trim() + "`n"
    $tmp = Join-Path $PSScriptRoot ".install-$Service.sh"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmp, $script, $utf8)
    $proc = Start-Process -FilePath "docker" -ArgumentList @("compose", "exec", "-T", $Service, "bash", "-s") -RedirectStandardInput $tmp -WorkingDirectory $PSScriptRoot -Wait -PassThru -NoNewWindow
    Remove-Item $tmp -ErrorAction SilentlyContinue
    if ($proc.ExitCode -ne 0) {
        throw "WordPress install failed for $Service"
    }
}

docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed"
}

Write-Host "Waiting for the database seed..."
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    docker compose exec -T db mysql -uroot -plocal-root -N -e "SELECT COUNT(*) FROM fieldnote.fn_titles" *> $null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 3
}
if (-not $ready) {
    throw "Database did not finish seeding. If this volume was created earlier, reset it with: docker compose down -v"
}

Wait-Http "http://localhost:8081/wp-login.php"
Wait-Http "http://localhost:8082/wp-login.php"
Wait-Http "http://localhost:8083/wp-login.php"
Install-WpSite "fieldnote" "http://localhost:8081" "Fieldnote"
Install-WpSite "ashford" "http://localhost:8082" "Ashford Registry"
Install-WpSite "lumen" "http://localhost:8083" "Lumen Floor"

Wait-Http "http://localhost:8084/track"
Wait-Http "http://localhost:8085/apply"
Wait-Http "http://localhost:8086/holdings"
Wait-Http "http://localhost:8087/reading-room"

New-Item -ItemType Directory -Force -Path "snapshots" | Out-Null
Save-Page "http://localhost:8081/catalog?q=harbor&page=1" "snapshots/fieldnote-catalog.html"
Save-Page "http://localhost:8082/directory" "snapshots/ashford-directory.html"
Save-Page "http://localhost:8083/console" "snapshots/lumen-console.html"
Save-Page "http://localhost:8084/track?limit=8" "snapshots/waybill-track.html"
Save-Page "http://localhost:8085/apply" "snapshots/halden-apply.html"
Save-Page "http://localhost:8086/holdings?page=1" "snapshots/stockwell-holdings.html"
Save-Page "http://localhost:8087/reading-room?gloss=Marginal%20note%20in%20a%20later%20hand.&shelf=west-cloister&leaf=2" "snapshots/vellum-reading-room.html"

$jar = Join-Path $env:TEMP "halden-cookies.txt"
Remove-Item $jar -ErrorAction SilentlyContinue
curl.exe -sS -c $jar -b $jar -o NUL --data-urlencode "advisor=Professor Hale" --data-urlencode "program=history" --data-urlencode "pages=24" "http://localhost:8085/apply/profile"
curl.exe -sS -c $jar -b $jar -o NUL --data-urlencode "statement=A short study of the harbor customary." --data-urlencode "copies=2" "http://localhost:8085/apply/materials"
curl.exe -fsS -b $jar "http://localhost:8085/apply/review" -o "snapshots/halden-review.html"
if ($LASTEXITCODE -ne 0) {
    throw "Could not capture the Halden review sheet."
}
Remove-Item $jar -ErrorAction SilentlyContinue
if (-not (Select-String -Path "snapshots/halden-review.html" -Pattern "Professor Hale" -Quiet)) {
    throw "The Halden review sheet did not keep the session."
}

Write-Host "Services are up."
Write-Host "  Fieldnote          http://localhost:8081/catalog"
Write-Host "  Ashford Registry   http://localhost:8082/directory"
Write-Host "  Lumen Floor        http://localhost:8083/console"
Write-Host "  Waybill Desk       http://localhost:8084/track"
Write-Host "  Halden Seminar     http://localhost:8085/apply"
Write-Host "  Stockwell Register http://localhost:8086/holdings"
Write-Host "  Vellum Room        http://localhost:8087/reading-room"
Write-Host "WordPress desk login is archivist / local-archivist."
Write-Host "Frozen pages are in snapshots/."
