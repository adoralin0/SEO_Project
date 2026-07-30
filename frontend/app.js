const API = "/api";

function isLoggedIn() {
  return Boolean(localStorage.getItem("accessToken"));
}

function currentPage() {
  const file = location.pathname.split("/").pop();
  // "/" is served as the login page
  return file || "login.html";
}

function setupBottomNav() {
  const nav = document.querySelector(".bottom-nav");
  if (!nav) return;

  const page = currentPage();
  const frame = document.querySelector(".phone-frame");

  if (!isLoggedIn()) {
    nav.innerHTML = "";
    if (frame) frame.classList.remove("has-nav");
    return;
  }

  if (frame) frame.classList.add("has-nav");

  const links = [
    { href: "index.html", label: "Home", match: ["index.html"] },
    { href: "explore.html", label: "Explore", match: ["explore.html", "menu.html", "get-points.html", "reward-qr.html"] },
    { href: "profile.html", label: "Me", match: ["profile.html", "dashboard.html"] },
  ];

  nav.innerHTML = links
    .map(
      (link) =>
        `<a href="${link.href}" class="${link.match.includes(page) ? "active" : ""}">${link.label}</a>`
    )
    .join("");
}

function requireAuth() {
  const page = currentPage();
  if (page === "login.html") return;
  if (!isLoggedIn()) {
    location.replace("login.html");
  }
}

requireAuth();
setupBottomNav();
