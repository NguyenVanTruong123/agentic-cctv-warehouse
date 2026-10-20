/* =========================================================
   VIDEO LIBRARY
   ========================================================= */
const STATUS = {
  none: ['Chưa phân tích', 'st-none'], busy: ['Đang phân tích', 'st-busy'],
  done: ['Đã phân tích', 'st-done'], error: ['Lỗi', 'st-err']
};

function renderLibrary() {
  if (!el.library) return;
  if (el.videoCount) el.videoCount.textContent = state.videos.length;
  el.library.innerHTML = '';
  if (!state.videos.length) {
    el.library.appendChild(makeEl('div', 'empty', 'Chưa có video nào. Nhấn "+ THÊM VIDEO / NẠP VIDEO" để nạp video đầu tiên.'));
    return;
  }
  state.videos.forEach((v) => {
    const item = makeEl('div', 'vitem' + (v.code === state.activeVideo ? ' active' : ''));
    const info = makeEl('div', 'vinfo');
    info.appendChild(makeEl('b', '', v.name));
    const hasFile = !!state.urls[v.code];
    info.appendChild(makeEl('div', 'vmeta',
      `${v.camName} · Nạp: ${new Date(v.createdAt).toLocaleDateString('vi-VN')} · Thời lượng: ${v.duration ? fmtDuration(v.duration) : '—'}` +
      (hasFile ? '' : ' · Tệp chưa có trong phiên này')));
    const [label, cls] = STATUS[v.status] || STATUS.none;
    info.appendChild(makeEl('div', 'vstatus ' + cls, label));
    const acts = makeEl('div', 'vactions');
    [['XEM', () => viewVideo(v.code), ''], ['PHÂN TÍCH AI', () => analyzeVideo(v.code), ''], ['XÓA', () => deleteVideo(v.code), 'btn-danger']]
      .forEach(([t, fn, c]) => {
        const b = makeEl('button', 'btn btn-sm ' + c, t); b.type = 'button';
        b.addEventListener('click', fn); acts.appendChild(b);
      });
    item.append(info, acts);
    el.library.appendChild(item);
  });
}

function viewVideo(code) {
  if (!state.urls[code]) { toast('Tệp video không còn trong phiên này (trang đã tải lại). Hãy nạp lại tệp.', 'warn'); return; }
  state.activeVideo = code;
  renderStage(); renderLibrary();
  el.video.play().catch(() => {});
}

function deleteVideo(code) {
  const v = state.videos.find((x) => x.code === code);
  if (!v || !confirm(`Xóa video "${v.name}" khỏi danh sách?`)) return;
  if (state.urls[code]) { URL.revokeObjectURL(state.urls[code]); delete state.urls[code]; }
  if (state.activeVideo === code) state.activeVideo = null;
  state.videos = state.videos.filter((x) => x.code !== code);
  save(CONFIG.STORAGE_KEY, state.videos);
  renderStage(); renderLibrary();
  toast('Đã xóa video.', 'success');
}
