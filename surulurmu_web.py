import streamlit as st
import requests
from PIL import Image
from pyzbar import pyzbar
import numpy as np

# --- 1. AYARLAR VE SÖZLÜK ---
KOZMETIK_SOZLUK = {
    "PARABEN": "Koruyucu: Hormonal sistemi etkileyebilir.",
    "SULFATE": "Sülfat: Cildi tahriş edebilir.",
    "SILICONE": "Silikon: Gözenekleri tıkayabilir.",
    "FRAGRANCE": "Sentetik Parfüm: Alerji riski taşır.",
    "ALCOHOL DENAT": "Kurutucu Alkol: Cilt bariyerine zarar verebilir."
}

st.set_page_config(page_title="SürülürMü? v4.0", page_icon="💄")
st.title("💄 SürülürMü? Profesyonel Denetçi")

# --- 2. ÜRÜN SORGULAMA FONKSİYONU (TAMAMEN ONARILDI) ---
def get_product_details(barcode):
    if not barcode: return
    barcode = str(barcode).strip()
    
    # Hem kozmetik hem gıda veritabanı (Hibrit Arama)
    urls = [
        f"https://world.openbeautyfacts.org/api/v0/product/{barcode}.json",
        f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    ]
    
    found = False
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("status") == 1:
                p = r.json()["product"]
                marka = p.get('brands', 'Belirtilmemiş')
                isim = p.get('product_name_tr') or p.get('product_name') or 'Bilinmeyen Ürün'
                icerik = p.get('ingredients_text_tr') or p.get('ingredients_text') or ''
                
                # Ekrana Bilgileri Bas (Elle girişte düzelen kısım burası)
                st.success(f"📦 **Marka:** {marka}\n\n✨ **Ürün:** {isim}")
                
                if icerik:
                    st.subheader("🧪 İçerik Analizi")
                    found_risks = []
                    for ing, desc in KOZMETIK_SOZLUK.items():
                        if ing in icerik.upper():
                            found_risks.append(f"⚠️ **{ing}:** {desc}")
                    
                    if found_risks:
                        for r_item in found_risks: st.error(r_item)
                    else:
                        st.success("✅ Bilinen bir riskli maddeye rastlanmadı.")
                    
                    with st.expander("Ham İçerik Listesini Gör"):
                        st.write(icerik)
                else:
                    st.warning("Ürünün içerik bilgisi veritabanında eksik.")
                found = True
                break
        except:
            continue
    
    if not found:
        st.warning(f"❌ {barcode} barkodlu ürün bulunamadı.")

# --- 3. ARAYÜZ TASARIMI ---
tab1, tab2 = st.tabs(["⌨️ Manuel Barkod", "📷 Fotoğraf Çek/Yükle"])

with tab1:
    # Manuel giriş alanı (Burası dokunulmaz kılındı)
    barcode_input = st.text_input("Barkod numarasını yazın ve Enter'a basın:", key="man_entry")
    if barcode_input:
        get_product_details(barcode_input)

with tab2:
    st.info("Canlı video yerine fotoğraf çekmek, telefonun kendi 'otomatik odaklama' (autofocus) özelliğini kullandığı için küçük barkodlarda çok daha başarılıdır.")
    
    # Telefonun kendi kamerasını açan en kararlı bileşen
    captured_img = st.camera_input("Barkodun fotoğrafını çekin")
    
    if captured_img:
        img = Image.open(captured_img)
        # Barkod çözümleme
        barcodes = pyzbar.decode(img)
        
        if barcodes:
            scanned_code = barcodes[0].data.decode("utf-8")
            st.info(f"🎯 Barkod Algılandı: {scanned_code}")
            get_product_details(scanned_code)
        else:
            st.error("Barkod okunamadı. Lütfen ışığı ayarlayıp biraz daha uzaktan/net çekmeyi deneyin.")
