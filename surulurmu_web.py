import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import cv2
import numpy as np
import pytesseract
import requests
import re
from PIL import Image
from pyzbar import pyzbar

# Kozmetik Risk Sözlüğü
KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat (SLS/SLES): Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir."
}


# --- BARKOD İŞLEMCİ SINIFI ---
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.last_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = pyzbar.decode(img)
        for barcode in barcodes:
            self.last_barcode = barcode.data.decode("utf-8")
            # Barkodu görsel olarak işaretle
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        return frame


st.set_page_config(page_title="SürülürMü? Canlı Denetçi", page_icon="💄")

st.title("💄 SürülürMü? Canlı Barkod Tarayıcı")
st.write("Barkodu kameraya gösterin, analiz otomatik başlayacaktır.")

# --- CANLI TARAYICI BÖLÜMÜ ---
ctx = webrtc_streamer(
    key="cosmetic-scanner",
    video_processor_factory=BarcodeProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)


def analyze_cosmetic(text):
    t_upper = text.upper()
    risks = []
    for ing, desc in KOZMETIK_SOZLUK.items():
        if ing in t_upper:
            risks.append(f"⚠️ **{ing}:** {desc}")
    return risks


# Barkod Yakalandığında Çalışacak Mantık
if ctx.video_processor and ctx.video_processor.last_barcode:
    barcode = ctx.video_processor.last_barcode
    st.info(f"✅ Barkod Algılandı: {barcode}")

    with st.spinner('Veritabanı sorgulanıyor...'):
        url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("status") == 1:
                p = r.json()["product"]
                isim = p.get('product_name_tr', p.get('product_name', 'Bilinmeyen Ürün'))
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text', '')

                st.subheader(f"✨ {isim}")
                risks = analyze_cosmetic(icerik)

                if risks:
                    st.error("🧪 İçerik Analiz Sonucu:")
                    for r_item in risks: st.markdown(r_item)
                else:
                    st.success("✅ Bilinen bir riskli maddeye rastlanmadı.")

                with st.expander("Tam İçerik Listesi"):
                    st.write(icerik if icerik else "İçerik verisi mevcut değil.")
            else:
                st.warning("Ürün veritabanında bulunamadı. Manuel giriş yapabilir veya resim yükleyebilirsiniz.")
        except:
            st.error("API bağlantı hatası.")

st.markdown("---")

# --- MANUEL GİRİŞ VE RESİM ANALİZİ (Yedek Plan) ---
col1, col2 = st.columns(2)
with col1:
    manual = st.text_input("Barkodu Elle Gir:")
with col2:
    img_file = st.file_uploader("Veya İçerik Fotoğrafı Yükle:", type=['jpg', 'png', 'jpeg'])

if img_file:
    image = Image.open(img_file)
    if st.button("🔍 Fotoğraftaki Yazıları Analiz Et"):
        text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l tur+eng')
        risks = analyze_cosmetic(text)
        if risks:
            for r_item in risks: st.error(r_item)
        else:
            st.success("Riskli madde bulunamadı.")