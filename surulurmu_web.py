import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import requests
from pyzbar import pyzbar
import numpy as np

# RTC Ayarları
RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir."
}

# --- 1. MANUEL GİRİŞ (DOKUNULMAZ VE STABİL) ---
def get_product_details(barcode):
    if not barcode: return
    # Barkodun başındaki sonundaki boşlukları temizle (En sık hata sebebi)
    barcode = str(barcode).strip()
    
    urls = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    ]
    
    found = False
    for url in urls:
        try:
            r = requests.get(url, timeout=7)
            data = r.json()
            if data.get("status") == 1:
                p = data["product"]
                marka = p.get('brands', 'Belirtilmemiş')
                isim = p.get('product_name_tr') or p.get('product_name') or 'İsimsiz Ürün'
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text') or ''
                
                st.success(f"✅ Ürün Bulundu!\n\n**Marka:** {marka}\n\n**İsim:** {isim}")
                
                if icerik:
                    st.subheader("🧪 İçerik Analizi")
                    risks_found = []
                    for ing, desc in KOZMETIK_SOZLUK.items():
                        if ing in icerik.upper():
                            risks_found.append(f"⚠️ **{ing}:** {desc}")
                    
                    if risks_found:
                        for r_item in risks_found: st.error(r_item)
                    else:
                        st.success("Temiz içerik!")
                    
                    with st.expander("Ham İçerik Metni"):
                        st.write(icerik)
                found = True
                break
        except:
            continue
            
    if not found:
        st.warning(f"❌ {barcode} barkodlu ürün veritabanında bulunamadı.")

# --- 2. KAMERA (QR/CAFE MENÜSÜ GİBİ HIZLI MOD) ---
class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.last_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        # Görüntüyü işlemden önce optimize et (Burası cafe menüsü hızı sağlar)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Hem düz barkod (EAN13) hem karekod (QR) için tarama
        barcodes = pyzbar.decode(gray)
        
        if not barcodes:
            # Kontrast artırıp tekrar dene (Işık sorunları için)
            sharp = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)[1]
            barcodes = pyzbar.decode(sharp)

        for barcode in barcodes:
            self.last_barcode = barcode.data.decode("utf-8")
        return frame

st.set_page_config(page_title="SürülürMü? v2.9")
st.title("💄 SürülürMü? Denetçi")

# Manuel giriş her zaman en üstte ve aktif
barcode_input = st.text_input("Barkodu buraya yazın veya kamerayı başlatın:", key="main_input")
if barcode_input:
    get_product_details(barcode_input)

st.markdown("---")

# Kamera Alt Bölümde
with st.expander("📷 Canlı Barkod Tarayıcıyı Aç/Kapat", expanded=True):
    ctx = webrtc_streamer(
        key="final-scan",
        video_processor_factory=BarcodeScanner,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True
    )
    
    if ctx.video_processor and ctx.video_processor.last_barcode:
        scanned = ctx.video_processor.last_barcode
        st.info(f"🎯 Yakalandı: {scanned}")
        get_product_details(scanned)
