import streamlit as st
import requests
from PIL import Image
from pyzbar import pyzbar
import numpy as np

# Kozmetik Sözlüğü (Senin hazinen)
KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir."
}

st.set_page_config(page_title="SürülürMü? v3.0", page_icon="💄")
st.title("💄 SürülürMü? Profesyonel Denetçi")

# --- ANALİZ FONKSİYONU (Manuel girişteki gibi stabil) ---
def get_details(barcode):
    barcode = str(barcode).strip()
    urls = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("status") == 1:
                p = data["product"]
                st.success(f"✅ **Marka:** {p.get('brands', 'Bilinmeyen')} \n\n **Ürün:** {p.get('product_name', 'İsimsiz')}")
                # İçerik Analizi
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text') or ''
                if icerik:
                    st.subheader("🧪 İçerik Analizi")
                    for ing, desc in KOZMETIK_SOZLUK.items():
                        if ing in icerik.upper():
                            st.error(f"⚠️ **{ing}:** {desc}")
                return True
        except: continue
    st.warning("Ürün veritabanında bulunamadı.")
    return False

# --- YENİ YÖNTEM: TAŞ GİBİ SAĞLAM KAMERA ---
st.subheader("📷 Barkodun Fotoğrafını Çek")
cam_image = st.camera_input("Barkodu hizalayıp fotoğraf çekin")

if cam_image:
    img = Image.open(cam_image)
    # Fotoğraftan barkodu oku
    barcodes = pyzbar.decode(img)
    if barcodes:
        scanned_code = barcodes[0].data.decode("utf-8")
        st.info(f"🎯 Barkod Okundu: {scanned_code}")
        get_details(scanned_code)
    else:
        st.error("Fotoğrafta barkod algılanamadı. Lütfen daha yakından ve net çekin.")

st.markdown("---")

# Elle Giriş (Hala en güvenli limanımız)
st.subheader("⌨️ Manuel Sorgulama")
barcode_input = st.text_input("Barkodu elle yazın:")
if barcode_input:
    get_details(barcode_input)
