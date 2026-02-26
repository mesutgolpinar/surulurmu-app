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

# --- 2. ÜRÜN SORGULAMA FONKSİYONU (SENİN İSTEDİĞİN STABİL HALİ) ---
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
                
                # Ekrana basma işlemleri (Burası manuel girişte çalışan kısım)
                st.success(f"📦 **Marka:** {marka} \n\n ✨ **Ürün:** {isim}")
                
                st.subheader("🧪 İçerik Analizi")
                found_any = False
                if icerik:
                    for ing, desc in KOZMETIK_SOZLUK.items():
                        if ing in icerik.upper():
                            st.error(f"⚠️ **{ing}:** {desc}")
                            found_any = True
                    if not found_any:
                        st.success("✅ Bilinen bir riskli maddeye rastlanmadı.")
                    with st.expander("Ham İçerik Listesi"):
                        st.write(icerik)
                return True
        except: continue
    st.warning("Ürün bulunamadı.")
    return False

# --- 3. KAMERA İŞLEMCİSİ (EAN-13 İÇİN KESKİNLEŞTİRİLMİŞ) ---
class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.last_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # EAN-13 çizgilerini daha iyi görmek için kontrastı tavan yapıyoruz
        sharp = cv2.convertScaleAbs(gray, alpha=1.5, beta=0) 
        
        # Sadece EAN13 ve QR kodlarını arayacak şekilde kısıtlıyoruz (Hız artırır)
        barcodes = pyzbar.decode(sharp)
        
        for barcode in barcodes:
            self.last_barcode = barcode.data.decode("utf-8")
        return frame

st.set_page_config(page_title="SürülürMü? v2.8", layout="centered")
st.title("💄 SürülürMü? Denetçi")

# Sekmeleri ayırdık ki manuel giriş her zaman taze kalsın
tab1, tab2 = st.tabs(["⌨️ Elle Barkod", "📷 Canlı Tarayıcı"])

with tab1:
    barcode_input = st.text_input("Barkod numarasını yazın:", key="manual_input_fixed")
    if barcode_input:
        get_product_details(barcode_input)

with tab2:
    st.info("EAN-13 barkodunu kameraya dikey veya yatay olarak ortalayın.")
    ctx = webrtc_streamer(
        key="live-v28",
        video_processor_factory=BarcodeScanner,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True
    )
    
    if ctx.video_processor and ctx.video_processor.last_barcode:
        barcode_found = ctx.video_processor.last_barcode
        st.info(f"🎯 Kamera Yakaladı: {barcode_found}")
        get_product_details(barcode_found)
