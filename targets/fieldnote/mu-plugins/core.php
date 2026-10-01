<?php
/**
 * Plugin Name: Fieldnote Catalog
 * Description: Seasonal catalog for the Fieldnote press list.
 */

add_filter('redirect_canonical', static function ($redirect) {
    $path = fieldnote_request_path();
    if ($path === '' || $path === 'catalog') {
        return false;
    }
    return $redirect;
});

add_action('template_redirect', static function () {
    if (!function_exists('is_blog_installed') || !is_blog_installed()) {
        return;
    }
    $path = fieldnote_request_path();
    if ($path === '') {
        fieldnote_render_home();
        exit;
    }
    if ($path === 'catalog') {
        fieldnote_render_catalog();
        exit;
    }
}, 0);

function fieldnote_request_path(): string
{
    $uri = isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/';
    $path = parse_url($uri, PHP_URL_PATH);
    if (!is_string($path)) {
        return '';
    }
    return trim($path, '/');
}

function fieldnote_page_offset(): int
{
    $raw = (isset($_GET['page']) && is_string($_GET['page'])) ? wp_unslash($_GET['page']) : '1';
    if (!preg_match('/\A[0-9]{1,4}\z/', $raw)) {
        return 0;
    }
    $page = (int) $raw;
    if ($page < 1) {
        $page = 1;
    }
    if ($page > 40) {
        $page = 40;
    }
    return ($page - 1) * 8;
}

function fieldnote_catalog_rows(): array
{
    global $wpdb;
    $term = (isset($_GET['q']) && is_string($_GET['q'])) ? wp_unslash($_GET['q']) : '';
    $offset = fieldnote_page_offset();
    $sql = "SELECT id, title, author_name, imprint_year, shelf_code
            FROM fn_titles
            WHERE title LIKE '%{$term}%'
               OR author_name LIKE '%{$term}%'
            ORDER BY imprint_year DESC
            LIMIT 8 OFFSET {$offset}";
    $rows = $wpdb->get_results($sql);
    return is_array($rows) ? $rows : [];
}

function fieldnote_render_home(): void
{
    status_header(200);
    header('Content-Type: text/html; charset=utf-8');
    echo fieldnote_document(
        'Fieldnote',
        '<header class="mast"><p class="mark">Fieldnote</p><h1>Press list</h1></header>'
        . '<main><p>The seasonal catalog is open for the current imprint year.</p>'
        . '<p><a href="/catalog">Open the catalog</a></p></main>'
    );
}

function fieldnote_render_catalog(): void
{
    $term = (isset($_GET['q']) && is_string($_GET['q'])) ? wp_unslash($_GET['q']) : '';
    $page = (isset($_GET['page']) && is_string($_GET['page'])) ? wp_unslash($_GET['page']) : '1';
    $rows = fieldnote_catalog_rows();
    $items = '';
    foreach ($rows as $row) {
        $items .= '<li><span class="title">' . esc_html($row->title) . '</span> '
            . '<span class="author">' . esc_html($row->author_name) . '</span> '
            . '<span class="year">' . esc_html((string) $row->imprint_year) . '</span> '
            . '<span class="shelf">' . esc_html($row->shelf_code) . '</span></li>';
    }
    if ($items === '') {
        $items = '<li class="empty">No titles match this shelf search.</li>';
    }
    $body = '<header class="mast"><p class="mark">Fieldnote</p><h1>Season catalog</h1></header>'
        . '<main><form method="get" action="/catalog">'
        . '<label>Title or author <input name="q" value="' . esc_attr($term) . '"></label>'
        . '<label>Page <input name="page" value="' . esc_attr($page) . '" inputmode="numeric"></label>'
        . '<button type="submit">Look up</button></form><ul class="list">' . $items . '</ul></main>';
    status_header(200);
    header('Content-Type: text/html; charset=utf-8');
    echo fieldnote_document('Fieldnote catalog', $body);
}

function fieldnote_document(string $title, string $body): string
{
    $css = 'body{margin:0;background:#f4efe6;color:#1f2a24;font:18px/1.45 Palatino,Georgia,serif}'
        . 'main,header{max-width:38rem;margin:0 auto;padding:1.5rem 1.2rem}'
        . '.mark{letter-spacing:.16em;text-transform:uppercase;font-size:.72rem}'
        . 'h1{font-weight:500;font-size:2rem;margin:.2rem 0 0}'
        . 'form{display:flex;gap:.8rem;align-items:end;margin:1rem 0}'
        . 'label{display:flex;flex-direction:column;font-size:.85rem;gap:.25rem}'
        . 'input,button{font:inherit}input{border:1px solid #1f2a24;background:#fff;padding:.35rem .5rem}'
        . 'button{background:#8c3a2f;color:#fff;border:0;padding:.45rem .8rem}'
        . 'ul{list-style:none;padding:0;margin:0}li{padding:.55rem 0;border-top:1px solid #d9d0c2}'
        . '.title{display:block}.author,.year,.shelf{color:#4d463d;font-size:.92rem;margin-right:.6rem}';
    return '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        . '<meta name="robots" content="noindex"><title>' . esc_html($title) . '</title>'
        . '<style>' . $css . '</style></head><body>' . $body . '</body></html>';
}
