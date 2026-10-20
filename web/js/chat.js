/* =========================================================
   PHÂN TÍCH AI (chưa có backend thì chỉ báo trạng thái)
   ========================================================= */
function setBotStatus(text, cls = '') {
  el.botStatus.textContent = text;
  el.botStatus.className = 'chip ' + cls;
}

async function analyzeVideo(code) {
  const v = state.videos.find((x) => x.code === code);
  if (!v) return;
  if (!CONFIG.API_URL) {
    addMessage('system', `Chưa kết nối backend AI nên chưa thể phân tích video "${v.name}". Hãy cấu hình CONFIG.API_URL trong script.js.`);
    setBotStatus('Lỗi kết nối', 'error');
    toast('Backend AI chưa được kết nối.', 'warn');
    return;
  }
  // Móc nối backend: chỉ gửi khi người dùng chủ động bấm phân tích
  v.status = 'busy'; save(CONFIG.STORAGE_KEY, state.videos); renderLibrary();
  setBotStatus('Đang phân tích video', 'busy');
  try {
    const fd = new FormData();
    fd.append('meta', JSON.stringify(v));
    if (state.urls[code]) fd.append('file', await (await fetch(state.urls[code])).blob(), v.fileName);
    const res = await fetch(CONFIG.API_URL, { method: 'POST', body: fd });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();             // dự kiến: {summary, events:[{id,time,type,level,status,evidenceUrl}]}
    v.status = 'done';
    addMessage('bot', data.summary || 'Đã phân tích xong.', { events: data.events || [], code });
    setBotStatus('Hoàn thành', 'done');
  } catch (err) {
    v.status = 'error';
    addMessage('system', 'Lỗi khi phân tích: ' + err.message);
    setBotStatus('Lỗi kết nối', 'error');
  }
  save(CONFIG.STORAGE_KEY, state.videos); renderLibrary();
}

/* =========================================================
   CHAT
   ========================================================= */
const ROLE_LABEL = { user: 'Quản lý', bot: 'AI', system: 'Hệ thống' };

function addMessage(role, text, opts = {}) {
  const m = { role, text, time: nowTime(), sim: !!opts.sim, events: opts.events || null, code: opts.code || null, noResult: !!opts.noResult };
  state.chat.push(m);
  save(CONFIG.CHAT_KEY, state.chat.map(({ events, ...rest }) => rest)); // không lưu dữ liệu sự kiện nặng
  renderMessage(m);
}

function renderMessage(m) {
  const box = makeEl('div', 'msg ' + m.role + (m.events && m.events.some((e) => e.level === 'Cao') ? ' alert' : ''));
  const who = makeEl('div', 'who');
  who.appendChild(makeEl('span', '', ROLE_LABEL[m.role]));
  who.appendChild(makeEl('span', 'mono', m.time));
  if (m.sim) who.appendChild(makeEl('span', 'sim-tag', 'MÔ PHỎNG – KHÔNG PHẢI KẾT QUẢ AI THẬT'));
  box.append(who, document.createTextNode(m.text));
  if (m.noResult) box.appendChild(buildResultCard(null));
  (m.events || []).forEach((e) => box.appendChild(buildResultCard(e, m.code)));
  el.messages.appendChild(box);
  el.messages.scrollTop = el.messages.scrollHeight;       // tự cuộn xuống tin mới nhất
}

