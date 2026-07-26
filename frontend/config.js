window.CLOUDHELM_CONFIG = {
  API_BASE_URL: "https://cloudhelm-platform-c7nv.onrender.com",
  FRONTEND_HOME_URL: "https://joao19921.github.io/CloudHelm/",
  FRONTEND_BACKOFFICE_URL: "https://joao19921.github.io/CloudHelm/backoffice.html",
};

(() => {
  const href = "./styles.css";
  if (document.querySelector(`link[href="${href}"]`)) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = href;
  document.head.appendChild(link);
})();
