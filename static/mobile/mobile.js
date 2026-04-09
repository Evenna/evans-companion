/* ══════════════════════════════════════════════════════
   Nexus Mobile JS  ·  预制人物：李建国
   ══════════════════════════════════════════════════════ */

/* ── 人物档案（预制数据） ─────────────────────────────── */
const PERSONA = {
  name:    '李建国',
  age:     68,
  job:     '退休教师',
  city:    '北京',
  group:   'elderly',
  style:   'gentle',
  level:   0.8,
  tags:    ['高血压', '独居', '爱下棋'],
  health: {
    meds:    '苯磺酸氨氯地平 5mg · 每日 12:30',
    doctor:  '张医生 · 社区卫生中心',
    bp:      '收缩压 < 140',
    steps:   3421,
    sleep:   7.5,
    hr:      72,
  },
  contacts: [
    { name: '李明',  rel: '儿子',  phone: '138-xxxx-5566', key: 'blue' },
    { name: '王淑芬', rel: '配偶 · 同住', key: 'green' },
  ],
};

const MOCK_TIMELINE = [
  { time: '刚刚',     tag: '场景',   text: '李建国正在客厅沙发上休息，光线充足，状态平稳' },
  { time: '15 分钟前', tag: '健康',   text: '检测到主人在椅子上坐立时间超过 90 分钟，建议起身活动' },
  { time: '12:32',   tag: '提醒',   text: '服药提醒已触发：苯磺酸氨氯地平 5mg，已确认服用' },
  { time: '11:20',   tag: '社交',   text: '检测到来访者，疑似为老陈（棋友），沟通约定明日下棋' },
  { time: '10:05',   tag: '运动',   text: '晨间散步 35 分钟，步数 3,421 步，状态良好' },
  { time: '09:00',   tag: '设备',   text: '空调已自动调节至 24°C，室温 27°C，相对湿度 62%' },
  { time: '昨天 19:10', tag: '社交', text: '与儿子李明视频通话 28 分钟，情绪愉悦' },
  { time: '昨天 15:40', tag: '场景', text: '下午阳光充足，检测到李建国在阳台浇花，精神状态良好' },
];

const MOCK_SCHEDULE = [
  { time: '12:30', date: '今天', text: '服降压药', sub: '苯磺酸氨氯地平 5mg · 饭后服用', done: true,  cat: 'health'  },
  { time: '19:00', date: '今天', text: '视频通话家人', sub: '李明一家 · 预计 30 分钟',   done: false, cat: 'social'  },
  { time: '09:00', date: '明天', text: '公园下棋',     sub: '与老陈约好 · 中山公园东门', done: false, cat: 'leisure' },
  { time: '14:00', date: '明天', text: '社区门诊复诊', sub: '张医生 · 带上上次化验单',   done: false, cat: 'health'  },
  { time: '全天',  date: '周六', text: '孙女李小雨来探望', sub: '儿子李明一家四口 · 备好午饭', done: false, cat: 'social' },
  { time: '10:00', date: '下周一', text: '扫地机器人深度清洁', sub: '全屋模式 · 预计 80 分钟', done: false, cat: 'device' },
  { time: '08:30', date: '下周三', text: '健康档案年度汇总', sub: 'Nexus 自动生成 · 发送给张医生', done: false, cat: 'ai' },
];

