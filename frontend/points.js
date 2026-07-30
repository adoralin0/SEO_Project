const STORAGE_KEY = "loyableRewardsPoints"; // tracked restaurants (legacy map)
const REWARDS_KEY = "loyableClaimedRewards";
const TOTAL_KEY = "loyableTotalPoints";

function getCurrentUserEmail() {
  try {
    return localStorage.getItem("email") || "";
  } catch {
    return "";
  }
}

function getScopedKey(baseKey) {
  const email = getCurrentUserEmail();
  return email ? `${baseKey}:${email}` : baseKey;
}

function readPointsMap() {
  try {
    return JSON.parse(localStorage.getItem(getScopedKey(STORAGE_KEY)) || "{}");
  } catch {
    return {};
  }
}

function writePointsMap(pointsMap) {
  localStorage.setItem(getScopedKey(STORAGE_KEY), JSON.stringify(pointsMap));
}

/** Shared account balance — spendable at any restaurant */
function readTotalPoints() {
  const key = getScopedKey(TOTAL_KEY);
  const raw = localStorage.getItem(key);
  if (raw !== null && raw !== "") {
    return Math.max(0, Math.floor(Number(raw)) || 0);
  }
  // One-time migrate: old per-restaurant balances → one pool
  const map = readPointsMap();
  const sum = Object.values(map).reduce(
    (s, p) => s + (Math.floor(Number(p)) || 0),
    0
  );
  writeTotalPoints(sum);
  const tracked = {};
  Object.keys(map).forEach((name) => {
    tracked[name] = 0;
  });
  writePointsMap(tracked);
  return sum;
}

function writeTotalPoints(n) {
  const value = Math.max(0, Math.floor(Number(n)) || 0);
  localStorage.setItem(getScopedKey(TOTAL_KEY), String(value));
}

function addTotalPoints(delta) {
  const next = readTotalPoints() + (Math.floor(Number(delta)) || 0);
  writeTotalPoints(next);
  return readTotalPoints();
}

function spendTotalPoints(amount) {
  const need = Math.max(0, Math.floor(Number(amount)) || 0);
  const current = readTotalPoints();
  if (current < need) return false;
  writeTotalPoints(current - need);
  return true;
}

function readRewardsMap() {
  try {
    return JSON.parse(localStorage.getItem(getScopedKey(REWARDS_KEY)) || "{}");
  } catch {
    return {};
  }
}

function writeRewardsMap(rewardsMap) {
  localStorage.setItem(getScopedKey(REWARDS_KEY), JSON.stringify(rewardsMap));
}

function getDisplayName() {
  const email = getCurrentUserEmail();
  if (!email) return "Guest";
  const local = email.split("@")[0] || "Guest";
  return local.replace(/[._]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function readNavState() {
  try {
    return JSON.parse(sessionStorage.getItem("loyableNavState") || "{}");
  } catch {
    return {};
  }
}

function writeNavState(partial) {
  const next = { ...readNavState(), ...partial };
  sessionStorage.setItem("loyableNavState", JSON.stringify(next));
  return next;
}
