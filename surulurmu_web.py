import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import requests
from pyzbar import pyzbar
import numpy as np

# --- 1. AYARLAR VE SÖZLÜK ---
RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir."
}

# --- 2. ÜRÜN SORGULAMA FONKSİYONU (TAM VERİ ÇEKER) ---
def get_product_details(barcode):
    if not barcode: return
    
    # Hem kozmetik hem genel veritabanını dene
    urls = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    ]
    
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("status") == 1:
                p = r.json()["product"]
                
                # Bilgileri Ayıkla
                marka = p.get('brands', 'Belirtilmemiş')
                isim = p.get('product_name_tr') or p.get('product_name') or 'İsimsiz Ürün'
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text') or ''
                
                st.success(f"📦 **Marka:** {marka} \n\n ✨ **Ürün:** {isim}")
                
                # Analiz Yap
                st.subheader("🧪 İçerik Analizi")
                found_any = False
                if icerik:
                    for ing, desc in KOZMETIK_SOZLUK.items():
                        if ing in icerik.upper():
                            st.error(f"⚠️ **{ing}:** {desc}")
                            found_any = True
                    
                    if not found_any:
                        st.balloons()
                        st.success("Bilinen bir riskli maddeye rastlanmadı.")
                    
                    with st.expander("Ham İçerik Listesini Gör"):
                        st.write(icerik)
                else:
                    st.warning("Ürünün içerik bilgisi veritabanında eksik.")
                return True
        except:
            continue
    st.warning("Ürün bulunamadı veya barkod hatalı.")
    return False

# --- 3. KAMERA İŞLEMCİSİ (KESKİN OKUMA MODU) ---
class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.last_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Görüntü net olsa bile barkodu ayırt etmek için kontrastı artırıyoruz
        # Bu işlem barkod çizgilerini jilet gibi keskinleştirir
        sharp = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        barcodes = pyzbar.decode(sharp)
        for barcode in barcodes:
            self.last_barcode = barcode.data.decode("utf-8")
        return frame

st.set_page_config(page_title="SürülürMü? v2.6", layout="centered")
st.title("💄 SürülürMü? Profesyonel Denetçi")

# --- 4. ARAYÜZ ---
tab1, tab2 = st.tabs(["⌨️ Elle Barkod", "📷 Canlı Tarayıcı"])

with tab1:
    barcode_input = st.text_input("Barkod numarasını yazın:", key="manual")
    if barcode_input:
        get_product_details(barcode_input)

with tab2:
    ctx = webrtc_streamer(
        key="live-scan",
        video_processor_factory=BarcodeScanner,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True
    )
    
    if ctx.video_processor and ctx.video_processor.last_barcode:
        st.info(f"🎯 Kamera Barkodu Yakaladı: {ctx.video_processor.last_barcode}")
        get_product_details(ctx.video_processor.last_barcode)