const MOCK_DEVICES = {
  /* 智能家居 */
  lights:       { state: 'on',  label: '主灯',       note: '客厅 · 暖白 3000K', group: '照明' },
  lamp:         { state: 'on',  label: '台灯',        note: '书房 · 护眼模式',   group: '照明' },
  ac:           { state: 'on',  label: '空调',        note: '24°C · 制冷',       group: '环境' },
  air_purifier: { state: 'on',  label: '空气净化器',  note: 'PM2.5: 12 · 优',   group: '环境' },
  speaker:      { state: 'off', label: '智能音箱',    note: '待机中',            group: '娱乐' },
  tv:           { state: 'off', label: '智能电视',    note: '65寸 · 已关闭',     group: '娱乐' },
  fridge:       { state: 'on',  label: '智能冰箱',    note: '2°C · 库存 86%',   group: '厨房' },
  /* 安全 */
  door_lock:    { state: 'on',  label: '智能门锁',    note: '已上锁 · 无异常',   group: '安全' },
  camera:       { state: 'on',  label: '室内摄像头',  note: '监测中 · 无事件',   group: '安全' },
  doorbell:     { state: 'on',  label: '智能门铃',    note: '在线 · 今日 1 访',  group: '安全' },
  /* 机器人 */
  sweeper:      { state: 'off', label: '扫地机器人',  note: '上次: 今天 8:30',   group: '机器人' },
  mopper:       { state: 'off', label: '拖地机器人',  note: '电量 78%',          group: '机器人' },
  robot_arm:    { state: 'off', label: '辅助机械臂',  note: '待命 · 末端夹具',   group: '机器人' },
  /* 健康设备 */
  health_mon:   { state: 'on',  label: '健康监测仪',  note: '心率 72 · 正常',    group: '健康' },
  pill_box:     { state: 'on',  label: '智能药盒',    note: '今日已服 1/2',       group: '健康' },
  bp_monitor:   { state: 'off', label: '血压计',      note: '上次: 126/78',      group: '健康' },
  sos:          { state: 'on',  label: '紧急呼叫器',  note: '随身携带 · 待机',   group: '健康' },
  /* 电脑设备 */
  computer:     { state: 'on',  label: '家用电脑',    note: 'Windows · 运行中',  group: '电脑' },
  tablet:       { state: 'off', label: '平板电脑',    note: '充电中 · 92%',      group: '电脑' },
  watch:        { state: 'on',  label: '智能手表',    note: '心率监测中',         group: '电脑' },
};

const MOCK_MEMORIES = [
  '老陈今天上午来访，约好明天 9 点公园下棋',
  '李明通话中提到周末想带孩子来住两天',
  '晨间散步时遇到邻居老王，聊了约 10 分钟',
  '昨天下午浇了阳台的花，状态良好',
];

/* Graph nodes — polar layout (ring + angle from top, clockwise) */
const GRAPH_NODES = [
  { id: 'you',   init: '建', label: '李建国', rel: '',     ring: 0, angle:   0, type: 'center' },
  // Ring 1 — closest family
  { id: 'wife',  init: '芬', label: '王淑芬', rel: '配偶', ring: 1, angle: 250, type: 'fam'    },
  { id: 'son',   init: '明', label: '李明',   rel: '儿子', ring: 1, angle:  15, type: 'fam'    },
  // Ring 2 — extended family + close friends
  { id: 'dilaw', init: '琳', label: '张晓琳', rel: '儿媳', ring: 2, angle:  50, type: 'fam'    },
  { id: 'gdau',  init: '雨', label: '李小雨', rel: '孙女', ring: 2, angle: 110, type: 'fam'    },
  { id: 'chen',  init: '陈', label: '老陈',   rel: '棋友', ring: 2, angle: 190, type: 'fri'    },
  { id: 'doc',   init: '张', label: '张医生', rel: '主治', ring: 2, angle: 305, type: 'med'    },
  // Ring 3 — acquaintances
  { id: 'wang',  init: '王', label: '老王',   rel: '健身', ring: 3, angle:  78, type: 'fri'    },
  { id: 'nurse', init: '李', label: '护士李', rel: '护士', ring: 3, angle: 148, type: 'med'    },
  { id: 'zhao',  init: '赵', label: '赵大妈', rel: '邻居', ring: 3, angle: 228, type: 'fri'    },
  { id: 'comm',  init: '书', label: '王书记', rel: '社区', ring: 3, angle: 330, type: 'med'    },
];

/* ── Helpers ─────────────────────────────────────── */
async function jget(url) {
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(r.status);
    return r.json();
  } catch { return null; }
}
async function jpost(url, body) {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  } catch { return null; }
}

function relTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  const s = (Date.now() - d) / 1000;
  if (s < 60)    return '刚刚';
  if (s < 3600)  return `${Math.floor(s / 60)} 分钟前`;
  if (s < 86400) return `${Math.floor(s / 3600)} 小时前`;
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function esc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function greeting() {
  const h = new Date().getHours();
  if (h < 6)  return '深夜好';
  if (h < 12) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
}

/* ── Tab routing ─────────────────────────────────── */
const tabs  = document.querySelectorAll('.tab');
const views = {
  home:     document.getElementById('view-home'),
  modules:  document.getElementById('view-modules'),
  timeline: document.getElementById('view-timeline'),
  devices:  document.getElementById('view-devices'),
  profile:  document.getElementById('view-profile'),
};

