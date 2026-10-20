/* =========================================================
   Hệ thống giám sát camera AI – frontend demo
   - Metadata video lưu localStorage; tệp video chỉ tồn tại
     trong phiên hiện tại (URL tạm từ URL.createObjectURL).
   - Chưa có backend: mọi phản hồi chat là MÔ PHỎNG và được gắn nhãn.
   ========================================================= */

/* ---------- Cấu hình: điền URL khi đã có backend Python / LangGraph ---------- */
const CONFIG = {
  API_URL: '',            // ví dụ: 'http://localhost:8000/api/analyze'
  STORAGE_KEY: 'cctv_videos_v1',
  CAM_KEY: 'cctv_cameras_v1',
  CHAT_KEY: 'cctv_chat_v1'
};

/* ---------- Trạng thái ứng dụng ---------- */
const state = {
  cameras: [],          // {id, name, live:false}
  videos: [],           // metadata video (lưu localStorage)
  urls: {},             // code -> object URL (chỉ trong phiên)
  selectedCam: null,
  activeVideo: null,    // code video đang phát
  chat: [],
  modalUrl: null,       // object URL xem trước trong modal
  modalFile: null,
  modalMeta: null
};

const $ = (id) => document.getElementById(id);
const el = {
  clock: $('clock'), backendChip: $('backendChip'), srcBadge: $('srcBadge'), camName: $('camName'),
  osdTime: $('osdTime'), osdCode: $('osdCode'), osdState: $('osdState'), btnPlay: $('btnPlay'),
  btnFull: $('btnFull'), stage: $('stage'), video: $('mainVideo'), placeholder: $('placeholder'),
  bbox: $('bboxLayer'), camList: $('camList'), btnAddCam: $('btnAddCam'), btnOpenModal: $('btnOpenModal'),
  videoCount: $('videoCount'), library: $('library'), messages: $('messages'), chatInput: $('chatInput'),
  btnSend: $('btnSend'), btnClearChat: $('btnClearChat'), botStatus: $('botStatus'),
  modal: $('modal'), form: $('videoForm'), btnClose: $('btnCloseModal'), btnCancel: $('btnCancel'),
  btnReset: $('btnReset'), btnSaveAnalyze: $('btnSaveAnalyze'), btnSave: $('btnSave'),
  fName: $('fName'), fCode: $('fCode'), fCam: $('fCam'), fArea: $('fArea'), fDate: $('fDate'),
  fTime: $('fTime'), fType: $('fType'), fDesc: $('fDesc'), fFile: $('fFile'), btnPick: $('btnPick'),
  btnRemoveFile: $('btnRemoveFile'), errName: $('errName'), errFile: $('errFile'), fileMeta: $('fileMeta'),
  mName: $('mName'), mSize: $('mSize'), mFormat: $('mFormat'), mDur: $('mDur'), preview: $('previewVideo'),
  toasts: $('toasts')
};
