import streamlit as st
import requests
import pytesseract
from PIL import Image
from pyzbar import pyzbar
import numpy as np

# Tesseract yolu (Linux sunucuda boş bırakılır)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Kozmetik Sözlüğü
KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SULPHATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "DIMETHICONE": "Silikon Türevi: Gözenekleri tıkayabilir.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "PARFUM": "Sentetik Parfüm: Alerji riski taşır."
}

st.set_page_config(page_title="SürülürMü? Pro", page_icon="💄")
st.title("💄 SürülürMü? Kozmetik Denetçi")

# --- ANALİZ FONKSİYONU ---
def analyze_content(text):
    if not text: return None
    t_upper = text.upper()
    risks = []
    for ing, desc in KOZMETIK_SOZLUK.items():
        if ing in t_upper:
            risks.append(f"⚠️ **{ing}:** {desc}")
    return risks

# --- 1. MANUEL BARKOD GİRİŞİ (TEPKİ VEREN KISIM) ---
st.subheader("⌨️ Barkod ile Sorgula")
barcode_input = st.text_input("Barkod numarasını girin ve Enter'a basın:", key="manual_barcode")

# Barkod girildiğinde tetiklenir
if barcode_input:
    with st.spinner(f'{barcode_input} sorgulanıyor...'):
        # Open Beauty Facts API
        url = f"https://world.openbeautyfacts.org/api/v0/product/{barcode_input}.json"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if r.status_code == 200 and data.get("status") == 1:
                product = data["product"]
                isim = product.get('product_name_tr') or product.get('product_name') or "Bilinmeyen Ürün"
                icerik = product.get('ingredients_text_tr') or product.get('ingredients_text') or ""
                
                st.success(f"✅ Ürün Bulundu: {isim}")
                
                analiz_sonucu = analyze_content(icerik)
                if analiz_sonucu:
                    st.error("🧪 Riskli İçerikler:")
                    for r_item in analiz_sonucu: st.write(r_item)
                else:
                    st.balloons()
                    st.success("✅ Temiz içerik! Bilinen bir riskli maddeye rastlanmadı.")
                
                with st.expander("Ham İçerik Metni"):
                    st.write(icerik if icerik else "İçerik verisi yok.")
            else:
                st.warning("Ürün veritabanında bulunamadı. Lütfen barkodu kontrol edin veya resim yükleyin.")
        except Exception as e:
            st.error(f"Bağlantı hatası: {str(e)}")

st.markdown("---")

# --- 2. RESİM YÜKLEME VE OCR ---
st.subheader("📷 İçerik Fotoğrafı Analizi")
uploaded_file = st.file_uploader("Ürünün arkasındaki 'Ingredients' kısmını çekin...", type=['jpg','jpeg','png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Yüklenen Fotoğraf', width=300)
    
    if st.button("Yazıları Çöz ve Analiz Et"):
        with st.spinner('Yazılar okunuyor...'):
            # Türkçe ve İngilizce desteği ile oku
            text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l tur+eng')
            risks = analyze_content(text)
            
            if risks:
                st.error("🧪 Analiz Sonucu:")
                for r_item in risks: st.write(r_item)
            else:
                st.success("Bilinen bir riskli madde saptanmadı.")
            
            with st.expander("Okunan Metni Gör"):
                st.write(text)