/* Thẻ kết quả; e = null nghĩa là chưa có kết quả phân tích */
function buildResultCard(e, code) {
  const card = makeEl('div', 'result-card' + (e && e.status !== 'Không đủ bằng chứng' ? ' alert' : ''));
  if (!e) {
    card.appendChild(makeEl('div', 'evidence', 'CHƯA CÓ KẾT QUẢ PHÂN TÍCH'));
    return card;
  }
  const dl = makeEl('dl');
  [['Mã sự kiện', e.id], ['Video / camera', e.source || '—'], ['Thời điểm', typeof e.time === 'number' ? fmtDuration(e.time) : '—'],
   ['Loại vi phạm', e.type], ['Mức cảnh báo', e.level], ['Trạng thái', e.status]]
    .forEach(([k, v]) => { dl.appendChild(makeEl('dt', '', k)); dl.appendChild(makeEl('dd', '', v)); });
  card.appendChild(dl);
  if (e.evidenceUrl) {
    const img = makeEl('img'); img.src = e.evidenceUrl; img.alt = 'Ảnh bằng chứng'; img.style.width = '100%';
    card.appendChild(img);
  } else {
    card.appendChild(makeEl('div', 'evidence', 'Không có ảnh bằng chứng (backend chưa cung cấp)'));
  }
  const b = makeEl('button', 'btn btn-sm', 'XEM TẠI THỜI ĐIỂM VI PHẠM'); b.type = 'button';
  b.addEventListener('click', () => {
    if (!code) { toast('Sự kiện mô phỏng không gắn với video thật.', 'warn'); return; }
    seekTo(code, e.time);
    if (e.box) drawBox(e.box);
  });
  card.appendChild(b);
  return card;
}

/* Phản hồi mô phỏng – luôn gắn nhãn MÔ PHỎNG */
function simulatedReply(text) {
  const t = text.toLowerCase();
  const vid = state.videos.find((v) => v.code === state.activeVideo);
  if (/bằng chứng|ảnh/.test(t)) {
    return { text: 'Đây chỉ là thẻ kết quả mẫu để kiểm tra giao diện. Chưa có phân tích thật nên không có ảnh bằng chứng.',
      events: [{ id: 'DEMO-001', source: vid ? vid.name : 'Chưa chọn video', time: 83, type: 'Không đội mũ bảo hộ (mẫu)', level: 'Cao', status: 'Nghi ngờ' }], code: null };
  }
  if (/đội mũ|mũ bảo hộ|kiểm tra|nguy hiểm|liệt kê|tóm tắt/.test(t)) {
    if (!vid) return { text: 'Chưa chọn video. Hãy chọn một video trong VIDEO LIBRARY, sau đó nhấn PHÂN TÍCH AI.', noResult: true };
    return { text: `Đã chọn video "${vid.name}". Backend AI chưa được kết nối nên chưa có kết quả phân tích.`, noResult: true };
  }
  return { text: 'Tôi có thể hỗ trợ kiểm tra vi phạm an toàn trên video đã nạp. Bạn muốn kiểm tra nội dung nào?' };
}

function sendMessage() {
  const text = el.chatInput.value.trim();
  if (!text) return;
  el.chatInput.value = '';
  addMessage('user', text);
  setBotStatus('Đang xử lý (mô phỏng)', 'busy');
  el.btnSend.disabled = true;
  if (CONFIG.API_URL) { /* TODO: gọi backend chat/LangGraph tại đây */ }
  setTimeout(() => {
    const r = simulatedReply(text);
    addMessage('bot', r.text, { sim: true, events: r.events, code: r.code, noResult: r.noResult });
    setBotStatus('Hoàn thành', 'done');
    el.btnSend.disabled = false;
    setTimeout(() => setBotStatus('Sẵn sàng'), 2500);
  }, 600);
}

function clearChat() {
  if (!state.chat.length || !confirm('Xóa toàn bộ lịch sử chat?')) return;
  state.chat = []; save(CONFIG.CHAT_KEY, []);
  el.messages.innerHTML = '';
  addMessage('system', 'Đã xóa lịch sử chat.');
}

function initChat() {
  state.chat = load(CONFIG.CHAT_KEY, []);
  if (!state.chat.length) {
    addMessage('system', 'Frontend demo. Chưa kết nối camera và backend AI; mọi phản hồi của chatbot là mô phỏng và được gắn nhãn rõ ràng.');
  } else {
    state.chat.forEach(renderMessage);
  }
}
