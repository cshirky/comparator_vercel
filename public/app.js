const MAX_SLOTS = 5;
const MIN_SLOTS = 2;

const slotsEl = document.getElementById("school-slots");
const addBtn = document.getElementById("add-slot");
const compareBtn = document.getElementById("compare-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

// { slotId -> { unitid, name } }
const selected = {};
let slotCount = 0;

function createSlot() {
  if (slotCount >= MAX_SLOTS) return;
  const id = ++slotCount;
  const wrap = document.createElement("div");
  wrap.className = "slot";
  wrap.dataset.slot = id;
  wrap.innerHTML = `
    <div class="slot-wrap">
      <input type="text" placeholder="Search for a school…" autocomplete="off" data-slot="${id}" />
      <div class="dropdown" id="dd-${id}" style="display:none"></div>
    </div>`;
  slotsEl.appendChild(wrap);

  const input = wrap.querySelector("input");
  const dd = wrap.querySelector(".dropdown");
  let debounce;

  input.addEventListener("input", () => {
    const q = input.value.trim();
    clearTimeout(debounce);
    if (selected[id]) { delete selected[id]; updateCompareBtn(); }
    if (q.length < 2) { dd.style.display = "none"; return; }
    debounce = setTimeout(() => search(q, id, input, dd), 300);
  });

  input.addEventListener("blur", () => setTimeout(() => dd.style.display = "none", 150));

  if (slotCount >= MAX_SLOTS) addBtn.style.display = "none";
  updateCompareBtn();
}

async function search(q, slotId, input, dd) {
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const items = await res.json();
    if (!Array.isArray(items) || items.length === 0) { dd.style.display = "none"; return; }
    dd.innerHTML = items.map(s =>
      `<div class="dropdown-item" data-unitid="${s.unitid}" data-name="${s.name}">
        ${s.name}
        <div class="sub">${s.city}, ${s.state}</div>
      </div>`
    ).join("");
    dd.style.display = "block";
    dd.querySelectorAll(".dropdown-item").forEach(item => {
      item.addEventListener("mousedown", () => {
        selected[slotId] = { unitid: item.dataset.unitid, name: item.dataset.name };
        input.value = item.dataset.name;
        dd.style.display = "none";
        updateCompareBtn();
      });
    });
  } catch {
    dd.style.display = "none";
  }
}

function updateCompareBtn() {
  const count = Object.keys(selected).length;
  compareBtn.disabled = count < MIN_SLOTS;
  compareBtn.textContent = count >= MIN_SLOTS ? `Compare ${count} schools` : "Compare";
}

addBtn.addEventListener("click", createSlot);

compareBtn.addEventListener("click", async () => {
  const unitids = Object.values(selected).map(s => s.unitid);
  statusEl.textContent = "Fetching data…";
  compareBtn.disabled = true;
  resultsEl.innerHTML = "";

  try {
    const res = await fetch(`/api/compare?unitids=${unitids.join(",")}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    render(data);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    compareBtn.disabled = Object.keys(selected).length < MIN_SLOTS;
  }
});

function badgeClass(sim) {
  return "badge badge-" + sim.replace(/ /g, "_");
}

function fmt(v) {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString();
  return v;
}

function render(data) {
  resultsEl.innerHTML = data.pairs.map(pair => `
    <div class="pair-section">
      <h2>${pair.school_a.name} vs. ${pair.school_b.name}</h2>
      <table>
        <thead>
          <tr>
            <th>Characteristic</th>
            <th>${pair.school_a.name}</th>
            <th>${pair.school_b.name}</th>
            <th>Similarity</th>
          </tr>
        </thead>
        <tbody>
          ${pair.comparisons.map(c => `
            <tr>
              <td>${c.label}</td>
              <td>${fmt(c.a)}</td>
              <td>${fmt(c.b)}</td>
              <td><span class="${badgeClass(c.similarity)}">${c.similarity}</span></td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`).join("");
}

// Start with 2 slots
createSlot();
createSlot();
