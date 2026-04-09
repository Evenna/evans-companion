/* ═══════════════════════════════════════════════
   Evans AI Companion — Frontend Logic
   ═══════════════════════════════════════════════ */

// ─── Global State ──────────────────────────────────────
let ws = null;
let cameraStream = null;
let pingTimer = null;
let reconnTimer = null;
let reconnAttempt = 0;
let allMemories = [];
let allReminders = [];
let chatHistory = [];
let stats = { memory: { total: 0 }, reminders: { total: 0, active: 0 } };
let currentMood = "neutral";

const MOOD_EMOJIS = {
  happy: "😊", sad: "😢", neutral: "😊", anxious: "😰",
  tired: "😴", excited: "🤩", angry: "😤", calm: "😌",
};
const MOOD_LABELS = {
  happy: "开心", sad: "低落", neutral: "平静", anxious: "焦虑",
  tired: "疲惫", excited: "兴奋", angry: "生气", calm: "放松",
};
const MOOD_COLORS = {
  happy: "#4caf72", sad: "#5fa8b8", neutral: "#7b8cde", anxious: "#c4975a",
  tired: "#9b7ec8", excited: "#c4748a", angry: "#c4594a", calm: "#5fa8b8",
};

// ─── DOM Refs ──────────────────────────────────────────
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const typingIndicator = document.getElementById("typingIndicator");
const memoryListEl = document.getElementById("memoryList");
const reminderListEl = document.getElementById("reminderList");

// ─── WebSocket ─────────────────────────────────────────
const proto = location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${proto}//${location.host}/ws`;

function connectWs(isReconn) {
  return new Promise((resolve, reject) => {
    if (!isReconn) reconnAttempt = 0;
    const s = new WebSocket(wsUrl);
    let opened = false;
    s.onopen = () => {
      opened = true; reconnAttempt = 0;
      updateConn(true);
      startPing(s);
      resolve(s);
    };
    s.onerror = () => updateConn(false);
    s.onclose = () => {
      stopPing();
      if (!opened) { reject(new Error("未建立")); return; }
      ws = null; updateConn(false);
      scheduleReconn();
    };
    s.onmessage = ev => {
      try { handleMsg(JSON.parse(ev.data)); } catch(e) { console.error(e); }
    };
  });
}

function startPing(s) {
  stopPing();
  pingTimer = setInterval(() => {
    if (s.readyState === WebSocket.OPEN) s.send(JSON.stringify({ type: "ping" }));
  }, 20000);
}
function stopPing() { if (pingTimer) { clearInterval(pingTimer); pingTimer = null; } }
function scheduleReconn() {
  if (reconnTimer) return;
  const delay = Math.min(30000, 1500 * Math.pow(1.5, reconnAttempt));
  reconnTimer = setTimeout(() => {
    reconnTimer = null; reconnAttempt++;
    connectWs(true).then(s => { ws = s; }).catch(() => scheduleReconn());
  }, delay);
}

function updateConn(ok) {
  const dot = document.getElementById("connDot");
  const text = document.getElementById("connText");
  const headerStatus = document.getElementById("headerStatus");
  if (dot) dot.className = "conn-dot " + (ok ? "online" : "");
  if (text) text.textContent = ok ? "已连接" : "重连中…";
  if (headerStatus) { headerStatus.textContent = ok ? "在线" : "离线"; headerStatus.style.color = ok ? "#4caf72" : "#c4594a"; }
}

// ─── Handle Messages ───────────────────────────────────
function handleMsg(j) {
  switch (j.type) {
    case "pong": break;

    case "session_init":
      if (j.stats) updateStats(j.stats);
      if (j.memories) { allMemories = j.memories; renderMemories(); }
      if (j.reminders_list) { allReminders = j.reminders_list; renderReminders(); }
      if (j.history) { chatHistory = j.history; renderChatHistory(); }
      addLog("system", "Evans 会话已初始化");
      break;

    case "typing":
      typingIndicator.classList.add("show");
      break;

    case "chat_response":
      typingIndicator.classList.remove("show");
      // Add assistant message
      addChatBubble("assistant", j.response, {
        mood: j.detected_mood,
        memories: j.new_memories,
        reminders: j.new_reminders,
      });
      currentMood = j.detected_mood || "neutral";
      updateMoodUI();
      if (j.new_memories && j.new_memories.length) {
        fetchMemories();
      }
      if (j.new_reminders && j.new_reminders.length) {
        fetchReminders();
      }
      if (j.stats) updateStats(j.stats);
      break;

    case "reminder_due":
      if (j.message) {
        addChatBubble("assistant", j.message, { proactive: true });
      }
      fetchReminders();
      break;

    case "result":
      // Image analysis result
      if (j.ok && j.data) {
        const l3 = j.data.layer3_cognition || {};
        const l6 = j.data.layer6_execution || {};
        const voice = l6.voice_response || l3.user_activity || "场景已分析";
        const scene = (j.data.layer2_fusion || {}).scene_label || "未知";
        addChatBubble("assistant", `📸 分析完成：${scene}\n${voice}`, {});
      }
      break;

    case "analyzing":
      typingIndicator.classList.add("show");
      break;

    case "error":
      typingIndicator.classList.remove("show");
      addLog("error", j.message);
      break;
  }
}

