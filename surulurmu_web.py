import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import numpy as np
from pyzbar import pyzbar
import requests

# RTC Ayarları (Mobil veri ve farklı ağlarda kamera erişimi için kritik)
RTC_CONFIG = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.found_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Görüntüyü biraz netleştir (Barkod yakalama şansını artırır)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Barkod Tara
        barcodes = pyzbar.decode(gray)
        
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            self.found_barcode = barcode_data
            
            # Ekran üzerinde yeşil çerçeve çiz (Görsel geri bildirim)
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 5)
            cv2.putText(img, "YAKALANDI!", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        return frame

st.set_page_config(page_title="SürülürMü? Canlı Tarayıcı", layout="wide")
st.title("💄 SürülürMü? Otomatik Barkod Tarayıcı")

# --- KAMERA BÖLÜMÜ ---
st.subheader("📷 Barkodu Kameraya Yaklaştırın")
ctx = webrtc_streamer(
    key="barcode-check",
    video_processor_factory=BarcodeScanner,
    rtc_configuration=RTC_CONFIG,
    media_stream_constraints={"video": True, "audio": False},
)

# --- ANALİZ MANTIĞI ---
if ctx.video_processor and ctx.video_processor.found_barcode:
    barcode = ctx.video_processor.found_barcode
    st.success(f"🎯 Barkod Yakalandı: {barcode}")
    
    # Otomatik API Sorgusu
    with st.spinner('Ürün bilgileri getiriliyor...'):
        # Hem kozmetik hem gıda veritabanına bak (Hibrit)
        url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("status") == 1:
                p = data["product"]
                st.subheader(f"✨ {p.get('product_name', 'Bilinmeyen Ürün')}")
                # ... Analiz sözlüğü buraya eklenebilir ...
            else:
                st.warning("Ürün veritabanında henüz yok.")
        except:
            st.error("Bağlantı sorunu.")
