const names = [
  "archive-room",
  "wing-block",
  "bay-row",
  "shelf-rail",
  "gathering-set",
  "folio-card",
];

names.forEach((name) => {
  if (!customElements.get(name)) {
    customElements.define(name, class extends HTMLElement {});
  }
});

document.querySelectorAll("folio-card").forEach((card) => {
  const leaf = card.getAttribute("data-leaf");
  if (card.hasAttribute("data-current") && leaf) {
    card.setAttribute("title", "Open at leaf " + leaf);
  }
});
