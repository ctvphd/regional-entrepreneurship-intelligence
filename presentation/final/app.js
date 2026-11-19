(() => {
  "use strict";

  const allSlides = [...document.querySelectorAll(".slide")];
  const mainSlides = allSlides.filter((slide) => !slide.classList.contains("backup"));
  const backupSlides = allSlides.filter((slide) => slide.classList.contains("backup"));
  const deck = document.getElementById("deck");
  const counter = document.getElementById("counter");
  const progressBar = document.getElementById("progressBar");
  const presenterShell = document.getElementById("presenterShell");
  const presenterMode = new URLSearchParams(location.search).get("presenter") === "1";
  const state = { group: "main", index: 0, startedAt: Date.now() };

  const slides = () => state.group === "main" ? mainSlides : backupSlides;
  const current = () => slides()[state.index];

  function revealNext() {
    const hidden = [...current().querySelectorAll("[data-reveal]:not(.revealed)")];
    if (!hidden.length) return false;
    hidden[0].classList.add("revealed");
    return true;
  }

  function resetReveals(slide) {
    slide.querySelectorAll("[data-reveal]").forEach((item) => item.classList.remove("revealed"));
  }

  function publish() {
    const payload = { group: state.group, index: state.index, timestamp: Date.now() };
    localStorage.setItem("rei-slide-state", JSON.stringify(payload));
  }

  function render({ broadcast = true } = {}) {
    allSlides.forEach((slide) => slide.classList.remove("active"));
    current().classList.add("active");
    const total = slides().length;
    counter.textContent = state.group === "main" ? `${state.index + 1} / ${total}` : `B${state.index + 1} / ${total}`;
    progressBar.style.width = `${((state.index + 1) / total) * 100}%`;
    document.title = `${current().dataset.title} · Regional Entrepreneurship Intelligence`;
    if (broadcast) publish();
    if (presenterMode) renderPresenter();
  }

  function move(delta) {
    if (delta > 0 && revealNext()) return;
    const next = Math.min(Math.max(state.index + delta, 0), slides().length - 1);
    if (next === state.index) return;
    resetReveals(current());
    state.index = next;
    render();
  }

  function goTo(index) {
    resetReveals(current());
    state.index = Math.min(Math.max(index, 0), slides().length - 1);
    render();
  }

  function toggleBackups() {
    resetReveals(current());
    state.group = state.group === "main" ? "backup" : "main";
    state.index = 0;
    render();
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
    else document.exitFullscreen?.();
  }

  function openPresenter() {
    const url = new URL(location.href);
    url.searchParams.set("presenter", "1");
    window.open(url, "rei-presenter", "popup,width=1500,height=920");
  }

  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  }

  function elapsedSeconds() {
    return Math.floor((Date.now() - state.startedAt) / 1000);
  }

  function targetSeconds() {
    const active = state.group === "main" ? mainSlides.slice(0, state.index + 1) : mainSlides;
    return active.reduce((total, slide) => total + Number(slide.dataset.time || 0), 0);
  }

  function renderPresenter() {
    const active = current();
    const nextSlide = slides()[Math.min(state.index + 1, slides().length - 1)];
    const notes = active.querySelector(".full-notes")?.textContent || "No notes for this backup slide.";
    const cues = [...active.querySelectorAll(".cues li")].map((item) => `<li>${item.textContent}</li>`).join("");
    presenterShell.innerHTML = `
      <div class="presenter-clock"><strong>Elapsed <span id="elapsed">${formatTime(elapsedSeconds())}</span></strong><strong>Target ${formatTime(targetSeconds())}</strong><strong>${state.group === "main" ? state.index + 1 : `B${state.index + 1}`} / ${slides().length}</strong></div>
      <div class="presenter-grid">
        <div>
          <div class="presenter-preview" id="currentPreview"></div>
          <div class="presenter-next"><h3>Next</h3><div class="presenter-preview" id="nextPreview"></div></div>
        </div>
        <article class="presenter-notes"><h2>${active.dataset.title}</h2><p>${notes}</p><h3>Concise cues</h3><ul>${cues || "<li>Use only if requested during Q&A.</li>"}</ul></article>
      </div>
      <nav class="controls" aria-label="Presenter controls"><button data-action="prev" aria-label="Previous slide">←</button><button data-action="next" aria-label="Next slide">→</button><button data-action="backup" aria-label="Toggle backup slides">B</button><button data-action="reset" aria-label="Reset timer">Reset</button></nav>`;
    const currentClone = active.cloneNode(true);
    const nextClone = nextSlide.cloneNode(true);
    currentClone.classList.add("active");
    nextClone.classList.add("active");
    presenterShell.querySelector("#currentPreview").append(currentClone);
    presenterShell.querySelector("#nextPreview").append(nextClone);
    presenterShell.querySelector("[data-action='prev']").onclick = () => move(-1);
    presenterShell.querySelector("[data-action='next']").onclick = () => move(1);
    presenterShell.querySelector("[data-action='backup']").onclick = toggleBackups;
    presenterShell.querySelector("[data-action='reset']").onclick = () => { state.startedAt = Date.now(); renderPresenter(); };
  }

  document.getElementById("prev").addEventListener("click", () => move(-1));
  document.getElementById("next").addEventListener("click", () => move(1));
  document.getElementById("backupToggle").addEventListener("click", toggleBackups);
  document.getElementById("presenter").addEventListener("click", openPresenter);
  document.getElementById("fullscreen").addEventListener("click", toggleFullscreen);

  document.addEventListener("keydown", (event) => {
    if (["ArrowRight", "PageDown", " "].includes(event.key)) { event.preventDefault(); move(1); }
    if (["ArrowLeft", "PageUp"].includes(event.key)) { event.preventDefault(); move(-1); }
    if (event.key === "Home") { event.preventDefault(); goTo(0); }
    if (event.key === "End") { event.preventDefault(); goTo(slides().length - 1); }
    if (event.key.toLowerCase() === "b") toggleBackups();
    if (event.key.toLowerCase() === "f") toggleFullscreen();
    if (event.key.toLowerCase() === "p" && !presenterMode) openPresenter();
    if (event.key === "Escape" && state.group === "backup") toggleBackups();
  });

  deck.addEventListener("click", (event) => {
    if (event.target.closest("a, button")) return;
    const direction = event.clientX < window.innerWidth / 2 ? -1 : 1;
    move(direction);
  });

  window.addEventListener("storage", (event) => {
    if (event.key !== "rei-slide-state" || !event.newValue) return;
    const incoming = JSON.parse(event.newValue);
    state.group = incoming.group === "backup" ? "backup" : "main";
    state.index = Math.min(Math.max(incoming.index || 0, 0), slides().length - 1);
    render({ broadcast: false });
  });

  if (presenterMode) {
    deck.hidden = true;
    document.querySelector("body > .controls").hidden = true;
    document.querySelector("body > .progress").hidden = true;
    presenterShell.hidden = false;
    setInterval(() => {
      const elapsed = document.getElementById("elapsed");
      if (elapsed) elapsed.textContent = formatTime(elapsedSeconds());
    }, 1000);
  }

  render({ broadcast: !presenterMode });
})();
