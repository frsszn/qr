import streamlit as st
import cv2
import os
import pandas as pd
import numpy as np
import tempfile
import pyzxing 
from ultralytics import YOLO
from pyzbar.pyzbar import decode as pyzbar_decode
from pyzxing import BarCodeReader

os.environ["HOME"] = tempfile.gettempdir()

# ====================== STREAMLIT PAGE CONFIG ======================
st.set_page_config(
    page_title="Barcode Detector App",
    page_icon="📦",
    layout="wide"
)

# ====================== CONFIG ======================
resize_factor = 2.5
padding = 20
save_failed = True
output_csv = "decoded_result.csv"

# ====================== LOAD MODEL ======================
@st.cache_resource
def load_model():
    return YOLO("model/best.pt")

model = load_model()

zxing_reader = BarCodeReader()



# ====== THEME DAN CENTERING ======
def centered_content(content_func):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        content_func()

st.markdown("""
    <style>
    div[data-baseweb="tab-list"] {
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

tab_about, tab_detect = st.tabs(["ℹ️ About", "🔍 Detection"])

# ====== ABOUT ======
with tab_about:
    centered_content(lambda: (
        st.title("📦 BarSight: a Barcode and QRCode Decoder App"),
        st.image(
            "https://compote.slate.com/images/6b8aaea8-f787-4ce3-a039-5aa0f003ba07.jpeg?crop=1560%2C1040%2Cx0%2Cy0"
        ),
        st.write("""
        Aplikasi ini menggunakan **YOLOv8**, **ZXing (pyzxing)**, dan **Pyzbar**  
        untuk mendeteksi dan membaca *barcode* atau *QR code* dari gambar.

        **Pipeline utama:**
        1. YOLOv8 mendeteksi posisi barcode.  
        2. ROI hasil deteksi diproses dengan preprocessing.  
        3. ZXing mencoba decode.  
        4. Jika gagal, fallback ke Pyzbar.  
        5. Hasil akhir bisa diunduh sebagai CSV.

        **Keterangan Warna:**
        - 🔴 **Merah:** Barcode 1D berhasil terdeteksi & terbaca  
        - 🟢 **Hijau:** QR Code berhasil terdeteksi & terbaca  
        - 🟡 **Kuning:** Barcode/QR hanya terdeteksi tapi belum bisa dibaca
        """)
    ))

# ====================== DETECTION TAB ======================
with tab_detect:
    st.header("🖼️ Upload Image for Detection")
    st.write("Silakan unggah gambar untuk mendeteksi barcode.")
    uploaded_file = st.file_uploader("Upload gambar (jpg/png)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
        tfile.write(uploaded_file.read())
        tfile.flush()
        img_path = tfile.name

        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            st.error("Gagal membaca gambar. Coba upload file lain.")
        else:
            img_draw = img.copy()
            decoded_data = []

            st.info("⏳ Sedang memproses deteksi YOLOv8...")
            results = model.predict(source=img, conf=0.4, imgsz=960, verbose=False)

            bbox_counter = 1
            for r in results:
                for i, box in enumerate(r.boxes):
                    bbox_id = f"bbox_{bbox_counter}"
                    bbox_counter += 1

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls)
                    label = model.names[cls]

                    h, w = img.shape[:2]
                    font_scale = max(0.5, min(w, h) / 800)
                    thickness = int(max(1, min(w, h) / 600))

                    x1p, y1p = max(0, x1 - padding), max(0, y1 - padding)
                    x2p, y2p = min(w, x2 + padding), min(h, y2 + padding)

                    crop = img[y1p:y2p, x1p:x2p]
                    if crop is None or crop.size == 0:
                        continue
                    crop_resized = cv2.resize(crop, None, fx=resize_factor, fy=resize_factor)

                    decoded_ok = False
                    decoded_text = None
                    code_type = None

                    # ZXing decode
                    try:
                        zxing_res = zxing_reader.decode(crop_resized)
                    except Exception:
                        zxing_res = None

                    if zxing_res:
                        for r_ in zxing_res:
                            raw_data = r_.get("parsed") or r_.get("raw") or ""
                            fmt_raw = r_.get("format", "UNKNOWN")

                            if isinstance(raw_data, bytes):
                                decoded_text = raw_data.decode("utf-8", errors="ignore").replace("\x1d", "|")
                            elif isinstance(raw_data, list):
                                decoded_text = "".join(chr(c) for c in raw_data)
                            else:
                                decoded_text = str(raw_data).replace("b'", "").replace("'", "").replace("\x1d", "|")

                            code_type = str(fmt_raw)
                            decoded_ok = True
                            break

                    # Pyzbar fallback
                    if not decoded_ok:
                        decoded = pyzbar_decode(crop_resized)
                        if decoded:
                            for d in decoded:
                                try:
                                    decoded_text = d.data.decode("utf-8")
                                except Exception:
                                    decoded_text = str(d.data)
                                code_type = d.type
                                decoded_ok = True
                                break

                    # Tentukan warna sesuai hasil
                    if decoded_ok:
                        if "QR" in str(code_type).upper():
                            color = (0, 255, 0)  # Hijau
                            tag = f"QR | {decoded_text}"
                        else:
                            color = (0, 0, 255)  # Merah
                            tag = f"BARCODE | {decoded_text}"
                    else:
                        color = (0, 255, 255)  # Kuning
                        tag = "UNDECODED"

                    # Gambar bounding box dan teks
                    cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, thickness + 1)
                    cv2.putText(img_draw, tag, (x1, max(25, y1 - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness + 1)

                    decoded_data.append({
                        "BBox ID": bbox_id,
                        "Source": label,
                        "Decoded Content": decoded_text if decoded_text else "(undecoded)",
                        "Type": code_type if code_type else "UNKNOWN"
                    })

            # ===== SHOW RESULT =====
            df = pd.DataFrame(decoded_data, columns=["BBox ID", "Source", "Decoded Content", "Type"])
            st.session_state["last_df"] = df

            st.subheader("🧩 Detection Result")
            st.image(cv2.cvtColor(img_draw, cv2.COLOR_BGR2RGB),
                     caption="Detection Result (dengan warna kode)"
                     )

            if not df.empty:
                st.markdown("### 📋 Decoded Data")
                st.table(df)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, output_csv, "text/csv")
            else:
                st.warning("⚠️ Tidak ada barcode yang berhasil didecode.")

