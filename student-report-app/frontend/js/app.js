/* ================================================
   app.js — Gradar Frontend
   ================================================ */

const API = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:'
  ? 'http://127.0.0.1:5000/api'
  : '/api';

const SUBJECTS = [
  { id: 'mark-tamil',   name: 'Tamil' },
  { id: 'mark-english', name: 'English' },
  { id: 'mark-maths',   name: 'Maths' },
  { id: 'mark-science', name: 'Science' },
  { id: 'mark-social',  name: 'Social Science' },
];

// ─── Authentication state & helpers ────────────────
function getToken() {
  return localStorage.getItem('gradar_admin_token');
}

function setToken(token) {
  if (token) localStorage.setItem('gradar_admin_token', token);
  else localStorage.removeItem('gradar_admin_token');
}

async function authFetch(url, options = {}) {
  const token = getToken();
  options.headers = options.headers || {};
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }
  
  const res = await fetch(url, options);
  
  if (res.status === 401) {
    const clone = res.clone();
    const data = await clone.json().catch(() => ({}));
    if (data.code === 'TOKEN_EXPIRED') {
      toast('warning', 'Session Expired', 'Your admin session has expired. Please sign in again.');
    }
    logoutAdmin();
  }
  return res;
}

// ─── Credentials state ────────────────────────────
let creds = { email: '', password: '', verified: false };

// ─── Students state ───────────────────────────────
let students = [];

// ─── DOM ─────────────────────────────────────────
const emailInput      = document.getElementById('sender-email');
const passwordInput   = document.getElementById('sender-password');
const testCredsBtn    = document.getElementById('test-creds-btn');
const saveCredsBtn    = document.getElementById('save-creds-btn');
const togglePwBtn     = document.getElementById('toggle-pw');
const studentsBody    = document.getElementById('students-table-body');
const emptyState      = document.getElementById('empty-state');
const tableWrapper    = document.getElementById('table-wrapper');
const emailModal      = document.getElementById('email-modal-overlay');
const emailResultsLog = document.getElementById('email-results-log');
const teacherModal    = document.getElementById('teacher-modal-overlay');

// ─── Toast ───────────────────────────────────────
function toast(type, title, msg, ms = 4500) {
  const icons = { success:'✅', error:'❌', info:'ℹ️', warning:'⚠️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type]||'📢'}</span>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-message">${msg}</div>` : ''}
    </div>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => { el.classList.add('removing'); setTimeout(() => el.remove(), 300); }, ms);
}

// ─── Show/hide password ───────────────────────────
togglePwBtn.addEventListener('click', () => {
  const show = passwordInput.type === 'password';
  passwordInput.type = show ? 'text' : 'password';
  togglePwBtn.textContent = show ? '🙈' : '👁️';
});

// ─── Credential status badge ─────────────────────
function setCredBadge(state, label) {
  document.querySelectorAll('.cred-status-badge').forEach(el => {
    el.className = `cred-status-badge ${state}`;
    el.textContent = label;
  });
}

// ─── Test Connection ──────────────────────────────
testCredsBtn.addEventListener('click', async () => {
  const email = emailInput.value.trim();
  const pass  = passwordInput.value.trim();

  if (!email || !pass) {
    toast('warning', 'Missing Fields', 'Enter both your Gmail address and App Password first.');
    return;
  }

  setCredBadge('cred-checking', '🔄 Testing…');
  testCredsBtn.classList.add('loading');
  testCredsBtn.disabled = true;

  try {
    const res  = await authFetch(`${API}/verify-credentials`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sender_email: email, sender_password: pass }),
    });
    const data = await res.json();

    if (data.success) {
      setCredBadge('cred-ok', '✅ Connected');
      toast('success', 'Connection Successful!',
        'Gmail credentials verified. You can now send emails to parents.');
    } else {
      setCredBadge('cred-fail', '❌ Failed');
      toast('error', 'Connection Failed', data.message || 'Could not connect to Gmail.');
    }
  } catch {
    setCredBadge('cred-fail', '❌ Error');
    toast('error', 'Server Error', 'Could not reach the backend. Is Flask running?');
  } finally {
    testCredsBtn.classList.remove('loading');
    testCredsBtn.disabled = false;
  }
});

