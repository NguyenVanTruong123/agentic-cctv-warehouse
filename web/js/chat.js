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

/* Thẻ kết quả hiển thị bằng chứng vi phạm */
function buildResultCard(e, code) {
  const card = makeEl('div', 'result-card alert');
  if (!e) {
    card.appendChild(makeEl('div', 'evidence', 'CHƯA CÓ KẾT QUẢ PHÂN TÍCH'));
    return card;
  }
  const dl = makeEl('dl');
  [['Mã sự kiện', e.id], ['Video / camera', e.source || '—'], ['Thời điểm', typeof e.time === 'number' ? fmtDuration(e.time) + ` (giây thứ ${e.time})` : '—'],
   ['Loại vi phạm', e.type], ['Mức cảnh báo', e.level], ['Trạng thái', e.status]]
    .forEach(([k, v]) => { dl.appendChild(makeEl('dt', '', k)); dl.appendChild(makeEl('dd', '', v)); });
  card.appendChild(dl);
  if (e.evidenceUrl) {
    const img = makeEl('img');
    img.src = e.evidenceUrl;
    img.alt = 'Ảnh bằng chứng vi phạm';
    img.style.width = '100%';
    img.style.borderRadius = '4px';
    img.style.marginTop = '6px';
    img.style.cursor = 'zoom-in';
    img.title = 'Bấm để mở ảnh bằng chứng gốc';
    img.onclick = () => window.open(e.evidenceUrl, '_blank');
    card.appendChild(img);
  } else {
    card.appendChild(makeEl('div', 'evidence', 'Không có ảnh bằng chứng'));
  }
  const b = makeEl('button', 'btn btn-sm btn-primary', '▶ XEM TẠI THỜI ĐIỂM VI PHẠM (TUA VIDEO)');
  b.type = 'button';
  b.style.marginTop = '8px';
  b.addEventListener('click', () => {
    seekTo(code || state.selectedCam, e.time);
  });
  card.appendChild(b);
  return card;
}

/* Phản hồi mô phỏng – fallback khi không có backend */
function simulatedReply(text) {
  const t = text.toLowerCase();
  const vid = state.videos.find((v) => v.code === state.activeVideo);
  if (/bằng chứng|ảnh/.test(t)) {
    return { text: 'Đây chỉ là thẻ kết quả mẫu để kiểm tra giao diện.',
      events: [{ id: 'DEMO-001', source: vid ? vid.name : 'CAM-03', time: 6, type: 'Đi vào vùng cấm xe nâng', level: 'Cao', status: 'Chưa xử lý', evidenceUrl: '/storage/evidence/EVT-20261019-001.jpg' }], code: 'CAM-03' };
  }
  return { text: 'Tôi là Trợ Lý Giám Sát An Toàn Kho. Hãy hỏi tôi về tình hình vi phạm ở các camera.' };
}

async function sendMessage() {
  const text = el.chatInput.value.trim();
  if (!text) return;
  el.chatInput.value = '';
  addMessage('user', text);
  setBotStatus('AI đang suy luận & tra cứu...', 'busy');
  el.btnSend.disabled = true;

  try {
    const res = await fetch(CONFIG.API_CHAT || '/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        active_camera: state.selectedCam || 'CAM-03'
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Lỗi máy chủ (${res.status})`);
    }

    const data = await res.json();
    setBotStatus('Hoàn thành', 'done');

    // Hiển thị tin nhắn trả lời từ LangGraph Agent
    addMessage('bot', data.reply, {
      sim: false,
      events: data.events,
      code: state.selectedCam
    });

    // Nếu Agent yêu cầu tua video đến giây vi phạm
    if (typeof data.seek_second === 'number' && data.seek_second >= 0) {
      seekTo(state.selectedCam, data.seek_second);
    }

  } catch (err) {
    console.warn('Lỗi gọi chat API backend, sử dụng mô phỏng fallback:', err);
    // Fallback neu Backend chua chay
    const r = simulatedReply(text);
    addMessage('bot', r.text + ` (Lưu ý: Không gọi được Backend API: ${err.message})`, {
      sim: true,
      events: r.events,
      code: r.code
    });
    setBotStatus('Lỗi kết nối', 'error');
  } finally {
    el.btnSend.disabled = false;
    setTimeout(() => setBotStatus('Sẵn sàng'), 3000);
  }
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
    addMessage('system', 'Chào bạn! Tôi là Trợ Lý Giám Sát An Toàn Kho Thông Minh (Smart Warehouse AI Agent). Bạn có thể hỏi tôi về các vi phạm an toàn, tra cứu quy định và yêu cầu tua video tới thời điểm vi phạm.');
  } else {
    state.chat.forEach(renderMessage);
  }
}
