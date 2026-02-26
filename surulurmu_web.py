import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import numpy as np
from pyzbar import pyzbar
import requests

# --- GÜÇLENDİRİLMİŞ BAĞLANTI AYARLARI ---
RTC_CONFIG = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.barcode_data = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # --- BARKOD YAKALAMA HASSASİYETİ ARTIRMA ---
        # Görüntüyü gri tonlamaya çevir ve kontrastı artır (Kameranın daha iyi görmesi için)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Pyzbar ile tara
        barcodes = pyzbar.decode(gray)
        
        for barcode in barcodes:
            self.barcode_data = barcode.data.decode("utf-8")
            (x, y, w, h) = barcode.rect
            # Barkodu bulduğunda ekrana yeşil çerçeve çiz (Geri bildirim için)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 4)
            
        return frame

st.set_page_config(page_title="SürülürMü? Denetçi", layout="centered")
st.title("💄 SürülürMü? Profesyonel Denetçi")

# --- 1. MANUEL GİRİŞ ALANI (HER ZAMAN GÖRÜNÜR) ---
st.subheader("⌨️ Manuel Barkod Girişi")
manual_input = st.text_input("Barkodu buraya yazın veya okutun:", key="manual_entry")

# --- 2. CANLI KAMERA ALANI ---
st.subheader("📷 Canlı Barkod Tarayıcı")
st.info("İpucu: Barkodu kameraya yaklaştırın ve odaklanmasını bekleyin.")

ctx = webrtc_streamer(
    key="barcode-v25",
    video_processor_factory=BarcodeProcessor,
    rtc_configuration=RTC_CONFIG,
    media_stream_constraints={
        "video": {"facingMode": "environment"}, # Arka kamerayı zorla
        "audio": False
    },
    async_processing=True,
)

# --- ANALİZ MANTIĞI (HER İKİ GİRİŞ İÇİN DE ÇALIŞIR) ---
final_barcode = None

# Eğer kamera bir şey yakaladıysa onu kullan
if ctx.video_processor and ctx.video_processor.barcode_data:
    final_barcode = ctx.video_processor.barcode_data
    st.success(f"🎯 Kamera Barkodu Yakaladı: {final_barcode}")
# Eğer manuel giriş yapıldıysa onu kullan
elif manual_input:
    final_barcode = manual_input

if final_barcode:
    with st.spinner('Ürün veritabanında aranıyor...'):
        # Buraya önceki mesajlardaki API sorgu kodlarını (Open Beauty Facts) ekleyebilirsin.
        url = f"https://world.openbeautyfacts.org/api/v0/product/{final_barcode}.json"
        r = requests.get(url)
        if r.status_code == 200 and r.json().get("status") == 1:
            p = r.json()["product"]
            st.write(f"### ✨ Ürün: {p.get('product_name', 'Bilinmeyen')}")
            # Analiz sonuçlarını buraya yazdırıyoruz...
        else:
            st.warning("Ürün bulunamadı. Lütfen barkodu kontrol edin.")