let currentTab = 'home';

function setTab(name) {
  if (!views[name]) return;
  currentTab = name;
  tabs.forEach(t => t.classList.toggle('active', t.dataset.target === name));
  Object.entries(views).forEach(([k, el]) => el.classList.toggle('active', k === name));
  loadTab(name);
}
tabs.forEach(t => t.addEventListener('click', () => setTab(t.dataset.target)));

function loadTab(name) {
  if (name === 'home')     loadHome();
  if (name === 'modules')  loadModules();
  if (name === 'timeline') loadTimeline();
  if (name === 'devices')  loadDevices();
  if (name === 'profile')  loadProfile();
}

/* ── Home ────────────────────────────────────────── */
async function loadHome() {
  // greeting
  document.getElementById('greetingTime').textContent = greeting();
  document.getElementById('greetingName').textContent = PERSONA.name;

  // metrics (real data from PERSONA, with slight random jitter)
  document.getElementById('mSteps').textContent = (PERSONA.health.steps + Math.floor(Math.random() * 80)).toLocaleString('zh');
  document.getElementById('mSleep').textContent = PERSONA.health.sleep;
  document.getElementById('mHr').textContent    = PERSONA.health.hr;

  // try API
  const data = await jget('/api/mobile/home');

  const scene  = data?.scene  || '李建国在客厅休息，环境安静，状态良好';
  const advice = data?.advice || '血压平稳，注意午后适量活动，傍晚可散步 20 分钟';
  document.getElementById('sceneText').textContent    = scene;
  document.getElementById('adviceText').textContent   = advice;
  document.getElementById('lastAnalyzeAt').textContent = relTime(data?.last_updated) || '2 分钟前';
  document.getElementById('analyzeCount').textContent  = data?.stats?.analyze_count ?? 12;

  // alerts
  const alertsEl = document.getElementById('alertsList');
  const alerts   = data?.alerts || [
    { level: 'normal', message: '明天 14:00 社区卫生中心复诊，建议提前 15 分钟出发' },
    { level: 'normal', message: '今日步数已完成每日目标的 68%，继续加油' },
  ];
  alertsEl.innerHTML = alerts.map(a => `
    <div class="list-row">
      <span class="row-kicker">${a.level === 'high' ? '重要' : '提示'}</span>
      <span class="row-text ${a.level === 'high' ? 'amber' : 'muted'}">${esc(a.message)}</span>
    </div>`).join('');

  // today's todos (home tab — show only today/tomorrow items)
  const todayEl = document.getElementById('todayTodos');
  if (todayEl) {
    const todayItems = MOCK_SCHEDULE.filter(s => s.date === '今天' || s.date === '明天');
    todayEl.innerHTML = todayItems.map(s => {
      const cat = SCH_CAT[s.cat] || SCH_CAT.leisure;
      return `
      <div class="sch-card ${s.done ? 'sch-done' : ''}">
        <div class="sch-accent" style="background:var(${cat.accentVar})"></div>
        <div class="sch-body">
          <div class="sch-top">
            <div class="sch-time-wrap">
              <span class="sch-time">${esc(s.time)}</span>
              <span class="sch-date">${esc(s.date)}</span>
            </div>
            <span class="badge ${cat.color}" style="font-size:10px;padding:2px 8px">${s.done ? '已完成' : cat.label}</span>
          </div>
          <p class="sch-title">${esc(s.text)}</p>
          <p class="sch-sub">${esc(s.sub)}</p>
        </div>
        ${s.done ? `<div class="sch-check"></div>` : ''}
      </div>`;
    }).join('');
  }

  // memories
  const memEl = document.getElementById('memoryPreview');
  const mems  = data?.recent_memories?.length ? data.recent_memories : MOCK_MEMORIES;
  memEl.innerHTML = mems.slice(0, 4).map(m => `
    <div class="list-row">
      <span class="row-text muted">${esc(m)}</span>
    </div>`).join('');
}

/* ── Modules ─────────────────────────────────────── */
async function loadModules() {
  const tl = await jget('/api/mobile/timeline');
  const events = tl?.events?.length ? tl.events : MOCK_TIMELINE;
  renderRelationGraph();
  renderSchedule();
  renderGuard(events);
  renderMeeting(events);
  renderFinanceBars();
}

