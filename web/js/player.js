/* =========================================================
   KHUNG XEM VIDEO
   ========================================================= */
function renderStage() {
  clearBoxes();
  const cam = state.cameras.find((c) => c.id === state.selectedCam);
  const vid = state.videos.find((v) => v.code === state.activeVideo);

  if (vid && state.urls[vid.code]) {
    // Đang xem video đã nạp (không phải camera trực tiếp)
    if (el.video.src !== state.urls[vid.code]) el.video.src = state.urls[vid.code];
    el.video.hidden = false; el.placeholder.hidden = true;
    el.srcBadge.textContent = 'VIDEO ĐÃ NẠP'; el.srcBadge.className = 'badge badge-video';
    el.camName.textContent = `${vid.name} · ${vid.camName}`;
    el.osdCode.textContent = vid.code; el.osdState.textContent = 'VIDEO ĐÃ NẠP';
    el.btnPlay.disabled = false;
    updatePlayLabel();
  } else if (cam && cam.videoUrl) {
    // Đang xem camera trực tiếp từ nhà kho có luồng/tệp video thật
    if (!el.video.src || !el.video.src.includes(cam.videoUrl)) {
      el.video.src = cam.videoUrl;
      el.video.muted = true;
      el.video.loop = true;
      el.video.load();
      el.video.play().catch((err) => console.log('Autoplay deferred:', err));
    }
    el.video.hidden = false; el.placeholder.hidden = true;
    el.srcBadge.textContent = 'LIVE CCTV'; el.srcBadge.className = 'badge badge-live';
    el.camName.textContent = cam.name;
    el.osdCode.textContent = cam.id; el.osdState.textContent = 'TRỰC TIẾP (ACTIVE)';
    el.btnPlay.disabled = false;
    updatePlayLabel();
  } else {
    el.video.pause(); el.video.removeAttribute('src'); el.video.load();
    el.video.hidden = true; el.placeholder.hidden = false;
    const live = cam && cam.live;
    el.srcBadge.textContent = live ? 'LIVE' : 'OFFLINE';
    el.srcBadge.className = 'badge ' + (live ? 'badge-live' : 'badge-off');
    el.camName.textContent = cam ? cam.name : 'Chưa chọn camera';
    el.osdCode.textContent = cam ? cam.id : '—';
    el.osdState.textContent = live ? 'LIVE' : 'OFFLINE';
    el.placeholder.textContent = 'Chưa kết nối camera';
    el.btnPlay.disabled = true; el.btnPlay.textContent = 'Phát';
    el.osdTime.textContent = nowTime();
  }
}

function updatePlayLabel() { el.btnPlay.textContent = el.video.paused ? 'Phát' : 'Dừng'; }
function togglePlay() { el.video.paused ? el.video.play() : el.video.pause(); }
function toggleFullscreen() {
  if (document.fullscreenElement) document.exitFullscreen();
  else if (el.stage.requestFullscreen) el.stage.requestFullscreen();
  else toast('Trình duyệt không hỗ trợ phóng to.', 'warn');
}

/* Khung đỏ cảnh báo – toạ độ theo %, dữ liệu do backend cung cấp sau này */
function drawBox(b) {
  const d = makeEl('div', 'bbox');
  Object.assign(d.style, { left: b.x + '%', top: b.y + '%', width: b.w + '%', height: b.h + '%' });
  d.appendChild(makeEl('span', '', b.label || 'Nghi ngờ vi phạm'));
  el.bbox.appendChild(d);
}
function clearBoxes() { el.bbox.innerHTML = ''; }

/* Nhảy tới thời điểm trong video đang phát */
function seekTo(code, seconds) {
  if (typeof seconds !== 'number' || seconds < 0) {
    toast('Thời điểm không hợp lệ.', 'error');
    return;
  }

  // 1. Nếu đang có camera trực tiếp được chọn
  const cam = state.cameras.find((c) => c.id === state.selectedCam);
  if (cam && cam.videoUrl && el.video.src) {
    el.video.currentTime = Math.min(seconds, el.video.duration || seconds);
    el.video.play().catch(() => {});
    toast(`Đã tua camera ${cam.id} tới giây thứ ${seconds} (thời điểm vi phạm)`, 'success');
    return;
  }

  // 2. Nếu là video nạp từ modal
  const vid = state.videos.find((v) => v.code === code);
  if (!vid || !state.urls[code]) {
    toast('Không tìm thấy tệp video.', 'warn');
    return;
  }
  state.activeVideo = code;
  renderStage();
  if (typeof renderLibrary === 'function') renderLibrary();
  const go = () => {
    el.video.currentTime = Math.min(seconds, el.video.duration || seconds);
    el.video.play().catch(() => {});
  };
  el.video.readyState >= 1 ? go() : el.video.addEventListener('loadedmetadata', go, { once: true });
}
