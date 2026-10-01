<?php
/**
 * Plugin Name: Ashford Registry
 * Description: Membership roll for the Ashford chapters.
 */

add_filter('redirect_canonical', static function ($redirect) {
    $path = ashford_request_path();
    if ($path === '' || $path === 'directory') {
        return false;
    }
    return $redirect;
});

add_action('template_redirect', static function () {
    if (!function_exists('is_blog_installed') || !is_blog_installed()) {
        return;
    }
    $path = ashford_request_path();
    if ($path === '') {
        ashford_render_home();
        exit;
    }
    if ($path === 'directory') {
        if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
            ashford_handle_post();
        }
        ashford_render_directory();
        exit;
    }
}, 0);

function ashford_request_path(): string
{
    $uri = isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/';
    $path = parse_url($uri, PHP_URL_PATH);
    return is_string($path) ? trim($path, '/') : '';
}

function ashford_handle_post(): void
{
    if (isset($_POST['portrait_url'])) {
        ashford_apply_portrait();
        return;
    }
    if (isset($_POST['enrollment'])) {
        ashford_apply_enrollment();
    }
}

function ashford_apply_enrollment(): void
{
    if (!is_string($_POST['enrollment'] ?? null)) {
        return;
    }
    $enrollment = sanitize_text_field(wp_unslash($_POST['enrollment']));
    update_option('ashford_enrollment', $enrollment, false);
}

function ashford_apply_portrait(): void
{
    if (!is_string($_POST['portrait_url'] ?? null)) {
        return;
    }
    $nonce = is_string($_POST['_ashford_nonce'] ?? null) ? $_POST['_ashford_nonce'] : '';
    if (!wp_verify_nonce($nonce, 'ashford_portrait')) {
        return;
    }
    $url = esc_url_raw(wp_unslash($_POST['portrait_url']));
    if ($url === '') {
        return;
    }
    update_option('ashford_featured_portrait', $url, false);
}

function ashford_members(): array
{
    global $wpdb;
    $rows = $wpdb->get_results(
        "SELECT id, full_name, chapter, role_title, standing_label, biography
         FROM ar_members ORDER BY chapter, full_name"
    );
    return is_array($rows) ? $rows : [];
}

function ashford_crest(string $letter): string
{
    $safe = esc_html(strtoupper(substr($letter, 0, 1)));
    return '<svg class="crest" viewBox="0 0 64 64" aria-hidden="true">'
        . '<circle cx="32" cy="32" r="28" fill="none" stroke="#b08d3e" stroke-width="2"></circle>'
        . '<path fill="#123027" d="M32 10l4.8 12.2H50l-10.4 8 4 12.4L32 35.2 20.4 42.6l4-12.4L14 22.2h13.2z"></path>'
        . '<text x="32" y="30" text-anchor="middle" font-size="11" fill="#f3f6f2">' . $safe . '</text>'
        . '</svg>';
}

function ashford_render_home(): void
{
    status_header(200);
    header('Content-Type: text/html; charset=utf-8');
    $body = '<header class="mast"><p class="mark">Ashford Registry</p><h1>Chapter roll</h1></header>'
        . '<main><p>The conservation society keeps one roll for the harbor, estuary, ridge, and basin chapters.</p>'
        . '<p><a href="/directory">Open the directory</a></p></main>';
    echo ashford_document('Ashford Registry', $body);
}