// ─── Send Chat Message ─────────────────────────────────
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  autoResizeTextarea();

  addChatBubble("user", text, {});

  try {
    await ensureWs();
  } catch {
    addLog("error", "未连接服务器");
    return;
  }

  ws.send(JSON.stringify({ type: "chat", text }));
}

function ensureWs() {
  if (ws && ws.readyState === WebSocket.OPEN) return Promise.resolve(ws);
  return connectWs(true).then(s => { ws = s; return s; });
}

// ─── Chat UI ───────────────────────────────────────────
function addChatBubble(role, text, meta = {}) {
  const welcome = document.getElementById("chatWelcome");
  if (welcome) welcome.remove();

  const div = document.createElement("div");
  div.className = `msg ${role}` + (meta.proactive ? " msg-proactive" : "");

  const avatar = role === "assistant" ? "💙" : "😊";
  const time = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });

  let metaHtml = "";
  if (meta.mood) metaHtml += `<span class="msg-tag mood">${MOOD_EMOJIS[meta.mood] || "😊"} ${MOOD_LABELS[meta.mood] || meta.mood}</span>`;
  if (meta.memories && meta.memories.length) metaHtml += `<span class="msg-tag memory">+${meta.memories.length} 记忆</span>`;
  if (meta.reminders && meta.reminders.length) metaHtml += `<span class="msg-tag reminder">+${meta.reminders.length} 提醒</span>`;

  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div>
      <div class="msg-bubble">${escHtml(text)}</div>
      ${metaHtml ? `<div class="msg-meta">${metaHtml}</div>` : ""}
      <div class="msg-time">${time}</div>
    </div>
  `;

  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderChatHistory() {
  chatMessages.innerHTML = "";
  if (!chatHistory.length) {
    chatMessages.innerHTML = `
      <div class="chat-welcome" id="chatWelcome">
        <div class="welcome-avatar">💙</div>
        <div class="welcome-text">嗨～我是 Evans，你的 AI 伴侣。有什么想聊的吗？或者让我帮你记点什么？</div>
        <div class="welcome-hint">试试发一条消息开始对话 ✨</div>
      </div>`;
    return;
  }
  chatHistory.forEach(m => {
    addChatBubble(m.role, m.content, {});
  });
}

// ─── Camera ────────────────────────────────────────────
async function toggleCamera() {
  const preview = document.getElementById("cameraPreview");
  const btn = document.getElementById("btnCamera");
  const video = document.getElementById("cameraVideo");

  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
    preview.classList.remove("show");
    btn.classList.remove("active");
    return;
  }

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 } }, audio: false });
    video.srcObject = cameraStream;
    preview.classList.add("show");
    btn.classList.add("active");
    document.getElementById("cameraOverlay").style.display = "none";
  } catch (e) {
    addLog("error", "摄像头失败: " + e.message);
  }
}

function captureAndSend() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  if (!cameraStream || !video.videoWidth) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);

  ensureWs().then(() => {
    ws.send(JSON.stringify({
      type: "analyze",
      image_base64: dataUrl,
      text: "",
      sensors: {},
      force: true,
    }));
  });
}

// ─── Memory API ────────────────────────────────────────
async function fetchMemories(category = "", query = "") {
  try {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (query) params.set("query", query);
    const resp = await fetch(`/api/memories?${params}`);
    const data = await resp.json();
    allMemories = data.items || [];
    renderMemories();
  } catch (e) {
    console.error("fetchMemories:", e);
  }
}

function renderMemories() {
  const searchVal = (document.getElementById("memorySearchInput")?.value || "").toLowerCase();
  const activeCat = document.querySelector(".cat-tag.active")?.dataset.cat || "all";

  let items = allMemories;
  if (activeCat !== "all") {
    items = items.filter(m => m.category === activeCat || m.category === activeCat + "s");
  }
  if (searchVal) {
    items = items.filter(m => m.content.toLowerCase().includes(searchVal));
  }

  if (!items.length) {
    memoryListEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📝</div><div>还没有记忆</div></div>';
    return;
  }

  memoryListEl.innerHTML = items.map(m => `
    <div class="memory-item">
      <div class="memory-item-header">
        <span class="memory-item-cat ${m.category}">${catLabel(m.category)}</span>
        <span class="memory-item-time">${formatTime(m.created_at)}</span>
      </div>
      <div class="memory-item-text">${escHtml(m.content)}</div>
      <div class="memory-item-actions">
        <button onclick="deleteMemory('${m.id}')">删除</button>
      </div>
    </div>
  `).join("");
}

async function addMemory() {
  const content = document.getElementById("memoryContent").value.trim();
  const category = document.getElementById("memoryCategory").value;
  if (!content) return;

  await fetch("/api/memories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, category, importance: 0.5 }),
  });

  document.getElementById("memoryContent").value = "";
  closeModal("memoryModal");
  fetchMemories();
  addChatBubble("assistant", `好的，我记住了 📝`, {});
}

async function deleteMemory(id) {
  await fetch(`/api/memories/${id}`, { method: "DELETE" });
  fetchMemories();
}

function catLabel(cat) {
  const map = { facts: "📌 事实", events: "📅 事件", preferences: "❤️ 偏好", people: "👤 人物", emotions: "💭 情感",
    fact: "📌 事实", event: "📅 事件", preference: "❤️ 偏好", emotion: "💭 情感" };
  return map[cat] || cat;
}

function filterMemories() { renderMemories(); }
function filterCat(cat) {
  document.querySelectorAll(".cat-tag").forEach(el => el.classList.toggle("active", el.dataset.cat === cat));
  renderMemories();
}

// ─── Reminder API ──────────────────────────────────────
async function fetchReminders() {
  try {
    const resp = await fetch("/api/reminders");
    const data = await resp.json();
    allReminders = data.items || [];
    renderReminders();
  } catch (e) {
    console.error("fetchReminders:", e);
  }
}

function renderReminders() {
  if (!allReminders.length) {
    reminderListEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⏰</div><div>暂无提醒</div></div>';
    return;
  }

  reminderListEl.innerHTML = allReminders.map(r => `
    <div class="reminder-item ${r.status === 'done' ? 'done' : ''}">
      <div class="reminder-item-header">
        <span class="reminder-item-time-icon">⏰</span>
        <span class="reminder-item-status ${r.status}">${r.status === 'active' ? '进行中' : '已完成'}</span>
      </div>
      <div class="reminder-item-text">${escHtml(r.text)}</div>
      <div class="reminder-item-trigger">${r.trigger_time ? formatTime(r.trigger_time) : '未设置时间'}${r.recurrence ? ' · ' + r.recurrence : ''}</div>
      <div class="reminder-item-actions">
        ${r.status === 'active' ? `<button class="done-btn" onclick="doneReminder('${r.id}')">完成</button>` : ''}
        <button onclick="deleteReminder('${r.id}')">删除</button>
      </div>
    </div>
  `).join("");
}

async function addReminder() {
  const text = document.getElementById("reminderContent").value.trim();
  const timeVal = document.getElementById("reminderTime").value;
  if (!text) return;

  // Convert datetime-local to natural text for backend
  let timeText = "";
  if (timeVal) {
    const d = new Date(timeVal);
    timeText = `${d.getMonth()+1}月${d.getDate()}日${d.getHours()}点${d.getMinutes() ? d.getMinutes()+'分' : ''}`;
  }

  await fetch("/api/reminders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, time_text: timeText }),
  });

  document.getElementById("reminderContent").value = "";
  document.getElementById("reminderTime").value = "";
  closeModal("reminderModal");
  fetchReminders();
  addChatBubble("assistant", `好的，我会提醒你的 ⏰`, {});
}

async function doneReminder(id) {
  await fetch(`/api/reminders/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "done" }),
  });
  fetchReminders();
}

