"""
PetDigiTwin — Full single-page web UI (served by Flask).
All five use-case panels in one HTML template; no separate container required.
"""

MAIN_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PetDigiTwin — Your Pet's Digital Twin</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --brand:   #2563eb;
      --brand2:  #7c3aed;
      --bg:      #f0f4ff;
      --card:    #ffffff;
      --border:  #e2e8f0;
      --text:    #1e293b;
      --muted:   #64748b;
      --green:   #16a34a;
      --amber:   #d97706;
      --red:     #dc2626;
      --radius:  12px;
    }

    body { font-family: "Segoe UI", Arial, sans-serif; background: var(--bg); color: var(--text); }

    /* ── Header ─────────────────────────────────────────────────────────── */
    header {
      background: linear-gradient(135deg, var(--brand) 0%, var(--brand2) 100%);
      color: #fff; padding: 18px 28px;
      display: flex; align-items: center; gap: 14px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    header .logo { font-size: 32px; }
    header h1 { font-size: 22px; font-weight: 700; }
    header p  { font-size: 13px; opacity: .85; }

    /* ── Layout ─────────────────────────────────────────────────────────── */
    .layout { display: flex; min-height: calc(100vh - 72px); }

    /* ── Sidebar ─────────────────────────────────────────────────────────── */
    .sidebar {
      width: 210px; flex-shrink: 0;
      background: var(--card); border-right: 1px solid var(--border);
      padding: 20px 0;
    }
    .sidebar h3 { font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
      color: var(--muted); padding: 0 18px 8px; }
    .pet-item {
      padding: 9px 18px; cursor: pointer; border-left: 3px solid transparent;
      font-size: 14px; display: flex; align-items: center; gap: 8px;
      transition: background .15s;
    }
    .pet-item:hover  { background: #f1f5ff; }
    .pet-item.active { background: #eff6ff; border-left-color: var(--brand); font-weight: 600; }
    .pet-icon { font-size: 20px; }

    /* ── Main ─────────────────────────────────────────────────────────── */
    main { flex: 1; padding: 24px; overflow-y: auto; }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 20px; }
    .tab-btn {
      padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border);
      background: var(--card); cursor: pointer; font-size: 13px; font-weight: 600;
      color: var(--muted); transition: all .15s;
    }
    .tab-btn:hover  { background: #eff6ff; color: var(--brand); }
    .tab-btn.active { background: var(--brand); color: #fff; border-color: var(--brand); }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    /* ── Cards ─────────────────────────────────────────────────────────── */
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 18px; margin-bottom: 18px;
    }
    .card h2 { font-size: 16px; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
    .card h2 .icon { font-size: 20px; }

    /* ── Pet banner ─────────────────────────────────────────────────────── */
    .pet-banner {
      background: linear-gradient(135deg,#eff6ff,#f5f3ff);
      border: 1px solid var(--border); border-radius: var(--radius);
      padding: 16px 20px; margin-bottom: 20px;
      display: flex; align-items: center; gap: 18px;
    }
    .pet-banner .big-icon { font-size: 48px; }
    .pet-banner .name { font-size: 22px; font-weight: 700; }
    .pet-banner .meta { font-size: 13px; color: var(--muted); }
    .badge {
      display: inline-block; padding: 2px 10px; border-radius: 20px;
      font-size: 11px; font-weight: 700; margin-right: 4px; margin-top: 4px;
    }
    .badge-blue   { background:#dbeafe; color:#1d4ed8; }
    .badge-red    { background:#fee2e2; color:#b91c1c; }
    .badge-amber  { background:#fef3c7; color:#92400e; }
    .badge-green  { background:#dcfce7; color:#15803d; }
    .badge-purple { background:#ede9fe; color:#6d28d9; }

    /* ── Stat grid ─────────────────────────────────────────────────────── */
    .stat-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(140px,1fr)); gap: 12px; }
    .stat-card {
      background: var(--bg); border-radius: 8px; padding: 12px 14px;
      text-align: center;
    }
    .stat-card .val { font-size: 24px; font-weight: 700; }
    .stat-card .lbl { font-size: 11px; color: var(--muted); margin-top: 2px; }

    /* ── Agent chat ─────────────────────────────────────────────────────── */
    .agent-box { display: flex; flex-direction: column; gap: 10px; }
    .agent-row { display: flex; gap: 8px; align-items: flex-start; }
    textarea {
      width: 100%; padding: 10px 12px; border: 1px solid var(--border);
      border-radius: 8px; font-size: 14px; resize: vertical; min-height: 70px;
    }
    button {
      padding: 9px 18px; background: var(--brand); color: #fff; border: none;
      border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
      transition: opacity .15s; white-space: nowrap;
    }
    button:disabled { opacity: .5; cursor: not-allowed; }
    button.secondary {
      background: var(--card); color: var(--brand); border: 1px solid var(--brand);
    }
    .response-box {
      background: #0b1020; color: #d1e7ff; border-radius: 8px;
      padding: 14px; font-size: 14px; line-height: 1.65;
      white-space: pre-wrap; overflow-wrap: anywhere; min-height: 60px;
    }
    .spinner { display: inline-block; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* ── Food cards ─────────────────────────────────────────────────────── */
    .food-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap: 14px; }
    .food-card {
      background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
      padding: 14px;
    }
    .food-card h4 { font-size: 14px; margin-bottom: 6px; }
    .food-card .price { font-size: 20px; font-weight: 700; color: var(--brand); }
    .food-card .safe { color: var(--green); font-size: 12px; font-weight: 700; }
    .food-card .warn { color: var(--red);   font-size: 12px; font-weight: 700; }

    /* ── Volunteer cards ────────────────────────────────────────────────── */
    .vol-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(240px,1fr)); gap: 14px; }
    .vol-card {
      background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
      padding: 14px; display: flex; flex-direction: column; gap: 6px;
    }
    .vol-card h4 { font-size: 15px; font-weight: 700; }
    .stars { color: #f59e0b; font-size: 14px; }

    /* ── Timeline ─────────────────────────────────────────────────────── */
    .timeline { list-style: none; padding-left: 4px; }
    .timeline li {
      position: relative; padding: 8px 0 8px 28px; font-size: 14px;
      border-left: 2px solid var(--border); margin-left: 8px;
    }
    .timeline li::before {
      content: "●"; position: absolute; left: -9px; color: var(--brand);
    }
    .timeline li:last-child { border-left: 2px solid transparent; }

    /* ── Utility ─────────────────────────────────────────────────────── */
    .row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
    .field { display: flex; flex-direction: column; gap: 4px; }
    .field label { font-size: 12px; font-weight: 600; color: var(--muted); }
    .field input, .field select {
      padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px;
      font-size: 14px; background: var(--card);
    }
    .alert {
      padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 14px;
    }
    .alert-green  { background:#dcfce7; color:#166534; border-left: 4px solid var(--green); }
    .alert-amber  { background:#fef3c7; color:#78350f; border-left: 4px solid var(--amber); }
    .alert-red    { background:#fee2e2; color:#991b1b; border-left: 4px solid var(--red);   }
    hr { border: none; border-top: 1px solid var(--border); margin: 14px 0; }
    .muted { color: var(--muted); font-size: 13px; }
    .hidden { display: none !important; }
  </style>
</head>
<body>

<!-- ── Header ──────────────────────────────────────────────────────────── -->
<header>
  <div class="logo">🐾</div>
  <div>
    <h1>PetDigiTwin</h1>
    <p>Your Pet's Digital Twin — One-stop health, nutrition, recovery &amp; care</p>
  </div>
</header>

<div class="layout">

  <!-- ── Sidebar: pet list ─────────────────────────────────────────────── -->
  <aside class="sidebar" id="sidebar">
    <h3>Your Pets</h3>
    <div id="petList"><div style="padding:16px;color:#94a3b8;font-size:13px">Loading…</div></div>
  </aside>

  <!-- ── Main area ──────────────────────────────────────────────────────── -->
  <main>
    <!-- Pet banner (updates on pet select) -->
    <div class="pet-banner" id="petBanner">
      <div class="big-icon">🐶</div>
      <div>
        <div class="name" id="bannerName">Select a pet</div>
        <div class="meta" id="bannerMeta">Choose a pet from the sidebar to get started</div>
        <div id="bannerBadges"></div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab-btn active" data-tab="health">🩺 Health Monitor</button>
      <button class="tab-btn" data-tab="nutrition">🥗 Nutrition</button>
      <button class="tab-btn" data-tab="recovery">🌿 Natural Recovery</button>
      <button class="tab-btn" data-tab="checkup">📅 Checkup Alerts</button>
      <button class="tab-btn" data-tab="volunteer">🤝 Find Pet Minder</button>
      <button class="tab-btn" data-tab="chat">💬 Ask AI</button>
    </div>

    <!-- ── Tab 1: Health Monitor ─────────────────────────────────────────── -->
    <div class="tab-panel active" id="tab-health">
      <div class="card">
        <h2><span class="icon">🩺</span> Daily Health Overview</h2>
        <div class="stat-grid" id="healthStats">
          <div class="stat-card"><div class="val" id="statAge">—</div><div class="lbl">Age (years)</div></div>
          <div class="stat-card"><div class="val" id="statWeight">—</div><div class="lbl">Weight (kg)</div></div>
          <div class="stat-card"><div class="val" id="statWeightStatus">—</div><div class="lbl">Weight Status</div></div>
          <div class="stat-card"><div class="val" id="statAgeCategory">—</div><div class="lbl">Life Stage</div></div>
          <div class="stat-card"><div class="val" id="statDaysSince">—</div><div class="lbl">Days Since Checkup</div></div>
        </div>
        <hr>
        <div id="healthAlertBox"></div>
        <div>
          <strong>Active Conditions</strong>
          <div id="healthConditions" style="margin-top:8px"></div>
        </div>
        <hr>
        <div>
          <strong>Health Notes</strong>
          <p class="muted" id="healthNotes" style="margin-top:6px">—</p>
        </div>
        <hr>
        <div>
          <strong>Food Allergies</strong>
          <div id="healthAllergies" style="margin-top:6px"></div>
        </div>
      </div>
    </div>

    <!-- ── Tab 2: Nutrition ──────────────────────────────────────────────── -->
    <div class="tab-panel" id="tab-nutrition">
      <div class="card">
        <h2><span class="icon">🥗</span> Food &amp; Nutrition Recommendations</h2>
        <div class="row" style="margin-bottom:14px">
          <div class="field">
            <label>Max Budget ($)</label>
            <input type="number" id="nutritionBudget" value="100" min="10" max="500" style="width:100px" />
          </div>
          <button onclick="loadFoodRecommendations()">Get Recommendations</button>
        </div>
        <div id="foodGrid" class="food-grid"><p class="muted">Select a pet and click Get Recommendations.</p></div>
      </div>
    </div>

    <!-- ── Tab 3: Natural Recovery ──────────────────────────────────────── -->
    <div class="tab-panel" id="tab-recovery">
      <div class="card">
        <h2><span class="icon">🌿</span> Natural Recovery &amp; Home Remedies</h2>
        <div class="row" style="margin-bottom:14px">
          <div class="field">
            <label>Search Condition</label>
            <input id="recoveryCondition" type="text" placeholder="e.g. joint_pain, skin_sensitivity" style="width:220px" />
          </div>
          <button onclick="searchRemedies()">Search</button>
          <button class="secondary" onclick="loadConditionRemedies()">Load from pet's conditions</button>
        </div>
        <div id="remedyResults"></div>
      </div>
    </div>

    <!-- ── Tab 4: Checkup Alerts ─────────────────────────────────────────── -->
    <div class="tab-panel" id="tab-checkup">
      <div class="card">
        <h2><span class="icon">📅</span> Proactive Checkup Predictions</h2>
        <div id="checkupResult"><p class="muted">Select a pet to see checkup status.</p></div>
      </div>
      <div class="card">
        <h2><span class="icon">📋</span> Veterinary Knowledge Base</h2>
        <div class="row" style="margin-bottom:14px">
          <div class="field">
            <label>Filter by condition</label>
            <input id="knowledgeFilter" type="text" placeholder="e.g. arthritis" style="width:200px"/>
          </div>
          <button onclick="loadKnowledge()">Search</button>
        </div>
        <div id="knowledgeList"></div>
      </div>
    </div>

    <!-- ── Tab 5: Volunteer / Pet Minder ────────────────────────────────── -->
    <div class="tab-panel" id="tab-volunteer">
      <div class="card">
        <h2><span class="icon">🤝</span> Find a Pet Minder for Your Vacation</h2>
        <div class="row" style="margin-bottom:14px">
          <div class="field">
            <label>Start Date</label>
            <input type="date" id="startDate" />
          </div>
          <div class="field">
            <label>End Date</label>
            <input type="date" id="endDate" />
          </div>
          <div class="field">
            <label>Max Distance (km)</label>
            <input type="number" id="maxDistance" value="50" min="5" max="500" style="width:100px" />
          </div>
          <button onclick="findVolunteers()">Find Pet Minders</button>
        </div>
        <div id="volunteerGrid" class="vol-grid"><p class="muted">Select dates and click Find Pet Minders.</p></div>
      </div>
      <div class="card">
        <h2><span class="icon">⭐</span> All Registered Pet Minders</h2>
        <div id="allVolunteers" class="vol-grid"></div>
      </div>
    </div>

    <!-- ── Tab 6: AI Chat ────────────────────────────────────────────────── -->
    <div class="tab-panel" id="tab-chat">
      <div class="card">
        <h2><span class="icon">💬</span> Ask PetDigiTwin AI</h2>
        <p class="muted" style="margin-bottom:14px">Ask anything about your pet's health, food, or care. The AI uses your pet's profile as context.</p>
        <div class="agent-box">
          <div class="row">
            <div style="flex:1">
              <textarea id="chatQuery" placeholder="e.g. Max has been limping for 2 days. What natural remedies can help?"></textarea>
            </div>
          </div>
          <div class="row">
            <button id="chatBtn" onclick="sendChatQuery()">Ask AI</button>
            <button class="secondary" onclick="setChatExample(this)" data-q="What natural remedies help joint pain?">Joint pain</button>
            <button class="secondary" onclick="setChatExample(this)" data-q="What's the best food for my pet's conditions?">Best food</button>
            <button class="secondary" onclick="setChatExample(this)" data-q="When does my pet need a checkup and why?">Checkup</button>
            <button class="secondary" onclick="setChatExample(this)" data-q="Find a volunteer pet minder for July 1-15">Pet minder</button>
          </div>
          <div class="response-box" id="chatResponse">Waiting for your question…</div>
        </div>
      </div>
      <div class="card">
        <h2><span class="icon">🗂️</span> Conversation History</h2>
        <ul class="timeline" id="chatHistory"><li class="muted">No queries yet.</li></ul>
      </div>
    </div>
  </main>
</div>

<script>
/* ── State ──────────────────────────────────────────────────────────────── */
let allPets = [];
let selectedPetId = null;
let chatHistory = [];

/* ── Init ───────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  await loadPets();
  await loadAllVolunteers();
  setDefaultDates();
  setupTabs();
});

function setDefaultDates() {
  const today = new Date();
  const plus14 = new Date(today); plus14.setDate(plus14.getDate() + 14);
  document.getElementById('startDate').value = today.toISOString().slice(0,10);
  document.getElementById('endDate').value   = plus14.toISOString().slice(0,10);
}

/* ── Tab routing ─────────────────────────────────────────────────────────── */
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });
}

/* ── Load pets ───────────────────────────────────────────────────────────── */
async function loadPets() {
  const res = await fetch('/api/pets');
  const data = await res.json();
  allPets = data.pets || [];
  renderSidebar();
  if (allPets.length) selectPet(allPets[0].id);
}

function renderSidebar() {
  const icons = { Labrador:'🦮', 'German Shepherd':'🐕', 'Golden Retriever':'🦮',
    Beagle:'🐶', Poodle:'🐩', Bulldog:'🐾', Husky:'🐺',
    Dachshund:'🌭', 'Shiba Inu':'🦊', Corgi:'🐕' };
  const container = document.getElementById('petList');
  container.innerHTML = allPets.map(p => `
    <div class="pet-item" id="pet-item-${p.id}" onclick="selectPet('${p.id}')">
      <span class="pet-icon">${icons[p.breed] || '🐾'}</span>
      <div>
        <div style="font-weight:600">${p.name}</div>
        <div style="font-size:11px;color:#94a3b8">${p.breed}</div>
      </div>
    </div>`).join('');
}

/* ── Select pet ──────────────────────────────────────────────────────────── */
async function selectPet(id) {
  selectedPetId = id;
  document.querySelectorAll('.pet-item').forEach(el => el.classList.remove('active'));
  const el = document.getElementById('pet-item-' + id);
  if (el) el.classList.add('active');

  const res = await fetch('/api/pets/' + id);
  const data = await res.json();
  const pet = data.pet;
  if (!pet) return;

  renderBanner(pet);
  renderHealthTab(pet);
  await renderCheckupTab(id);
}

/* ── Banner ─────────────────────────────────────────────────────────────── */
function renderBanner(pet) {
  document.getElementById('bannerName').textContent = `${pet.name}`;
  document.getElementById('bannerMeta').textContent =
    `${pet.breed} · ${pet.age} year${pet.age !== 1 ? 's' : ''} old · Owner: ${pet.owner_name}`;
  document.getElementById('bannerBadges').innerHTML =
    (pet.conditions || []).map(c => `<span class="badge badge-blue">${c.replace(/_/g,' ')}</span>`).join('') +
    (pet.food_allergies || []).map(a => `<span class="badge badge-red">⚠️ No ${a}</span>`).join('');
}

/* ── Health tab ─────────────────────────────────────────────────────────── */
async function renderHealthTab(pet) {
  document.getElementById('statAge').textContent        = pet.age;
  document.getElementById('statWeight').textContent     = pet.weight_kg;
  document.getElementById('statWeightStatus').textContent = pet.weight_status || '—';
  document.getElementById('statAgeCategory').textContent  = pet.age_category || '—';
  document.getElementById('healthNotes').textContent    = pet.health_notes || '—';

  const daysSince = pet.last_checkup_days_ago;
  document.getElementById('statDaysSince').textContent = daysSince;

  const alertBox = document.getElementById('healthAlertBox');
  if (daysSince > 365) {
    alertBox.innerHTML = `<div class="alert alert-red">⚠️ Annual checkup overdue — last visit was ${daysSince} days ago.</div>`;
  } else if (daysSince > 180) {
    alertBox.innerHTML = `<div class="alert alert-amber">⏰ Consider a checkup — last visit was ${daysSince} days ago.</div>`;
  } else {
    alertBox.innerHTML = `<div class="alert alert-green">✅ Checkup is up to date (${daysSince} days ago).</div>`;
  }

  document.getElementById('healthConditions').innerHTML =
    (pet.conditions || []).map(c =>
      `<span class="badge badge-purple">${c.replace(/_/g,' ')}</span>`).join('') || '<span class="muted">None</span>';

  document.getElementById('healthAllergies').innerHTML =
    (pet.food_allergies || []).map(a =>
      `<span class="badge badge-red">🚫 ${a}</span>`).join('') || '<span class="muted">No known allergies</span>';
}

/* ── Nutrition tab ───────────────────────────────────────────────────────── */
async function loadFoodRecommendations() {
  if (!selectedPetId) return alert('Please select a pet first.');
  const budget = document.getElementById('nutritionBudget').value || 100;
  const grid = document.getElementById('foodGrid');
  grid.innerHTML = '<span class="spinner">⏳</span> Loading recommendations…';

  const res  = await fetch(`/api/food-recommendations?pet_id=${selectedPetId}&budget=${budget}`);
  const data = await res.json();
  const foods = data.recommendations || [];

  if (!foods.length) { grid.innerHTML = '<p class="muted">No foods found for this budget.</p>'; return; }

  grid.innerHTML = foods.map(f => `
    <div class="food-card">
      <h4>${f.name}</h4>
      <div class="muted">${f.brand}</div>
      <div class="price">$${f.price}</div>
      <div>${(f.suitable_for||[]).map(s=>`<span class="badge badge-blue">${s.replace(/_/g,' ')}</span>`).join('')}</div>
      <div style="margin-top:6px">
        ${f.has_allergen ? '<span class="warn">⚠️ Contains allergen</span>' : '<span class="safe">✅ Safe for pet</span>'}
      </div>
      <div class="muted" style="margin-top:4px">${f.calories_per_cup || '—'} kcal/cup</div>
    </div>`).join('');
}

/* ── Recovery tab ────────────────────────────────────────────────────────── */
async function searchRemedies() {
  const cond = document.getElementById('recoveryCondition').value.trim();
  if (!cond) return alert('Enter a condition first.');
  await _showRemedies(cond);
}

async function loadConditionRemedies() {
  if (!selectedPetId) return alert('Select a pet first.');
  const pet = allPets.find(p => p.id === selectedPetId);
  const conditions = pet ? (pet.conditions || []) : [];
  if (!conditions.length) { document.getElementById('remedyResults').innerHTML = '<p class="muted">No conditions found for this pet.</p>'; return; }
  for (const c of conditions) await _showRemedies(c, true);
}

async function _showRemedies(condition, append = false) {
  const box = document.getElementById('remedyResults');
  if (!append) box.innerHTML = '';
  box.innerHTML += '<span class="spinner">⏳</span> Loading…';

  const res  = await fetch(`/api/health-knowledge?condition=${encodeURIComponent(condition)}`);
  const data = await res.json();
  const results = data.results || [];

  if (!append) box.innerHTML = '';
  else box.innerHTML = box.innerHTML.replace(/<span class="spinner">.*?<\/span> Loading…/g, '');

  if (!results.length) { box.innerHTML += `<p class="muted">No knowledge found for "${condition}".</p>`; return; }

  box.innerHTML += results.map(r => `
    <div class="card" style="margin-bottom:12px">
      <h2><span class="icon">🌿</span> ${r.title || r.condition}</h2>
      <p style="margin-bottom:12px">${r.content || '—'}</p>
      ${r.natural_remedies && r.natural_remedies.length ? `
        <strong>Natural Remedies:</strong>
        <ul style="margin-top:6px;padding-left:18px">
          ${r.natural_remedies.map(rem=>`<li>${rem}</li>`).join('')}
        </ul>` : ''}
    </div>`).join('');
}

/* ── Checkup tab ─────────────────────────────────────────────────────────── */
async function renderCheckupTab(petId) {
  const box = document.getElementById('checkupResult');
  box.innerHTML = '<span class="spinner">⏳</span> Checking…';

  const res  = await fetch(`/api/checkup-prediction?pet_id=${petId}`);
  const data = await res.json();
  const r    = data.result || {};

  const alertClass = r.urgency === 'high' ? 'alert-red' : r.urgency === 'medium' ? 'alert-amber' : 'alert-green';
  const icon = r.urgency === 'high' ? '🚨' : r.urgency === 'medium' ? '⚠️' : '✅';
  box.innerHTML = `
    <div class="alert ${alertClass}">
      <strong>${icon} ${r.needs_checkup ? 'Checkup Recommended' : 'No Checkup Needed Right Now'}</strong><br/>
      ${r.reason || 'Continue monitoring.'}
    </div>
    <div class="stat-grid">
      <div class="stat-card"><div class="val">${r.days_since ?? '—'}</div><div class="lbl">Days since last visit</div></div>
      <div class="stat-card"><div class="val">${r.urgency || '—'}</div><div class="lbl">Urgency</div></div>
      <div class="stat-card"><div class="val">${r.last_checkup ? r.last_checkup.slice(0,10) : '—'}</div><div class="lbl">Last checkup date</div></div>
    </div>
    <p style="margin-top:12px;font-weight:600">Recommended Action: ${r.recommended_action || '—'}</p>`;
}

async function loadKnowledge() {
  const filter = document.getElementById('knowledgeFilter').value.trim();
  const url = filter ? `/api/knowledge?condition=${encodeURIComponent(filter)}` : '/api/knowledge';
  const res  = await fetch(url);
  const data = await res.json();
  const items = data.knowledge || [];
  document.getElementById('knowledgeList').innerHTML = items.map(k => `
    <div style="padding:10px 0;border-bottom:1px solid var(--border)">
      <strong>${k.title || k.condition}</strong>
      <div style="margin-top:4px">${(k.natural_remedies||[]).map(r=>`<span class="badge badge-green">${r}</span>`).join('')}</div>
    </div>`).join('') || '<p class="muted">No results.</p>';
}

/* ── Volunteer tab ───────────────────────────────────────────────────────── */
async function findVolunteers() {
  if (!selectedPetId) return alert('Select a pet first.');
  const start = document.getElementById('startDate').value;
  const end   = document.getElementById('endDate').value;
  const dist  = document.getElementById('maxDistance').value;
  const grid  = document.getElementById('volunteerGrid');
  grid.innerHTML = '<span class="spinner">⏳</span> Searching…';

  const res  = await fetch(`/api/find-volunteers?pet_id=${selectedPetId}&start_date=${start}&end_date=${end}&max_distance_km=${dist}`);
  const data = await res.json();
  const vols = data.volunteers || [];

  grid.innerHTML = vols.length
    ? vols.map(renderVolCard).join('')
    : '<p class="muted">No matched pet minders found. Try increasing the date range or distance.</p>';
}

async function loadAllVolunteers() {
  const res  = await fetch('/api/volunteers');
  const data = await res.json();
  document.getElementById('allVolunteers').innerHTML =
    (data.volunteers || []).map(renderVolCard).join('') || '<p class="muted">None registered.</p>';
}

function renderVolCard(v) {
  const stars = '★'.repeat(Math.round(v.rating || 0)) + '☆'.repeat(5 - Math.round(v.rating || 0));
  return `
    <div class="vol-card">
      <h4>🙋 ${v.name}</h4>
      <div class="stars">${stars} <span style="color:var(--text);font-weight:700">${v.rating}</span></div>
      <div class="muted">${v.bio || ''}</div>
      <div>${(v.experience_breeds||[]).map(b=>`<span class="badge badge-blue">${b}</span>`).join('')}</div>
      <div style="font-size:14px;font-weight:700;color:var(--brand);margin-top:4px">$${v.price_per_day}/day</div>
    </div>`;
}

/* ── AI Chat tab ─────────────────────────────────────────────────────────── */
function setChatExample(btn) {
  document.getElementById('chatQuery').value = btn.dataset.q;
}

async function sendChatQuery() {
  const q = document.getElementById('chatQuery').value.trim();
  if (!q) return;
  const btn = document.getElementById('chatBtn');
  const out = document.getElementById('chatResponse');
  btn.disabled = true;
  out.textContent = '⏳ Thinking…';

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, pet_id: selectedPetId, max_iterations: 5 })
    });
    const data = await res.json();
    const answer = data.response || data.message || 'No response.';
    out.textContent = answer;

    chatHistory.unshift({ q, a: answer.slice(0, 120) + (answer.length > 120 ? '…' : '') });
    const hist = document.getElementById('chatHistory');
    hist.innerHTML = chatHistory.map(h =>
      `<li><strong>Q: ${h.q}</strong><br/><span class="muted">${h.a}</span></li>`).join('');
  } catch(e) {
    out.textContent = 'Request failed: ' + e;
  } finally {
    btn.disabled = false;
  }
}

/* ── Per-pet detail endpoint hit (inline enrichment) ──────────────────────── */
// The /api/pets/:id returns raw pet data; we enrich inline for health stats.
// Checkup and food tabs use dedicated API routes defined in app.py.
</script>
</body>
</html>
"""