// ─── Save & Activate ─────────────────────────────
saveCredsBtn.addEventListener('click', () => {
  const email = emailInput.value.trim();
  const pass  = passwordInput.value.trim();

  if (!email || !pass) {
    toast('warning', 'Missing Fields', 'Enter both Gmail address and App Password.');
    emailInput.focus();
    return;
  }

  creds = { email, password: pass, verified: false };
  setCredBadge('cred-ok', '🔑 Saved — Ready to Send');
  toast('success', 'Credentials Activated!',
    'Click "✉️ Send" on any student row to send their report card to the parent.');
  teacherModal.classList.remove('active');
});

// ─── Get active credentials (with validation) ────
function getCredentials() {
  // Prefer explicitly saved, fall back to current field values
  const email = creds.email || emailInput.value.trim();
  const pass  = creds.password || passwordInput.value.trim();
  return { email, pass };
}

function requireCreds() {
  const { email, pass } = getCredentials();
  if (!email || !pass) {
    toast('warning', 'Setup Required',
      'Please enter your Gmail & App Password in the Teacher Email Setup panel, then click "Save & Activate".');
    emailInput.focus();
    return null;
  }
  return { email, pass };
}

// ─── Fetch students ───────────────────────────────
async function fetchStudents() {
  try {
    const res = await authFetch(`${API}/students`);
    students = await res.json();
    renderTable();
    fetchSummary();

    // Trigger logo and background neon lines shine animations on load/refresh/data push
    triggerLogoShine();
    triggerNeonBgShine();
  } catch {
    toast('error', 'Connection Error', 'Cannot connect to backend. Is Flask running on port 5000?');
  }
}

// ─── Fetch summary ────────────────────────────────
async function fetchSummary() {
  try {
    const res  = await authFetch(`${API}/summary`);
    const data = await res.json();
    document.getElementById('stat-total').textContent   = data.total_students;
    document.getElementById('stat-avg').textContent     = data.class_average ? `${data.class_average}%` : '—';
    document.getElementById('stat-top').textContent     = data.top_student ? data.top_student.name.split(' ')[0] : '—';
    document.getElementById('stat-emailed').textContent = students.filter(s => s.email_sent).length;
    renderGradeChart(data.grade_distribution, data.total_students);
  } catch { /* silent */ }
}

// ─── Logo Shine Effect ────────────────────────────
function triggerLogoShine() {
  const logo = document.getElementById('brand-logo');
  if (!logo) return;
  logo.classList.remove('shine-active');
  // Force reflow so the animation restarts
  void logo.offsetWidth;
  logo.classList.add('shine-active');
}

// ─── Neon Background Shine Effect ─────────────────
function triggerNeonBgShine() {
  const bgLines = document.getElementById('bg-neon-lines-wrap');
  if (!bgLines) return;
  bgLines.classList.remove('supercharge');
  // Force reflow so the animation restarts
  void bgLines.offsetWidth;
  bgLines.classList.add('supercharge');
}

// ─── Helpers ──────────────────────────────────────
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}
function subjectClass(m) {
  return m >= 75 ? 'high' : m >= 50 ? 'mid' : 'low';
}
function avgClass(avg) {
  if (avg >= 90) return 'avg-excellent';
  if (avg >= 75) return 'avg-good';
  if (avg >= 60) return 'avg-average';
  return 'avg-poor';
}

