(() => {
  const navButtons = document.querySelectorAll(".nav-item");
  const views = document.querySelectorAll(".view");
  const crumb = document.getElementById("crumb-current");
  const envButtons = document.querySelectorAll(".env-btn");
  const body = document.body;

  const labels = {
    overview: "Architecture overview",
    setup: "Setup steps",
    guardrails: "Guardrails & limits",
    cicd: "CI/CD & tuning",
  };

  function activate(target) {
    navButtons.forEach((b) =>
      b.classList.toggle("active", b.dataset.target === target),
    );
    views.forEach((v) => v.classList.toggle("active", v.id === target));
    if (crumb && labels[target]) crumb.textContent = labels[target];
    if (location.hash.slice(1) !== target) {
      history.replaceState(null, "", `#${target}`);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => activate(btn.dataset.target));
  });

  function setEnv(env) {
    envButtons.forEach((b) => b.classList.toggle("active", b.dataset.env === env));
    body.classList.remove("env-dev", "env-prod");
    body.classList.add(`env-${env}`);
  }

  envButtons.forEach((b) => b.addEventListener("click", () => setEnv(b.dataset.env)));

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    const order = ["overview", "setup", "guardrails", "cicd"];
    const current =
      document.querySelector(".view.active")?.id || "overview";
    const idx = order.indexOf(current);
    if (e.key === "ArrowDown" || e.key === "j") {
      activate(order[Math.min(order.length - 1, idx + 1)]);
    } else if (e.key === "ArrowUp" || e.key === "k") {
      activate(order[Math.max(0, idx - 1)]);
    } else if (["1", "2", "3", "4"].includes(e.key)) {
      activate(order[parseInt(e.key, 10) - 1]);
    }
  });

  const initial = location.hash.slice(1);
  activate(labels[initial] ? initial : "overview");
  setEnv("dev");
})();