async function deleteReminder(id) {
  await fetch(`/api/reminders/${id}`, { method: "DELETE" });
  fetchReminders();
}

// ─── Stats ─────────────────────────────────────────────
function updateStats(s) {
  stats = s;
  const mem = s.memory || {};
  const rem = s.reminders || {};
  document.getElementById("statMemories").textContent = mem.total || 0;
  document.getElementById("statReminders").textContent = rem.active || 0;
  // Chat count from history
  const chatCount = chatHistory.length;
  document.getElementById("statChats").textContent = chatCount;
}

async function fetchStats() {
  try {
    const resp = await fetch("/api/stats");
    const s = await resp.json();
    updateStats(s);
    // Update mood from proactive status
    if (s.proactive && s.proactive.current_mood) {
      currentMood = s.proactive.current_mood;
      updateMoodUI();
    }
  } catch {}
}

function updateMoodUI() {
  const emoji = MOOD_EMOJIS[currentMood] || "😊";
  const label = MOOD_LABELS[currentMood] || "平静";
  const el1 = document.getElementById("moodEmoji");
  const el2 = document.getElementById("moodText");
  const el3 = document.getElementById("insightMoodEmoji");
  const el4 = document.getElementById("insightMoodLabel");
  if (el1) el1.textContent = emoji;
  if (el2) el2.textContent = label;
  if (el3) el3.textContent = emoji;
  if (el4) el4.textContent = label;
}