// ─── Render table ─────────────────────────────────
function renderTable() {
  if (!students.length) {
    emptyState.classList.remove('hidden');
    tableWrapper.classList.add('hidden');
    return;
  }
  emptyState.classList.add('hidden');
  tableWrapper.classList.remove('hidden');
  studentsBody.innerHTML = '';

  students.forEach(s => {
    const rankClass  = s.rank <= 3 ? `rank-${s.rank}` : 'rank-other';
    const rankLabel  = s.rank === 1 ? '🥇' : s.rank === 2 ? '🥈' : s.rank === 3 ? '🥉' : s.rank;
    const emailBadge = s.email_sent
      ? `<span class="email-status sent">✉️ Sent</span>`
      : `<span class="email-status pending">⏳ Pending</span>`;

    const sendBtnClass = s.email_sent
      ? 'btn btn-send btn-sm sent'
      : 'btn btn-send btn-sm';
    const sendLabel = s.email_sent ? '✔ Resend' : '✉️ Send';

    // Serialise marks for the delete modal onclick (as JSON-safe)
    const marksJson = JSON.stringify(s.marks).replace(/"/g, '&quot;');

    const tr = document.createElement('tr');
    tr.setAttribute('data-id', s.id);
    tr.innerHTML = `
      <td class="text-center"><span class="rank-badge ${rankClass}">${rankLabel}</span></td>
      <td>
        <div style="font-weight:600;color:var(--text-primary)">${esc(s.name)}</div>
        <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px">${esc(s.parent_email)}</div>
      </td>
      <td class="text-center"><span class="subject-cell ${subjectClass(s.marks[0])}">${s.marks[0] ?? '—'}</span></td>
      <td class="text-center"><span class="subject-cell ${subjectClass(s.marks[1])}">${s.marks[1] ?? '—'}</span></td>
      <td class="text-center"><span class="subject-cell ${subjectClass(s.marks[2])}">${s.marks[2] ?? '—'}</span></td>
      <td class="text-center"><span class="subject-cell ${subjectClass(s.marks[3])}">${s.marks[3] ?? '—'}</span></td>
      <td class="text-center"><span class="subject-cell ${subjectClass(s.marks[4])}">${s.marks[4] ?? '—'}</span></td>
      <td class="text-center" style="font-family:var(--font-mono);font-weight:700">${s.total}</td>
      <td class="text-center"><span class="avg-badge ${avgClass(s.average)}">${s.average}%</span></td>
      <td class="text-center">${emailBadge}</td>
      <td class="text-center">
        <div class="action-cell" style="justify-content: center;">
          <button class="${sendBtnClass}" id="send-btn-${s.id}"
            onclick="sendSingleEmail(${s.id},'${esc(s.name)}','${esc(s.parent_email)}')"
            title="Send report card to ${esc(s.parent_email)}">
            ${sendLabel}
          </button>
          <button class="btn btn-danger btn-sm"
            onclick="deleteStudent(${s.id},'${esc(s.name)}','${esc(s.parent_email)}',${marksJson},${s.total},${s.average})"
            title="Delete ${esc(s.name)}'s record">
            🗑️ Delete
          </button>
        </div>
      </td>`;
    studentsBody.appendChild(tr);
  });

  // Show / hide Delete All button
  const delAllBtn = document.getElementById('delete-all-btn');
  if (students.length > 0) delAllBtn.classList.remove('hidden');
  else delAllBtn.classList.add('hidden');
}

// ─── Grade chart ──────────────────────────────────
function renderGradeChart(dist, total) {
  const chart = document.getElementById('grade-chart');
  if (!total) {
    chart.innerHTML = `
      <p class="text-muted" style="font-size:0.85rem;text-align:center;padding:1rem 0">
        Add students to see the distribution.
      </p>`;
    return;
  }
  const colors = {
    '90-100':   'linear-gradient(90deg,#68d391,#38a169)',
    '80-89':    'linear-gradient(90deg,#63b3ed,#4299e1)',
    '70-79':    'linear-gradient(90deg,#9f7aea,#805ad5)',
    '60-69':    'linear-gradient(90deg,#f6ad55,#ed8936)',
    'Below 60': 'linear-gradient(90deg,#fc8181,#e53e3e)',
  };
  chart.innerHTML = '';
  Object.entries(dist).forEach(([label, count]) => {
    const pct = total > 0 ? (count / total) * 100 : 0;
    const row = document.createElement('div');
    row.className = 'grade-row';
    row.innerHTML = `
      <span class="grade-label">${label}</span>
      <div class="grade-bar-track">
        <div class="grade-bar-fill" data-pct="${pct}"
             style="background:${colors[label]};width:0%"></div>
      </div>
      <span class="grade-count">${count}</span>`;
    chart.appendChild(row);
  });
  requestAnimationFrame(() => {
    chart.querySelectorAll('.grade-bar-fill').forEach(b => {
      setTimeout(() => { b.style.width = b.dataset.pct + '%'; }, 100);
    });
  });
}

// ─── Add student ──────────────────────────────────
document.getElementById('add-student-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name  = document.getElementById('student-name').value.trim();
  const email = document.getElementById('parent-email').value.trim();
  if (!name || !email) { toast('error', 'Missing Fields', 'Name and parent email are required.'); return; }

  const marks   = SUBJECTS.map(s => parseInt(document.getElementById(s.id).value, 10));
  const missing = SUBJECTS.filter((_, i) => isNaN(marks[i]));
  if (missing.length) {
    toast('error', 'Missing Marks', `Enter marks for: ${missing.map(s => s.name).join(', ')}`);
    return;
  }
  if (marks.some(m => m < 0 || m > 100)) {
    toast('error', 'Invalid Marks', 'Each mark must be between 0 and 100.'); return;
  }

  const btn = document.getElementById('add-btn');
  btn.classList.add('loading'); btn.disabled = true;

  try {
    const res  = await authFetch(`${API}/students`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, parent_email: email, marks }),
    });
    const data = await res.json();
    if (res.ok) {
      toast('success', 'Student Added', `${name} added to the leaderboard.`);
      document.getElementById('add-student-form').reset();
      fetchStudents();
    } else {
      toast('error', 'Error', data.error || 'Failed to add student.');
    }
  } catch { toast('error', 'Connection Error', 'Could not reach the backend.'); }
  finally { btn.classList.remove('loading'); btn.disabled = false; }
});

