<?php
/**
 * Plugin Name: Lumen Floor
 * Description: Regional probe console for the Lumen operations floor.
 */

add_filter('redirect_canonical', static function ($redirect) {
    $path = lumen_request_path();
    if ($path === '' || $path === 'console') {
        return false;
    }
    return $redirect;
});

add_action('template_redirect', static function () {
    if (!function_exists('is_blog_installed') || !is_blog_installed()) {
        return;
    }
    $path = lumen_request_path();
    if ($path === '') {
        status_header(200);
        header('Content-Type: text/html; charset=utf-8');
        echo lumen_document(
            'Lumen Floor',
            '<header class="mast"><p class="mark">Lumen Floor</p><h1>Operations</h1></header>'
            . '<main><p>The regional probe console is on the floor display.</p>'
            . '<p><a href="/console">Open the console</a></p></main>'
        );
        exit;
    }
    if ($path === 'console') {
        lumen_render_console();
        exit;
    }
}, 0);

function lumen_request_path(): string
{
    $uri = isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/';
    $path = parse_url($uri, PHP_URL_PATH);
    return is_string($path) ? trim($path, '/') : '';
}

function lumen_regions(): array
{
    return ['harbor', 'estuary', 'ridge', 'basin'];
}

function lumen_selected_region(): string
{
    $raw = (isset($_GET['region']) && is_string($_GET['region'])) ? sanitize_key(wp_unslash($_GET['region'])) : 'harbor';
    return in_array($raw, lumen_regions(), true) ? $raw : 'harbor';
}

function lumen_hour_count(): int
{
    if (!isset($_GET['hours']) || !is_string($_GET['hours'])) {
        return 14;
    }
    $hours = absint(wp_unslash($_GET['hours']));
    if ($hours < 1) {
        return 1;
    }
    if ($hours > 24) {
        return 24;
    }
    return $hours;
}

function lumen_headline(): string
{
    if (!isset($_GET['headline']) || !is_string($_GET['headline'])) {
        return 'Floor status';
    }
    return wp_unslash($_GET['headline']);
}

function lumen_headline_script(string $headline): string
{
    return '<script>window.__LUMEN_FLOOR__={headline:"' . $headline . '"};</script>';
}

function lumen_probes(): array
{
    global $wpdb;
    $rows = $wpdb->get_results(
        "SELECT service_name, region_code, latency_ms, status_label
         FROM lc_probes ORDER BY region_code, service_name"
    );
    return is_array($rows) ? $rows : [];
}