/* relation graph — polar concentric layout */
function renderRelationGraph() {
  const svg = document.getElementById('graphSvg');
  if (!svg) return;

  // fixed viewBox for consistent layout
  const VW = 320, VH = 270;
  const cx  = VW / 2, cy = VH / 2 + 5;
  svg.setAttribute('viewBox', `0 0 ${VW} ${VH}`);
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

  const RING_R  = [0, 56, 100, 130];
  const NODE_R  = [26, 20, 17, 14];

  function polar(ring, angleDeg) {
    const r   = RING_R[ring];
    const rad = (angleDeg - 90) * Math.PI / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  function curvedPath(x1, y1, x2, y2) {
    const mx  = (x1 + x2) / 2;
    const my  = (y1 + y2) / 2;
    const dx  = x2 - x1, dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const bend = 0.12;
    const cpx = mx - (dy / len) * bend * len;
    const cpy = my + (dx / len) * bend * len;
    return `M ${x1.toFixed(1)} ${y1.toFixed(1)} Q ${cpx.toFixed(1)} ${cpy.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`;
  }

  // pre-compute positions
  const pos = {};
  GRAPH_NODES.forEach(n => {
    pos[n.id] = n.ring === 0
      ? { x: cx, y: cy }
      : polar(n.ring, n.angle);
  });

  // ─ orbit rings ─
  const rings = RING_R.slice(1).map(r =>
    `<circle class="graph-ring" cx="${cx}" cy="${cy}" r="${r}"/>`
  ).join('');

  // ─ edges ─
  const edgeClass = { fam: 'gedge-fam', fri: 'gedge-fri', med: 'gedge-med' };
  const edges = GRAPH_NODES.filter(n => n.id !== 'you').map((n, i) => {
    const p  = pos[n.id];
    const ec = edgeClass[n.type] || 'gedge-fri';
    const d  = curvedPath(cx, cy, p.x, p.y);
    return `<path class="gedge ${ec}" d="${d}"
      style="animation: edgeFade .6s ease ${i * 55 + 100}ms both"/>`;
  }).join('');

  // ─ nodes ─
  const ringClass = ['gnode-center', 'gnode-r1', 'gnode-r2', 'gnode-r3'];
  const nodes = GRAPH_NODES.map((n, i) => {
    const { x, y } = pos[n.id];
    const nr    = NODE_R[n.ring];
    const rc    = ringClass[n.ring];
    const delay = i * 60;
    const isCenter = n.ring === 0;

    // text sizing
    const initSize  = isCenter ? 14 : (n.ring === 1 ? 12 : 11);
    const nameSize  = isCenter ? 0  : (n.ring <= 2  ? 9  : 8);
    const relSize   = 8;

    // label fill
    const initFill = isCenter ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.85)';
    const nameFill = n.ring === 1 ? 'rgba(127,164,248,0.95)' : 'rgba(255,255,255,0.42)';
    const relFill  = 'rgba(255,255,255,0.22)';

    const glowEl = isCenter
      ? `<circle class="gnode-glow" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${nr + 6}"/>`
      : '';

    return `
    <g style="animation: nodeIn .5s cubic-bezier(.34,1.56,.64,1) ${delay}ms both">
      ${glowEl}
      <circle class="${rc}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${nr}"/>
      <text text-anchor="middle" dominant-baseline="central"
            x="${x.toFixed(1)}" y="${y.toFixed(1)}"
            font-size="${initSize}" font-family="-apple-system,sans-serif"
            font-weight="700" fill="${initFill}">${esc(n.init)}</text>
      ${nameSize > 0 ? `<text text-anchor="middle"
            x="${x.toFixed(1)}" y="${(y + nr + 8).toFixed(1)}"
            font-size="${nameSize}" font-family="-apple-system,sans-serif"
            font-weight="500" fill="${nameFill}">${esc(n.label)}</text>` : ''}
      ${n.rel ? `<text text-anchor="middle"
            x="${x.toFixed(1)}" y="${(y + nr + 17).toFixed(1)}"
            font-size="${relSize}" font-family="-apple-system,sans-serif"
            fill="${relFill}">${esc(n.rel)}</text>` : ''}
    </g>`;
  }).join('');

  svg.innerHTML = `
    <defs>
      <style>
        @keyframes nodeIn {
          from { opacity:0; transform-box:fill-box; transform-origin:center; transform:scale(.2); }
          to   { opacity:1; transform-box:fill-box; transform-origin:center; transform:scale(1); }
        }
        @keyframes edgeFade {
          from { opacity:0; stroke-dashoffset:80; stroke-dasharray:80; }
          to   { opacity:1; stroke-dashoffset:0; }
        }
        g { transform-box: fill-box; }
      </style>
    </defs>
    ${rings}${edges}${nodes}`;
}

