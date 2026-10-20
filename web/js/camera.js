/* =========================================================
   CAMERA
   ========================================================= */
function initCameras() {
  state.cameras = load(CONFIG.CAM_KEY, null) || [
    { id: 'CAM 01', name: 'CAM 01 - Khu bốc dỡ (Xưởng A)', live: false },
    { id: 'CAM 02', name: 'CAM 02 - Lối đi', live: false },
    { id: 'CAM 03', name: 'CAM 03 - Khu sản xuất', live: false }
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
    box.appendChild(makeEl('small', '', cam.live ? 'Đã kết nối' : 'Chưa kết nối'));
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
  renderLibrary();
}

function addSampleCamera() {
  const n = state.cameras.length + 1;
  const cam = { id: `CAM ${pad(n)}`, name: `CAM ${pad(n)} - Camera mẫu`, live: false };
  state.cameras.push(cam);
  save(CONFIG.CAM_KEY, state.cameras);
  selectCamera(cam.id);
  toast(`Đã thêm ${cam.name} (chưa kết nối nguồn).`, 'success');
}