// Enter moves to next subject field
document.querySelectorAll('.subject-input').forEach((el, i, all) => {
  el.addEventListener('keydown', ev => {
    if (ev.key === 'Enter') {
      ev.preventDefault();
      (all[i + 1] || document.getElementById('add-btn')).focus();
    }
  });
});

// ─── Delete Modal state ──────────────────────────
let pendingDeleteId   = null;
let pendingDeleteName = '';

const deleteModal    = document.getElementById('delete-modal-overlay');
const deleteAllModal = document.getElementById('delete-all-modal-overlay');

function openDeleteModal(id, name, email, marks, total, avg) {
  pendingDeleteId   = id;
  pendingDeleteName = name;

  // Populate modal
  document.getElementById('del-avatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('del-name').textContent   = name;
  document.getElementById('del-email').textContent  = email;

  const subjectLabels = ['Tamil','English','Maths','Science','Social'];
  const markStr = (marks || []).map((m, i) => `${subjectLabels[i]}: ${m}`).join('  |  ');
  document.getElementById('del-marks').textContent =
    `${markStr}  ·  Total: ${total}  ·  Avg: ${avg}%`;

  deleteModal.classList.add('active');
  // re-trigger shake animation
  const icon = deleteModal.querySelector('.delete-modal-icon');
  icon.style.animation = 'none';
  requestAnimationFrame(() => { icon.style.animation = ''; });
}

function closeDeleteModal() {
  deleteModal.classList.remove('active');
  pendingDeleteId   = null;
  pendingDeleteName = '';
}

// Cancel / backdrop close
document.getElementById('del-cancel-btn').addEventListener('click', closeDeleteModal);
deleteModal.addEventListener('click', e => { if (e.target === deleteModal) closeDeleteModal(); });

// ── Confirm single delete ────────────────────────
document.getElementById('del-confirm-btn').addEventListener('click', async () => {
  if (!pendingDeleteId) return;

  const btn = document.getElementById('del-confirm-btn');
  btn.classList.add('loading'); btn.disabled = true;

  try {
    const res = await authFetch(`${API}/students/${pendingDeleteId}`, { method: 'DELETE' });
    if (res.ok) {
      toast('success', 'Record Deleted', `${pendingDeleteName}'s record has been removed.`);
      closeDeleteModal();
      fetchStudents();
    } else {
      toast('error', 'Error', 'Failed to delete student record.');
    }
  } catch {
    toast('error', 'Connection Error', 'Could not reach the backend.');
  } finally {
    btn.classList.remove('loading'); btn.disabled = false;
  }
});

// ── Delete All modal ────────────────────────────
document.getElementById('delete-all-btn').addEventListener('click', () => {
  document.getElementById('del-all-count').textContent = `all ${students.length}`;
  deleteAllModal.classList.add('active');
});

document.getElementById('del-all-cancel-btn').addEventListener('click', () =>
  deleteAllModal.classList.remove('active'));
deleteAllModal.addEventListener('click', e => {
  if (e.target === deleteAllModal) deleteAllModal.classList.remove('active');
});

document.getElementById('del-all-confirm-btn').addEventListener('click', async () => {
  const btn = document.getElementById('del-all-confirm-btn');
  btn.classList.add('loading'); btn.disabled = true;

  // Delete one by one (sequential so ranks stay consistent)
  const ids = students.map(s => s.id);
  let deleted = 0;
  for (const id of ids) {
    try {
      const res = await authFetch(`${API}/students/${id}`, { method: 'DELETE' });
      if (res.ok) deleted++;
    } catch { /* continue */ }
  }

  btn.classList.remove('loading'); btn.disabled = false;
  deleteAllModal.classList.remove('active');
  toast('success', 'All Records Cleared', `${deleted} student records deleted.`);
  fetchStudents();
});

// ─── Delete single student (opens modal) ─────────
function deleteStudent(id, name, email, marks, total, avg) {
  openDeleteModal(id, name, email, marks, total, avg);
}

// ─── Send email to ONE student ────────────────────
async function sendSingleEmail(id, name, parentEmail) {
  const cr = requireCreds();
  if (!cr) return;

  const btn = document.getElementById(`send-btn-${id}`);
  if (btn) {
    btn.classList.add('sending');
    btn.innerHTML = `<span class="spinner"
      style="display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.7s linear infinite"></span> Sending…`;
  }

  toast('info', 'Sending…', `Sending report card to ${parentEmail}`);

  try {
    const res  = await authFetch(`${API}/send-email/${id}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sender_email: cr.email, sender_password: cr.pass }),
    });
    const data = await res.json();

    if (res.ok && data.success) {
      toast('success', '📬 Report Card Sent!',
        `Successfully delivered to ${parentEmail}`);
      if (btn) { btn.classList.remove('sending'); btn.classList.add('sent'); btn.innerHTML = '✔ Sent'; }
      fetchStudents();
    } else {
      const errMsg = data.message || data.error || 'Unknown error';
      toast('error', 'Send Failed', errMsg);
      if (btn) { btn.classList.remove('sending'); btn.innerHTML = '✉️ Retry'; }
    }
  } catch {
    toast('error', 'Connection Error', 'Could not reach the backend.');
    if (btn) { btn.classList.remove('sending'); btn.innerHTML = '✉️ Retry'; }
  }
}

// ─── Send ALL emails ──────────────────────────────
document.getElementById('send-all-btn').addEventListener('click', async () => {
  const cr = requireCreds();
  if (!cr) return;
  if (!students.length) { toast('info', 'No Students', 'Add students first.'); return; }

  const btn = document.getElementById('send-all-btn');
  btn.classList.add('loading'); btn.disabled = true;
  emailResultsLog.innerHTML = '';

  try {
    const res  = await authFetch(`${API}/send-emails`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sender_email: cr.email, sender_password: cr.pass }),
    });
    const data = await res.json();

    if (res.ok) {
      emailModal.classList.add('active');
      data.results.forEach(r => {
        const item = document.createElement('div');
        item.className = `email-result-item ${r.success ? 'success' : 'error'}`;
        item.innerHTML = `
          <span>${r.success ? '✅' : '❌'}</span>
          <span><strong>${r.student}</strong> — ${r.message}</span>`;
        emailResultsLog.appendChild(item);
      });
      const sent = data.results.filter(r => r.success).length;
      toast('success', 'All Emails Processed',
        `${sent}/${data.results.length} report cards sent to parents.`);
      fetchStudents();
    } else {
      toast('error', 'Error', data.error || 'Failed to send emails.');
    }
  } catch { toast('error', 'Connection Error', 'Could not reach the backend.'); }
  finally { btn.classList.remove('loading'); btn.disabled = false; }
});

// ─── Close modal ──────────────────────────────────
['close-modal-btn', 'cancel-modal-btn'].forEach(id =>
  document.getElementById(id).addEventListener('click', () => emailModal.classList.remove('active'))
);
emailModal.addEventListener('click', e => { if (e.target === emailModal) emailModal.classList.remove('active'); });

// ─── Setup SMTP Modal ──────────────────────────────
document.getElementById('setup-btn').addEventListener('click', () => {
  teacherModal.classList.add('active');
});
document.getElementById('close-teacher-modal-btn').addEventListener('click', () => {
  teacherModal.classList.remove('active');
});
teacherModal.addEventListener('click', e => {
  if (e.target === teacherModal) teacherModal.classList.remove('active');
});

// ─── Export CSV ───────────────────────────────────
document.getElementById('export-csv-btn').addEventListener('click', () => {
  if (!students.length) { toast('info', 'No Data', 'Add students before exporting.'); return; }
  window.location.href = `${API}/export-csv?token=${encodeURIComponent(getToken() || '')}`;
  toast('success', 'Downloading', 'CSV file is being downloaded.');
});

// ─── Admin Authentication handlers ────────────────
async function checkAuthOnLoad() {
  const token = getToken();
  if (!token) {
    showLoginScreen();
    return;
  }
  
  try {
    const res = await fetch(`${API}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (res.ok && data.success) {
      loginAdminSuccess(data.admin);
    } else {
      logoutAdmin();
    }
  } catch {
    showLoginScreen();
  }
}

function showLoginScreen() {
  const loginOverlay = document.getElementById('login-screen-overlay');
  if (loginOverlay) loginOverlay.classList.add('active');
  
  // Hide authenticated elements
  document.getElementById('nav-admin-profile').style.display = 'none';
  document.getElementById('logout-btn').style.display = 'none';
}

function loginAdminSuccess(admin) {
  const loginOverlay = document.getElementById('login-screen-overlay');
  if (loginOverlay) loginOverlay.classList.remove('active');
  
  // Show admin UI info
  const profile = document.getElementById('nav-admin-profile');
  const logout = document.getElementById('logout-btn');
  const nameEl = document.getElementById('admin-name');
  const avatarEl = document.getElementById('admin-avatar');
  
  if (profile) profile.style.display = 'flex';
  if (logout) logout.style.display = 'inline-flex';
  if (nameEl) nameEl.textContent = admin.username;
  if (avatarEl) avatarEl.textContent = admin.username.charAt(0).toUpperCase();
  
  // Fetch dashboard data
  fetchStudents();
}

function logoutAdmin() {
  setToken(null);
  showLoginScreen();
  // Clear lists
  students = [];
  renderTable();
}

// ─── Login Form Submit ────────────────────────────
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const errEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');
    
    if (!username || !password) return;
    
    errEl.style.display = 'none';
    btn.classList.add('loading');
    btn.disabled = true;
    
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      
      if (res.ok && data.success) {
        setToken(data.token);
        loginAdminSuccess(data.admin);
        toast('success', 'Welcome Back!', `Signed in successfully as ${data.admin.username}.`);
        document.getElementById('login-form').reset();
      } else {
        errEl.textContent = data.error || 'Invalid credentials.';
        errEl.style.display = 'flex';
        // shake effect
        errEl.style.animation = 'none';
        void errEl.offsetHeight; // force reflow
        errEl.style.animation = '';
      }
    } catch {
      errEl.textContent = 'Server connection failed. Is Flask running?';
      errEl.style.display = 'flex';
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  });
}

// ─── Logout Button Click ──────────────────────────
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', () => {
    logoutAdmin();
    toast('info', 'Signed Out', 'You have been successfully signed out.');
  });
}

// ─── Init ─────────────────────────────────────────
checkAuthOnLoad();
