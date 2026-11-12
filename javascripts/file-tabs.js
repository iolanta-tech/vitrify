function activateFileTabFromHash() {
  let id;
  try {
    id = decodeURIComponent(window.location.hash.slice(1));
  } catch {
    return;
  }
  const anchor = document.getElementById(id);
  const input = anchor?.dataset.tabTarget
    ? document.getElementById(anchor.dataset.tabTarget)
    : null;
  if (!(input instanceof HTMLInputElement) || input.type !== "radio") return;

  const tabSet = input.closest(".tabbed-set");
  if (!tabSet) return;

  if (!input.checked) input.click();
  const label = Array.from(tabSet.querySelectorAll("label")).find(
    (candidate) => candidate.htmlFor === input.id,
  );
  (label || tabSet).scrollIntoView({ block: "start" });
}

function formatFileTabLabels() {
  document.querySelectorAll(".tabbed-labels label a").forEach((link) => {
    if (link.querySelector("code")) return;

    const code = document.createElement("code");
    code.textContent = link.textContent;
    link.replaceChildren(code);
  });
}

function observeFileTabLabels() {
  formatFileTabLabels();
  new MutationObserver(formatFileTabLabels).observe(document.body, {
    childList: true,
    subtree: true,
  });
}

if (document.body) {
  observeFileTabLabels();
} else {
  window.addEventListener("DOMContentLoaded", observeFileTabLabels);
}

window.addEventListener("DOMContentLoaded", activateFileTabFromHash);
window.addEventListener("hashchange", activateFileTabFromHash);
