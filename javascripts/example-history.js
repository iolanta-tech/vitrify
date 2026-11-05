function initializeExampleHistory() {
  document.querySelectorAll(".example-history").forEach((history) => {
    if (history.dataset.initialized) return;
    history.dataset.initialized = "true";
    const chart = history.querySelector(".history-chart");
    const selected = chart.querySelector('[aria-current="page"]');
    if (selected) {
      chart.scrollLeft = selected.offsetLeft - chart.clientWidth / 2 + selected.clientWidth / 2;
    }
    history.querySelectorAll("[data-history-scroll]").forEach((button) => {
      button.addEventListener("click", () => {
        chart.scrollBy({ left: Number(button.dataset.historyScroll) * chart.clientWidth * 0.8, behavior: "smooth" });
      });
    });

  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeExampleHistory);
} else {
  initializeExampleHistory();
}
