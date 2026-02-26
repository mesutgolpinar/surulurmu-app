import streamlit as st
import requests
import pytesseract
from PIL import Image
import numpy as np

# Analiz Sözlüğü (Aynı kalıyor)
KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SULPHATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "DIMETHICONE": "Silikon: Gözenekleri tıkayabilir.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "PARFUM": "Sentetik Parfüm: Alerji riski taşır.",
    "PARAFFINUM": "Mineral Yağ: Petrol türevidir."
}

st.set_page_config(page_title="SürülürMü? Pro v2.2", page_icon="💄")
st.title("💄 SürülürMü? Profesyonel Denetçi")

def analyze_content(text):
    if not text: return None
    t_upper = text.upper()
    risks = []
    for ing, desc in KOZMETIK_SOZLUK.items():
        if ing in t_upper:
            risks.append(f"⚠️ **{ing}:** {desc}")
    return risks

st.subheader("⌨️ Barkod Sorgulama")
barcode_input = st.text_input("Barkod numarasını yazın (Örn: 3600523725129):")

if barcode_input:
    # 1. STRATEJİ: Önce Kozmetik Veritabanını Dene
    # 2. STRATEJİ: Bulamazsa Genel Gıda/Ürün Veritabanını Dene
    apis = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode_input}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode_input}.json"
    ]
    
    found = False
    with st.spinner('Ürün aranıyor...'):
        for url in apis:
            try:
                r = requests.get(url, timeout=5)
                data = r.json()
                if data.get("status") == 1:
                    product = data["product"]
                    isim = product.get('product_name_tr') or product.get('product_name') or "Bilinmeyen"
                    icerik = product.get('ingredients_text_tr') or product.get('ingredients_text') or ""
                    
                    st.success(f"✅ Ürün Bulundu: {isim}")
                    risks = analyze_content(icerik)
                    if risks:
                        for r_item in risks: st.error(r_item)
                    else:
                        st.balloons()
                        st.success("Temiz içerik saptandı.")
                    
                    with st.expander("İçerik Detayı"):
                        st.write(icerik)
                    found = True
                    break
            except:
                continue

    if not found:
        st.warning("❌ Ürün veritabanında bulunamadı.")
        google_url = f"https://www.google.com/search?q={barcode_input}+içindekiler"
        st.markdown(f"""
            <a href="{google_url}" target="_blank">
                <button style="width:100%; padding:10px; background-color:#4285F4; color:white; border:none; border-radius:5px; cursor:pointer;">
                    🔍 Ürünü Google'da Ara (İçindekiler İçin)
                </button>
            </a>
            """, unsafe_allow_html=True)
        st.info("💡 Not: Ürünü bulamadığımızda fotoğrafını çekip 'İçerik Fotoğrafı Analizi' kısmından taratabilirsiniz.")

st.markdown("---")
st.subheader("📷 İçerik Fotoğrafı Analizi (En Kesin Yol)")
# Fotoğraf yükleme kısmı aynı kalıyor...
