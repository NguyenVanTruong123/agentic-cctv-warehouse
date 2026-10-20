/* =========================================================
   GẮN SỰ KIỆN & KHỞI TẠO
   ========================================================= */
function bindEvents() {
  el.btnPlay.addEventListener('click', togglePlay);
  el.btnFull.addEventListener('click', toggleFullscreen);
  if (el.btnAddCam) el.btnAddCam.addEventListener('click', addSampleCamera);
  el.video.addEventListener('play', updatePlayLabel);
  el.video.addEventListener('pause', updatePlayLabel);
  el.video.addEventListener('timeupdate', () => {
    el.osdTime.textContent = `${fmtDuration(el.video.currentTime)} / ${fmtDuration(el.video.duration)}`;
  });

  el.btnOpenModal.addEventListener('click', openModal);
  el.btnClose.addEventListener('click', () => closeModal());
  el.btnCancel.addEventListener('click', () => closeModal());
  el.btnReset.addEventListener('click', resetForm);
  el.btnPick.addEventListener('click', () => el.fFile.click());
  el.fFile.addEventListener('change', () => handleFileChosen(el.fFile.files[0]));
  el.btnRemoveFile.addEventListener('click', clearModalFile);
  el.form.addEventListener('submit', (e) => { e.preventDefault(); saveVideo(); });
  el.btnSaveAnalyze.addEventListener('click', () => { const c = saveVideo(); if (c) analyzeVideo(c); });
  el.modal.addEventListener('mousedown', (e) => { if (e.target === el.modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !el.modal.hidden) closeModal(); });

  el.btnSend.addEventListener('click', sendMessage);
  el.btnClearChat.addEventListener('click', clearChat);
  el.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendMessage(); }
  });

  // Thu hồi URL tạm khi đóng trang
  window.addEventListener('beforeunload', () => Object.values(state.urls).forEach((u) => URL.revokeObjectURL(u)));
}

async function checkBackend() {
  try {
    const res = await fetch(CONFIG.API_HEALTH || '/api/v1/health');
    if (res.ok) {
      const data = await res.json();
      el.backendChip.textContent = `Backend AI: Đã kết nối (${data.active_cameras} cam)`;
      el.backendChip.className = 'chip';
      el.backendChip.style.background = '#065f46';
      el.backendChip.style.color = '#34d399';
    } else {
      el.backendChip.textContent = 'Backend AI: Lỗi máy chủ';
      el.backendChip.className = 'chip chip-warn';
    }
  } catch (e) {
    el.backendChip.textContent = 'Backend AI: Chưa kết nối';
    el.backendChip.className = 'chip chip-warn';
  }
}

async function init() {
  state.videos = load(CONFIG.STORAGE_KEY, []).map((v) => (v.status === 'busy' ? { ...v, status: 'none' } : v));
  await initCameras();
  if (typeof renderLibrary === 'function') renderLibrary();
  initChat();
  bindEvents();
  checkBackend();
  tickClock(); setInterval(tickClock, 1000);
}
init();
