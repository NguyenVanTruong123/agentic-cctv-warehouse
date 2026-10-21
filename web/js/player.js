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

/* Nhảy tới thời điểm trong video đang phát & tự động chuyển camera/phiên video */
function seekTo(code, seconds, videoUrl) {
  if (typeof seconds !== 'number' || seconds < 0) {
    toast('Thời điểm không hợp lệ.', 'error');
    return;
  }

  // 1. Tự động đồng bộ Camera nếu code được chỉ định khác camera đang chọn
  const targetCamId = code || state.selectedCam;
  const cam = state.cameras.find((c) => c.id === targetCamId);

  if (cam) {
    if (state.selectedCam !== cam.id || state.activeVideo) {
      state.selectedCam = cam.id;
      state.activeVideo = null;
      if (typeof renderCameras === 'function') renderCameras();
    }

    // Nếu có phiên video cụ thể được yêu cầu (hôm nay vs hôm qua)
    if (videoUrl) {
      cam.videoUrl = videoUrl;
    }

    const finalUrl = cam.videoUrl;
    if (finalUrl) {
      el.video.hidden = false;
      el.placeholder.hidden = true;
      el.srcBadge.textContent = 'TRÍCH XUẤT VI PHẠM';
      el.srcBadge.className = 'badge badge-video';
      el.camName.textContent = `${cam.name} · Tua vi phạm`;
      el.osdCode.textContent = cam.id;
      el.osdState.textContent = `VI PHẠM (${seconds}s)`;
      el.btnPlay.disabled = false;

      const performJump = () => {
        el.video.currentTime = Math.min(seconds, el.video.duration || seconds);
        el.video.play().catch(() => {});
        updatePlayLabel();
        toast(`Đã tự động chuyển ${cam.id} & tua tới giây thứ ${seconds} (vi phạm)`, 'success');
      };

      if (!el.video.src || !el.video.src.includes(finalUrl)) {
        el.video.src = finalUrl;
        el.video.muted = true;
        el.video.loop = true;
        el.video.load();
        if (el.video.readyState >= 1) {
          performJump();
        } else {
          el.video.addEventListener('loadedmetadata', performJump, { once: true });
        }
      } else {
        performJump();
      }
      return;
    }
  }

  // 2. Nếu là video nạp từ modal (thư viện tải lên)
  const vid = state.videos.find((v) => v.code === code);
  if (vid && state.urls[code]) {
    state.activeVideo = code;
    renderStage();
    if (typeof renderLibrary === 'function') renderLibrary();
    const go = () => {
      el.video.currentTime = Math.min(seconds, el.video.duration || seconds);
      el.video.play().catch(() => {});
      updatePlayLabel();
      toast(`Đã tua video ${vid.name} tới giây thứ ${seconds}`, 'success');
    };
    el.video.readyState >= 1 ? go() : el.video.addEventListener('loadedmetadata', go, { once: true });
    return;
  }

  toast('Không tìm thấy nguồn video phù hợp.', 'warn');
}
