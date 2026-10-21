/* ---------- Tiện ích ---------- */
const pad = (n) => String(n).padStart(2, '0');
const nowTime = () => { const d = new Date(); return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
function fmtDuration(s) {
  if (!isFinite(s)) return '—';
  s = Math.floor(s);
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s % 3600 / 60))}:${pad(s % 60)}`;
}
function fmtSize(b) {
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
  if (b < 1024 ** 3) return (b / 1024 / 1024).toFixed(1) + ' MB';
  return (b / 1024 ** 3).toFixed(2) + ' GB';
}
function save(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); }
  catch (e) { toast('Không lưu được dữ liệu vào trình duyệt.', 'error'); }
}
function load(key, fallback) {
  try { const v = JSON.parse(localStorage.getItem(key)); return v ?? fallback; }
  catch (e) { return fallback; }
}
function toast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  el.toasts.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}
function makeEl(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

/* ---------- Đồng hồ ---------- */
function tickClock() {
  el.clock.textContent = nowTime();
  if (!state.activeVideo) el.osdTime.textContent = nowTime();
}

/* ---------- Bộ giải mã Markdown sang HTML an toàn & gọn gàng ---------- */
function formatMarkdown(text) {
  if (!text) return '';
  // 1. Escape HTML chống XSS an toàn
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // 2. Thu gọn nhiều dòng trống liên tiếp thành tối đa 1 dòng trống
  safe = safe.replace(/\n{3,}/g, '\n\n');

  // 3. Chuyển tiêu đề ### và ##
  safe = safe.replace(/^###\s+(.+)$/gm, '<div style="font-weight:700;color:#93c5fd;margin:6px 0 2px;">$1</div>');
  safe = safe.replace(/^##\s+(.+)$/gm, '<div style="font-weight:700;font-size:14px;color:#60a5fa;margin:8px 0 3px;">$1</div>');

  // 4. Chuyển **in đậm** thành <strong>
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#ffffff;font-weight:600;">$1</strong>');

  // 5. Chuyển *in nghiêng* thành <em>
  safe = safe.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // 6. Chuyển `code` thành khối mã nổi bật
  safe = safe.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08);padding:1px 5px;border-radius:3px;font-family:monospace;color:#fde047;">$1</code>');

  // 7. Chuyển Markdown Table (| ... |) thành HTML Table chuẩn đẹp
  safe = safe.replace(/((?:^\|.+?\|\s*(?:\r?\n|$))+)/gm, (match) => {
    const rawLines = match.trim().split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (rawLines.length < 2) return match;
    const sepIndex = rawLines.findIndex(l => /^\|[\s\-:|]+\|$/.test(l));
    if (sepIndex === -1) return match;

    const headerLines = rawLines.slice(0, sepIndex);
    const bodyLines = rawLines.slice(sepIndex + 1);

    const parseRow = (line) => {
      const trimmed = line.replace(/^\||\|$/g, '');
      return trimmed.split('|').map(c => c.trim());
    };

    let html = '<div class="chat-table-wrapper" style="overflow-x:auto;margin:8px 0;border-radius:6px;border:1px solid rgba(255,255,255,0.12);box-shadow:0 2px 8px rgba(0,0,0,0.25);"><table class="chat-table" style="width:100%;border-collapse:collapse;font-size:12.5px;background:rgba(15,23,42,0.65);">';

    if (headerLines.length > 0) {
      html += '<thead>';
      headerLines.forEach(hl => {
        html += '<tr style="background:rgba(30,41,59,0.95);border-bottom:1px solid rgba(255,255,255,0.15);">';
        parseRow(hl).forEach(cell => {
          html += `<th style="padding:7px 10px;color:#93c5fd;font-weight:600;text-align:left;white-space:nowrap;">${cell}</th>`;
        });
        html += '</tr>';
      });
      html += '</thead>';
    }

    if (bodyLines.length > 0) {
      html += '<tbody>';
      bodyLines.forEach((bl, idx) => {
        const bg = idx % 2 === 0 ? 'background:rgba(255,255,255,0.02);' : 'background:transparent;';
        html += `<tr style="${bg}border-bottom:1px solid rgba(255,255,255,0.06);">`;
        parseRow(bl).forEach((cell, cIdx) => {
          const colStyle = cIdx === 0 ? 'font-weight:600;color:#f8fafc;width:28%;white-space:nowrap;' : 'color:#cbd5e1;';
          html += `<td style="padding:6px 10px;vertical-align:top;${colStyle}">${cell}</td>`;
        });
        html += '</tr>';
      });
      html += '</tbody>';
    }

    html += '</table></div>';
    return html;
  });

  // 8. Gạch đầu dòng: - item hoặc * item thành flex list item gọn gàng
  safe = safe.replace(/^[\s]*[-•*]\s+(.+)$/gm, '<div class="chat-li"><span class="chat-bullet">•</span><span>$1</span></div>');

  // 9. Dọn dẹp khoảng cách thừa quanh thẻ block (div, table, wrapper)
  safe = safe.replace(/<\/div>\n/g, '</div>');
  safe = safe.replace(/\n<\/div>/g, '</div>');
  safe = safe.replace(/\n\n/g, '<div style="height:6px;"></div>');
  safe = safe.replace(/\n/g, '<br>');

  return safe;
}