// ─── Mood Chart ────────────────────────────────────────
function updateMoodChart() {
  const chart = document.getElementById("moodChart");
  if (!chart) return;
  // Simple bar chart from recent moods
  const moods = ["happy", "neutral", "calm", "tired", "sad", "anxious"];
  chart.innerHTML = moods.map(m => {
    const h = m === currentMood ? 50 : 15;
    return `<div class="mood-bar" style="height:${h}px;background:${MOOD_COLORS[m] || '#7b8cde'}" title="${MOOD_LABELS[m]}"></div>`;
  }).join("");
}

// ─── Tabs ──────────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll(".panel-tab").forEach(el => el.classList.toggle("active", el.dataset.tab === tab));
  document.querySelectorAll(".tab-content").forEach(el => {
    el.classList.toggle("active", el.id === "tab" + tab.charAt(0).toUpperCase() + tab.slice(1));
  });
  if (tab === "insights") updateMoodChart();
}

// ─── Sidebar Toggle ────────────────────────────────────
function toggleSidebar(side) {
  const el = side === "left" ? document.getElementById("sidebar-left") : document.getElementById("sidebar-right");
  el.classList.toggle("show");
}

// ─── Modals ────────────────────────────────────────────
function openModal(id) { document.getElementById(id)?.classList.add("show"); }
function closeModal(id) { document.getElementById(id)?.classList.remove("show"); }

// ─── Log ───────────────────────────────────────────────
function addLog(type, detail) {
  const ts = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  const list = document.getElementById("logList");
  if (!list) return;
  const div = document.createElement("div");
  div.className = "log-item";
  div.innerHTML = `<span class="log-ts">${ts}</span><span class="log-detail">${escHtml(detail)}</span>`;
  list.prepend(div);
  while (list.children.length > 50) list.lastChild.remove();
}

function toggleLog() {
  document.getElementById("log-footer")?.classList.toggle("open");
}

// ─── Quick Actions ─────────────────────────────────────
function sendMoodCheck() {
  const msg = "我现在心情怎么样？";
  chatInput.value = msg;
  sendMessage();
}

// ─── Utilities ─────────────────────────────────────────
function escHtml(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n/g,"<br>");
}

function formatTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}

function autoResizeTextarea() {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
}

// ─── Event Listeners ───────────────────────────────────
chatInput?.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
chatInput?.addEventListener("input", autoResizeTextarea);

// ─── Reminder check polling ────────────────────────────
setInterval(async () => {
  try {
    const resp = await fetch("/api/reminders/check", { method: "POST" });
    const data = await resp.json();
    if (data.due && data.due.length) {
      data.due.forEach(r => {
        addChatBubble("assistant", `⏰ 提醒：${r.text}`, { proactive: true });
      });
      fetchReminders();
    }
  } catch {}
}, 30000);

// Stats polling
setInterval(fetchStats, 30000);

// ─── Init ──────────────────────────────────────────────
connectWs(false).then(s => { ws = s; }).catch(() => scheduleReconn());
fetchMemories();
fetchReminders();
fetchStats();
addLog("system", "Evans 已就绪");

// Make functions available to onclick handlers
window.sendMessage = sendMessage;
window.toggleCamera = toggleCamera;
window.captureAndSend = captureAndSend;
window.addMemory = addMemory;
window.addReminder = addReminder;
window.deleteMemory = deleteMemory;
window.deleteReminder = deleteReminder;
window.doneReminder = doneReminder;
window.filterMemories = filterMemories;
window.filterCat = filterCat;
window.switchTab = switchTab;
window.toggleSidebar = toggleSidebar;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleLog = toggleLog;
window.sendMoodCheck = sendMoodCheck;