/* ── Schedule category meta — all use single accent ─ */
const SCH_CAT = {
  health:  { label: '健康', color: 'blue', accentVar: '--accent',       fillVar: '--accent-dim' },
  social:  { label: '社交', color: 'blue', accentVar: '--accent',       fillVar: '--accent-dim' },
  leisure: { label: '休闲', color: 'blue', accentVar: '--accent',       fillVar: '--accent-dim' },
  device:  { label: '设备', color: 'blue', accentVar: '--accent',       fillVar: '--accent-dim' },
  ai:      { label: 'AI',   color: 'blue', accentVar: '--accent',       fillVar: '--accent-dim' },
};

function renderSchedule() {
  document.getElementById('scheduleList').innerHTML = MOCK_SCHEDULE.map(s => {
    const cat  = SCH_CAT[s.cat] || SCH_CAT.leisure;
    return `
    <div class="sch-card ${s.done ? 'sch-done' : ''}" data-cat="${s.cat}">
      <div class="sch-accent" style="background:var(${cat.accentVar})"></div>
      <div class="sch-body">
        <div class="sch-top">
          <div class="sch-time-wrap">
            <span class="sch-time">${esc(s.time)}</span>
            <span class="sch-date">${esc(s.date)}</span>
          </div>
          <span class="badge ${cat.color}" style="font-size:10px;padding:2px 8px">${s.done ? '已完成' : cat.label}</span>
        </div>
        <p class="sch-title">${esc(s.text)}</p>
        <p class="sch-sub">${esc(s.sub)}</p>
      </div>
      ${s.done ? `<div class="sch-check"></div>` : ''}
    </div>`;
  }).join('');
}

/* guard */
function renderGuard(events) {
  const risks = events.filter(e =>
    /诈骗|陌生电话|风险|可疑|警告/.test(JSON.stringify(e)));
  const level = Math.min(risks.length, 5);

  document.getElementById('riskNum').textContent = level || 1;
  document.getElementById('riskDesc').textContent =
    level > 2 ? '检测到可疑通话或信息，请注意核实' : '近期无可疑通话或信息，安全状态良好';

  const badge = document.getElementById('guardBadge');
  if (badge) {
    badge.className = `badge ${level > 2 ? 'red' : 'green'}`;
    badge.textContent = level > 2 ? '风险' : '安全';
  }

  const pips = document.querySelectorAll('.risk-pip');
  pips.forEach((p, i) => {
    p.className = 'risk-pip';
    if (i < (level || 1)) {
      p.classList.add('active');
      if (level <= 1) p.classList.add('safe');
    }
  });

  const el = document.getElementById('guardReasons');
  el.innerHTML = risks.length
    ? risks.slice(0, 3).map(e => `
        <div class="reason-item">${esc(e.content || e.text || JSON.stringify(e))}</div>`).join('')
    : `<div class="reason-item" style="color:var(--t3)">过去 7 天无风险事件记录</div>
       <div class="reason-item" style="color:var(--t3)">通话识别模型运行正常</div>`;
}

/* meeting */
function renderMeeting(events) {
  const rows = [
    { kicker: '最近会议',   text: '昨日 19:10 家庭视频通话（3 人，28 分钟）' },
    { kicker: '发言人识别', text: '李建国 · 李明 · 张晓琳（儿媳）' },
    { kicker: '关键决策',   text: '本周六全家来探望；妈妈下月体检提前预约' },
    { kicker: '待办事项',   text: '预约体检 · 订超市配送 · 通知弟弟一起来' },
  ];
  document.getElementById('meetingSummary').innerHTML = rows.map(r => `
    <div class="list-row">
      <span class="row-kicker">${esc(r.kicker)}</span>
      <span class="row-text">${esc(r.text)}</span>
    </div>`).join('');
}

