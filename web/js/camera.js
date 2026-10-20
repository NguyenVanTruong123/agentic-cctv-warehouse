/* =========================================================
   CAMERA
   ========================================================= */
async function initCameras() {
  try {
    const res = await fetch(CONFIG.API_CAMERAS);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        state.cameras = data;
        state.selectedCam = data[0].id;
        renderCameras();
        renderStage();
        return;
      }
    }
  } catch (err) {
    console.warn("Khong the tai camera tu backend, dung fallback:", err);
  }

  // Fallback mac dinh cho he thong
  state.cameras = [
    {
      id: 'CAM-03',
      name: 'CAM-03 - Camera Cửa Kho Số 3 - Dock Bốc Dỡ',
      location: 'Nhà Kho Thông Minh - Khu Vực Cửa Số 3',
      live: true,
      videoUrl: '/storage/cctv_videos/dock_boc_do_preview.mp4'
    }
  ];
  state.selectedCam = state.cameras[0].id;
  renderCameras();
  renderStage();
}

function renderCameras() {
  el.camList.innerHTML = '';
  state.cameras.forEach((cam) => {
    const b = makeEl('button', 'btn cam-btn' + (cam.live ? ' on' : '') + (cam.id === state.selectedCam ? ' selected' : ''));
    b.type = 'button';
    b.appendChild(makeEl('span', 'dot'));
    const box = makeEl('span');
    box.appendChild(document.createTextNode(cam.name.split(' - ')[1] ? cam.id + ': ' + cam.name.split(' - ')[1] : cam.name));
    box.appendChild(makeEl('small', '', cam.live ? 'Đang trực tiếp (ACTIVE)' : 'Ngoại tuyến (OFFLINE)'));
    b.appendChild(box);
    b.addEventListener('click', () => selectCamera(cam.id));
    el.camList.appendChild(b);
  });
  // Cập nhật dropdown camera trong form
  el.fCam.innerHTML = '';
  state.cameras.forEach((c) => el.fCam.add(new Option(c.name, c.id)));
  el.fCam.add(new Option('Camera khác', 'OTHER'));
}

function selectCamera(id) {
  state.selectedCam = id;
  state.activeVideo = null;
  renderCameras();
  renderStage();
  if (typeof renderLibrary === 'function') renderLibrary();
}

function addSampleCamera() {
  const n = state.cameras.length + 1;
  const cam = { id: `CAM ${pad(n)}`, name: `CAM ${pad(n)} - Camera mẫu`, live: false };
  state.cameras.push(cam);
  save(CONFIG.CAM_KEY, state.cameras);
  selectCamera(cam.id);
  toast(`Đã thêm ${cam.name} (chưa kết nối nguồn).`, 'success');
}