function lumen_render_console(): void
{
    $region = lumen_selected_region();
    $hours = lumen_hour_count();
    $headline = lumen_headline();
    $probes = lumen_probes();
    $cards = '';
    foreach ($probes as $probe) {
        $latency = (int) $probe->latency_ms;
        $lanes = '';
        for ($hour = 0; $hour < $hours; $hour++) {
            $sample = $latency + (($hour * 13 + strlen((string) $probe->service_name)) % 37);
            $lanes .= '<div class="lane" data-hour="' . $hour . '" data-component="HourLane">'
                . '<span class="tick">' . sprintf('%02d', $hour) . '</span>'
                . '<i class="bar" style="--v:' . $sample . '"></i>'
                . '<span class="ms">' . $sample . ' ms</span>'
                . '<small>' . esc_html($probe->status_label) . '</small></div>';
        }
        $selected = $probe->region_code === $region ? ' is-selected' : '';
        $cards .= '<article class="probe' . $selected . '" data-component="ProbeCard"'
            . ' data-service="' . esc_attr($probe->service_name) . '"'
            . ' data-region="' . esc_attr($probe->region_code) . '">'
            . '<header><h2>' . esc_html($probe->service_name) . '</h2>'
            . '<p>' . esc_html($probe->region_code) . ' · ' . esc_html($probe->status_label) . '</p></header>'
            . '<div class="lanes" data-component="LaneRow">' . $lanes . '</div></article>';
    }
    $config = wp_json_encode([
        'region' => $region,
        'hours' => $hours,
        'probeCount' => count($probes),
    ]);
    $regionOptions = '';
    foreach (lumen_regions() as $code) {
        $regionOptions .= '<option value="' . esc_attr($code) . '"'
            . ($code === $region ? ' selected' : '') . '>' . esc_html($code) . '</option>';
    }
    $body = '<div id="console-root" data-reactroot="" data-hydrate="1"'
        . ' data-region="' . esc_attr($region) . '" data-hours="' . esc_attr((string) $hours) . '">'
        . '<header class="mast" data-component="FloorHeader"><p class="mark">Lumen Floor</p>'
        . '<h1 id="floor-title">Floor status</h1></header>'
        . '<form class="filters" method="get" action="/console" data-component="FloorFilters">'
        . '<label>Headline <input name="headline" value="' . esc_attr($headline) . '"></label>'
        . '<label>Region <select name="region">' . $regionOptions . '</select></label>'
        . '<label>Hours <input name="hours" value="' . esc_attr((string) $hours) . '" inputmode="numeric"></label>'
        . '<button type="submit">Apply window</button></form>'
        . '<p class="summary" data-component="FloorSummary"><span id="region-readout"></span>'
        . ' <span id="hours-readout"></span></p>'
        . '<section class="floor" data-component="ProbeList">' . $cards . '</section></div>'
        . '<script id="lumen-config" type="application/json">' . $config . '</script>'
        . lumen_headline_script($headline)
        . '<script>' . lumen_hydrate_script() . '</script>';
    status_header(200);
    header('Content-Type: text/html; charset=utf-8');
    echo lumen_document('Lumen Floor', $body);
}

function lumen_hydrate_script(): string
{
    return <<<'JS'
(function () {
  var configNode = document.getElementById("lumen-config");
  var config = JSON.parse(configNode.textContent || "{}");
  var region = document.getElementById("region-readout");
  var hours = document.getElementById("hours-readout");
  var title = document.getElementById("floor-title");
  if (region) region.textContent = config.region || "";
  if (hours) hours.textContent = String(config.hours || "") + " h window";
  var floor = window.__LUMEN_FLOOR__ || {};
  if (title) title.textContent = floor.headline || "Floor status";
})();
JS;
}

function lumen_document(string $title, string $body): string
{
    $css = 'body{margin:0;background:#0e141b;color:#d7e2ea;font:14px/1.4 ui-monospace,Consolas,monospace}'
        . '#console-root{padding:1rem 1.2rem 2rem}.mark{letter-spacing:.18em;text-transform:uppercase;color:#3ddc97}'
        . 'h1{font:500 1.6rem/1.2 ui-sans-serif,system-ui,sans-serif;margin:.3rem 0 1rem}'
        . '.filters{display:flex;gap:.8rem;align-items:end;flex-wrap:wrap}'
        . 'label{display:flex;flex-direction:column;gap:.25rem;color:#93a4b3}'
        . 'input,select,button{font:inherit;background:#121a22;color:#d7e2ea;border:1px solid #2a3946;padding:.35rem .5rem}'
        . 'button{background:#145c40;color:#e8fff5}'
        . '.summary{color:#93a4b3}.floor{display:grid;gap:.8rem}'
        . '.probe{border:1px solid #243140;padding:.7rem;background:#121a22}'
        . '.probe.is-selected{border-color:#3ddc97}'
        . 'h2{font-size:.95rem;margin:0}.lanes{display:grid;grid-template-columns:repeat(auto-fill,minmax(7rem,1fr));gap:.35rem;margin-top:.6rem}'
        . '.lane{display:grid;grid-template-columns:1.6rem 1fr;gap:.2rem .4rem;background:#0e141b;padding:.35rem}'
        . '.bar{display:block;height:.45rem;background:#3ddc97;width:calc(var(--v) * 1%);grid-column:1 / -1}'
        . '.ms,small{color:#93a4b3}';
    return '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        . '<meta name="robots" content="noindex"><title>' . esc_html($title) . '</title>'
        . '<style>' . $css . '</style></head><body>' . $body . '</body></html>';
}