/* finance */
function renderFinanceBars() {
  const cats = [
    { label: '餐饮', pct: 35, cls: 'fill-0', amount: '994' },
    { label: '医疗', pct: 28, cls: 'fill-3', amount: '795' },
    { label: '交通', pct: 18, cls: 'fill-1', amount: '511' },
    { label: '娱乐', pct: 11, cls: 'fill-2', amount: '312' },
    { label: '其他', pct: 8,  cls: 'fill-3', amount: '228' },
  ];
  document.getElementById('financeBars').innerHTML = cats.map(c => `
    <div class="finance-row">
      <span class="finance-cat">${c.label}</span>
      <div class="bar-track"><div class="bar-fill ${c.cls}" style="width:${c.pct}%"></div></div>
      <span class="finance-pct">${c.pct}%</span>
    </div>`).join('');
  document.getElementById('financeAdvice').textContent =
    '本月医疗开支含复诊费用，餐饮及娱乐支出健康，较上月结余增加 8%';
}

/* ── Timeline ────────────────────────────────────── */
async function loadTimeline() {
  const data  = await jget('/api/mobile/timeline');
  const el    = document.getElementById('timelineList');
  const evts  = data?.events?.length ? data.events : MOCK_TIMELINE;
  el.innerHTML = evts.map(e => {
    const tag  = e.tag  || '';
    const text = e.text || e.content || e.description || JSON.stringify(e);
    const time = e.time || relTime(e.created_at) || '';
    return `<div class="tl-item">
      <span class="tl-time">${esc(time)}</span>
      <div class="tl-content">
        ${tag ? `<span class="tl-tag">${esc(tag)}</span>` : ''}
        <span class="tl-text">${esc(text)}</span>
      </div>
    </div>`;
  }).join('');
}

/* ── Devices ─────────────────────────────────────── */
const DEV_ICONS = {
  lights:       'M9 18h6m-3-14v1M12 5a7 7 0 0 1 7 7c0 2.4-1.2 4.5-3 5.8H8C6.2 16.5 5 14.4 5 12a7 7 0 0 1 7-7z',
  lamp:         'M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41M12 7a5 5 0 1 0 0 10A5 5 0 0 0 12 7z',
  ac:           'M8 3v4m8-4v4M3 11h18M5 19h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2z',
  air_purifier: 'M12 2a8 8 0 0 1 8 8c0 5-8 12-8 12S4 15 4 10a8 8 0 0 1 8-8zm0 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  speaker:      'M11 5 6 9H2v6h4l5 4V5zM19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07',
  tv:           'M2 7h20v13H2zM8 2l4 5 4-5',
  fridge:       'M5 2h14a2 2 0 0 1 2 2v18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM3 10h18M12 6v2',
  door_lock:    'M12 3a4 4 0 0 1 4 4v3H8V7a4 4 0 0 1 4-4zM4 10h16v11H4V10zm8 4v3',
  camera:       'M23 7l-7 5 7 5V7zM1 5h15a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H1V5z',
  doorbell:     'M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0',
  sweeper:      'M3 12h1m17 0h1M12 3v1m0 17v1M5.6 5.6l.7.7m11.4-.7-.7.7M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm-9 5h2m14 0h2',
  mopper:       'M3 20h18M12 4v12M8 8l4-4 4 4m-8 8 4 4 4-4',
  robot_arm:    'M4 20v-6l3-6h5l3 6v6M7 14h10M9 10V6a3 3 0 0 1 6 0v4',
  health_mon:   'M22 12h-4l-3 9L9 3l-3 9H2',
  pill_box:     'M9 3h6v4H9zM3 7h18v14H3zM9 7v14m6-14v14',
  bp_monitor:   'M12 2a5 5 0 0 0-5 5v3H5v12h14V10h-2V7a5 5 0 0 0-5-5zm0 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4z',
  sos:          'M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4m0 4h.01',
  computer:     'M2 3h20v13H2zM8 20h8m-4-4v4',
  tablet:       'M5 2h14a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 17a1 1 0 1 0 0-2 1 1 0 0 0 0 2z',
  watch:        'M12 2a7 7 0 1 0 0 14A7 7 0 0 0 12 2zM9 2h6l1 4H8zM9 16h6l1 4H8zM12 6v6l3 2',
};

const DEV_GROUP_ORDER = ['照明','环境','娱乐','厨房','安全','机器人','健康','电脑'];

