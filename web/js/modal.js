/* =========================================================
   MODAL NẠP VIDEO
   ========================================================= */
function openModal() {
  resetForm();
  el.modal.hidden = false;
  el.fName.focus();
}
function isFormDirty() {
  return !!(el.fName.value || el.fCode.value || el.fArea.value || el.fDesc.value || el.fDate.value || el.fTime.value || state.modalFile);
}
function closeModal(force = false) {
  if (!force && isFormDirty() && !confirm('Dữ liệu chưa lưu sẽ bị mất. Đóng form?')) return;
  clearModalFile();
  el.modal.hidden = true;
}
function resetForm() {
  el.form.reset(); clearModalFile();
  el.errName.textContent = ''; el.fName.classList.remove('invalid');
  el.fDate.value = new Date().toISOString().slice(0, 10);
}

function clearModalFile() {
  if (state.modalUrl) URL.revokeObjectURL(state.modalUrl);
  Object.assign(state, { modalUrl: null, modalFile: null, modalMeta: null });
  el.fFile.value = '';
  el.preview.removeAttribute('src'); el.preview.hidden = true;
  el.fileMeta.hidden = true; el.btnRemoveFile.hidden = true; el.errFile.textContent = '';
}

function handleFileChosen(file) {
  if (!file) return;
  el.errFile.textContent = '';
  if (!file.type.startsWith('video/')) {
    clearModalFile();
    el.errFile.textContent = 'Tệp không hợp lệ: chỉ chấp nhận video (MP4, WebM, MOV...).';
    toast('Tệp không phải video.', 'error');
    return;
  }
  if (state.modalUrl) URL.revokeObjectURL(state.modalUrl);
  state.modalFile = file;
  state.modalUrl = URL.createObjectURL(file);
  state.modalMeta = { duration: null };
  el.mName.textContent = file.name;
  el.mSize.textContent = fmtSize(file.size);
  el.mFormat.textContent = file.type || file.name.split('.').pop().toUpperCase();
  el.mDur.textContent = 'Đang đọc...';
  el.fileMeta.hidden = false; el.btnRemoveFile.hidden = false;
  el.preview.hidden = false; el.preview.src = state.modalUrl;
  if (!el.fName.value) el.fName.value = file.name.replace(/\.[^.]+$/, '');
}

/* Đọc metadata / báo lỗi nếu trình duyệt không phát được định dạng */
el.preview.addEventListener('loadedmetadata', () => {
  if (!state.modalMeta) return;
  state.modalMeta.duration = el.preview.duration;
  el.mDur.textContent = fmtDuration(el.preview.duration);
});
el.preview.addEventListener('error', () => {
  if (!state.modalFile) return;
  el.mDur.textContent = 'Không đọc được';
  el.errFile.textContent = 'Trình duyệt không phát được định dạng này. Có thể vẫn lưu, nhưng không xem trước được.';
});

function validateForm() {
  let ok = true;
  el.errName.textContent = ''; el.fName.classList.remove('invalid');
  if (!el.fName.value.trim()) {
    el.errName.textContent = 'Vui lòng nhập tên video.'; el.fName.classList.add('invalid'); el.fName.focus(); ok = false;
  }
  if (!state.modalFile) { el.errFile.textContent = 'Vui lòng chọn một tệp video.'; ok = false; }
  return ok;
}

/* Lưu video; trả về mã video hoặc null nếu không hợp lệ */
function saveVideo() {
  if (!validateForm()) return null;
  let code = el.fCode.value.trim() || 'VID-' + Date.now().toString(36).toUpperCase();
  if (state.videos.some((v) => v.code === code)) {
    el.fCode.focus(); toast(`Mã video "${code}" đã tồn tại.`, 'error'); return null;
  }
  const camId = el.fCam.value;
  const camObj = state.cameras.find((c) => c.id === camId);
  const meta = {
    code, name: el.fName.value.trim(), camId, camName: camObj ? camObj.name : 'Camera khác',
    area: el.fArea.value.trim(), date: el.fDate.value, time: el.fTime.value,
    desc: el.fDesc.value.trim(), type: el.fType.value,
    fileName: state.modalFile.name, size: state.modalFile.size, format: state.modalFile.type,
    duration: state.modalMeta && isFinite(state.modalMeta.duration) ? state.modalMeta.duration : null,
    createdAt: new Date().toISOString(), status: 'none'
  };
  // Chuyển URL tạm từ modal sang thư viện (không revoke ở đây)
  state.urls[code] = state.modalUrl;
  state.modalUrl = null; state.modalFile = null;
  state.videos.unshift(meta);
  save(CONFIG.STORAGE_KEY, state.videos);
  closeModal(true);
  renderLibrary();
  toast(`Đã lưu video "${meta.name}".`, 'success');
  return code;
}
