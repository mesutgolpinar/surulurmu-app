import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import requests
from pyzbar import pyzbar
import numpy as np

# RTC Ayarları
RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# --- ÜRÜN SORGULAMA FONKSİYONU (Manuel girişteki gibi çalışır) ---
def get_product_details(barcode):
    if not barcode: return
    urls = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("status") == 1:
                p = r.json()["product"]
                marka = p.get('brands', 'Belirtilmemiş')
                isim = p.get('product_name_tr') or p.get('product_name') or 'İsimsiz Ürün'
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text') or ''
                st.success(f"📦 **Marka:** {marka} \n\n ✨ **Ürün:** {isim}")
                if icerik:
                    # Risk analizini burada göster (Önceki kodun aynısı)
                    st.info("İçerik analiz ediliyor...")
                return True
        except: continue
    return False

# --- GÜÇLENDİRİLMİŞ KAMERA İŞLEMCİSİ ---
class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.last_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # 1. Görüntüyü Griye Çevir
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. ÖNEMLİ: Görüntüyü Ölçeklendir (Düşük çözünürlüklü tarama daha hızlıdır)
        # Bazen görüntü çok net/büyük olduğunda kütüphane çizgileri tanıyamaz.
        small_img = cv2.resize(gray, (0,0), fx=0.5, fy=0.5)
        
        # 3. İki Farklı Modda Tara (Ham ve Keskinleştirilmiş)
        barcodes = pyzbar.decode(small_img)
        if not barcodes:
            # Eğer bulamadıysa, kontrastı artırıp tekrar dene
            sharp = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
            barcodes = pyzbar.decode(sharp)
            
        for barcode in barcodes:
            self.last_barcode = barcode.data.decode("utf-8")
            
        return frame

st.set_page_config(page_title="SürülürMü? v2.7")
st.title("💄 SürülürMü? Profesyonel Denetçi")

tab1, tab2 = st.tabs(["⌨️ Elle Barkod", "📷 Canlı Tarayıcı"])

with tab1:
    barcode_input = st.text_input("Barkod numarasını yazın:", key="manual_fixed")
    if barcode_input:
        get_product_details(barcode_input)

with tab2:
    st.warning("Barkodu kameraya yaklaştırın ve 1-2 saniye sabit tutun.")
    ctx = webrtc_streamer(
        key="live-scan-v27",
        video_processor_factory=BarcodeScanner,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 640}, # Çözünürlüğü düşürerek okuma hızını artırdık
                "height": {"ideal": 480}
            }, 
            "audio": False
        },
        async_processing=True
    )
    
    if ctx.video_processor and ctx.video_processor.last_barcode:
        barcode_found = ctx.video_processor.last_barcode
        st.success(f"🎯 Barkod Yakalandı: {barcode_found}")
        get_product_details(barcode_found)