async function loadDevices() {
  const data    = await jget('/api/mobile/devices');
  const el      = document.getElementById('devicesList');
  const apiDevs = data?.devices || {};

  // merge
  const devs = Object.entries(MOCK_DEVICES).map(([k, meta]) => {
    const api = apiDevs[k];
    return [k, {
      ...meta,
      state: api?.state ?? meta.state,
      note:  api?.value ? `${api.value}` : meta.note,
    }];
  });

  // group by category
  const grouped = {};
  DEV_GROUP_ORDER.forEach(g => { grouped[g] = []; });
  devs.forEach(([k, v]) => {
    if (!grouped[v.group]) grouped[v.group] = [];
    grouped[v.group].push([k, v]);
  });

  let html = '';
  DEV_GROUP_ORDER.forEach(g => {
    if (!grouped[g]?.length) return;
    html += `<div class="dev-group-label">${g}</div>`;
    html += `<div class="dev-group-grid">`;
    html += grouped[g].map(([k, v]) => {
      const on   = v.state === 'on';
      const path = DEV_ICONS[k] || 'M12 12m-8 0a8 8 0 1 0 16 0a8 8 0 1 0-16 0';
      return `<div class="dev-card ${on ? 'is-on' : ''}" id="dc-${k}">
        <div class="dev-icon-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="${path}"/>
          </svg>
        </div>
        <div class="dev-name">${esc(v.label)}</div>
        <div class="dev-state">${on ? (v.note || '已开启') : '已关闭'}</div>
        <button class="dev-toggle" data-key="${k}" data-on="${on}">${on ? '关闭' : '开启'}</button>
      </div>`;
    }).join('');
    html += `</div>`;
  });

  el.innerHTML = html;

  el.querySelectorAll('.dev-toggle').forEach(btn => {
    btn.addEventListener('click', async () => {
      const key  = btn.dataset.key;
      const isOn = btn.dataset.on === 'true';
      MOCK_DEVICES[key].state = isOn ? 'off' : 'on';
      await jpost('/api/mobile/device/action', { device: key, action: isOn ? 'off' : 'on' });
      loadDevices();
    });
  });
}

/* ── Profile ─────────────────────────────────────── */
async function loadProfile() {
  const data = await jget('/api/mobile/profile');
  const p    = data?.profile || {};
  document.getElementById('pName').value  = p.name  || PERSONA.name;
  document.getElementById('pGroup').value = p.group || PERSONA.group;
  document.getElementById('pStyle').value = p.communication_style || PERSONA.style;
  const lvl = p.proactivity_level ?? PERSONA.level;
  document.getElementById('pLevel').value = lvl;
  document.getElementById('pLevelNum').textContent = (+lvl).toFixed(1);
}

document.getElementById('pLevel').addEventListener('input', e => {
  document.getElementById('pLevelNum').textContent = (+e.target.value).toFixed(1);
});

document.getElementById('btnSaveProfile').addEventListener('click', async () => {
  const btn = document.getElementById('btnSaveProfile');
  await jpost('/api/mobile/profile', {
    name:                document.getElementById('pName').value,
    group:               document.getElementById('pGroup').value,
    communication_style: document.getElementById('pStyle').value,
    proactivity_level:   +document.getElementById('pLevel').value,
  });
  btn.textContent = '已保存';
  setTimeout(() => { btn.textContent = '保存修改'; }, 1600);
});

/* ── Refresh triggers ────────────────────────────── */
document.getElementById('btnRefreshHome')     ?.addEventListener('click', loadHome);
document.getElementById('btnRefreshTimeline') ?.addEventListener('click', loadTimeline);
document.getElementById('btnRefreshDevices')  ?.addEventListener('click', loadDevices);

/* ── Story ───────────────────────────────────────── */
document.getElementById('btnReadStory')  ?.addEventListener('click', () =>
  alert('《建国往事》第三章\n\n"三尺讲台四十年"\n\n1973年，25岁的李建国走上讲台，\n这一站，便是四十年。\n\n（15个教学故事，共 12,800 字）'));
document.getElementById('btnShareStory') ?.addEventListener('click', () =>
  alert('已分享至家人设备\n李明、王淑芬、李小雨'));

/* ── Init ────────────────────────────────────────── */
loadHome();
loadTimeline();
loadDevices();

setInterval(() => loadTab(currentTab), 15000);