function ashford_render_directory(): void
{
    $notice = (isset($_GET['notice']) && is_string($_GET['notice'])) ? wp_unslash($_GET['notice']) : '';
    $enrollment = (string) get_option('ashford_enrollment', 'open');
    $portrait = (string) get_option('ashford_featured_portrait', '');
    $cards = '';
    foreach (ashford_members() as $member) {
        $letter = substr((string) $member->full_name, 0, 1);
        $cards .= '<article class="wp-block-column member-card">'
            . '<figure class="wp-block-image">' . ashford_crest($letter) . '</figure>'
            . '<h2>' . esc_html($member->full_name) . '</h2>'
            . '<p class="meta">' . esc_html($member->chapter) . ' · ' . esc_html($member->role_title) . '</p>'
            . '<p class="standing">' . esc_html($member->standing_label) . '</p>'
            . '<p>' . esc_html($member->biography) . '</p>'
            . '<button type="button" data-open-member="1"'
            . ' data-name="' . esc_attr($member->full_name) . '"'
            . ' data-role="' . esc_attr($member->role_title) . '"'
            . ' data-bio="' . esc_attr($member->biography) . '">Chapter sheet</button>'
            . '</article>';
    }
    $banner = $notice !== '' ? '<div class="bulletin">' . $notice . '</div>' : '';
    $portraitBlock = $portrait !== ''
        ? '<img class="portrait" alt="Featured chapter portrait" src="' . esc_url($portrait) . '">'
        : '<p class="portrait-empty">No featured portrait has been filed.</p>';
    $nonce = wp_nonce_field('ashford_portrait', '_ashford_nonce', true, false);
    $body = '<header class="mast"><p class="mark">Ashford Registry</p><h1>Membership directory</h1></header>'
        . '<main>' . $banner
        . '<div class="wp-block-group directory-band"><div class="wp-block-group__inner-container">'
        . '<p>Enrollment desk: <strong>' . esc_html($enrollment) . '</strong></p>'
        . $portraitBlock
        . '<div class="desk-forms">'
        . '<form method="post" action="/directory"><label>Enrollment desk'
        . '<input name="enrollment" maxlength="40" value="' . esc_attr($enrollment) . '"></label>'
        . '<button type="submit">Update desk</button></form>'
        . '<form method="get" action="/directory"><label>Bulletin'
        . '<input name="notice" value="' . esc_attr($notice) . '"></label>'
        . '<button type="submit">Print bulletin</button></form>'
        . '<form method="post" action="/directory"><label>Featured portrait URL'
        . '<input name="portrait_url" type="url" placeholder="https://example.local/portrait.jpg"></label>'
        . $nonce . '<button type="submit">File portrait</button></form>'
        . '</div></div></div>'
        . '<section class="wp-block-group season-panel"><div class="wp-block-group__inner-container">'
        . '<h2>Season hours</h2>'
        . '<p>The harbor chapter meets on the first Thursday, the estuary chapter on the second, the ridge chapter on the third, and the basin chapter on the last Thursday of the month. Bring the work diary if the desk has asked for a correction.</p>'
        . '<p>Skiffs for the eelgrass count leave the inner berth at dawn. The chart room stays open for an hour after the meeting so new members can check the portrait card and the printed roll.</p>'
        . '<p>Dues for the current season are recorded by the basin treasurer. A member on leave remains on this directory until the clerk moves the standing at the next assembly.</p>'
        . '</div></section>'
        . '<div class="wp-block-group"><div class="wp-block-columns member-grid">' . $cards . '</div></div>'
        . '<dialog id="member-sheet"><form method="dialog"><button>Close</button></form>'
        . '<div id="member-sheet-body"></div></dialog>'
        . '<template id="member-template"><article><h3 data-slot="name"></h3>'
        . '<p data-slot="role"></p><p data-slot="bio"></p></article></template>'
        . '<script>' . ashford_sheet_script() . '</script>'
        . '</main>';
    status_header(200);
    header('Content-Type: text/html; charset=utf-8');
    echo ashford_document('Ashford directory', $body);
}

function ashford_sheet_script(): string
{
    return <<<'JS'
document.querySelectorAll("[data-open-member]").forEach(function (button) {
  button.addEventListener("click", function () {
    var sheet = document.getElementById("member-sheet");
    var body = document.getElementById("member-sheet-body");
    var node = document.getElementById("member-template").content.cloneNode(true);
    body.replaceChildren();
    node.querySelector('[data-slot="name"]').textContent = button.getAttribute("data-name") || "";
    node.querySelector('[data-slot="role"]').textContent = button.getAttribute("data-role") || "";
    node.querySelector('[data-slot="bio"]').textContent = button.getAttribute("data-bio") || "";
    body.appendChild(node);
    sheet.showModal();
  });
});
JS;
}

function ashford_document(string $title, string $body): string
{
    $css = 'body{margin:0;background:#f3f6f2;color:#14241c;font:17px/1.5 Georgia,serif}'
        . 'main,header{max-width:68rem;margin:0 auto;padding:1.4rem}'
        . '.mark{letter-spacing:.18em;text-transform:uppercase;font-size:.72rem;color:#123027}'
        . 'h1{font-weight:500;margin:.2rem 0 1rem}.bulletin{background:#123027;color:#f3f6f2;padding:.8rem 1rem}'
        . '.directory-band{background:#fff;border:1px solid #d5ddd4;padding:1rem;margin-bottom:1rem}'
        . '.desk-forms{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}'
        . 'label{display:flex;flex-direction:column;font-size:.85rem;gap:.3rem}'
        . 'input,button{font:inherit}input{border:1px solid #123027;padding:.4rem}'
        . 'button{background:#123027;color:#f3f6f2;border:0;padding:.45rem .7rem;margin-top:.45rem}'
        . '.member-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}'
        . '.member-card{background:#fff;border-top:3px solid #b08d3e;padding:1rem}'
        . '.crest{width:4rem;height:4rem}.meta,.standing{color:#3d5348;font-size:.92rem}'
        . '.portrait{max-width:12rem;display:block;margin:.5rem 0}'
        . 'dialog{border:1px solid #123027;max-width:32rem;padding:1.2rem}'
        . '@media(max-width:800px){.desk-forms,.member-grid{grid-template-columns:1fr}}';
    return '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        . '<meta name="robots" content="noindex"><title>' . esc_html($title) . '</title>'
        . '<style>' . $css . '</style></head><body>' . $body . '</body></html>';
}
