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

function init() {
  state.videos = load(CONFIG.STORAGE_KEY, []).map((v) => (v.status === 'busy' ? { ...v, status: 'none' } : v));
  initCameras();
  renderLibrary();
  initChat();
  bindEvents();
  el.backendChip.textContent = CONFIG.API_URL ? 'Backend AI: đã cấu hình' : 'Backend AI: chưa kết nối';
  tickClock(); setInterval(tickClock, 1000);
}
init();
