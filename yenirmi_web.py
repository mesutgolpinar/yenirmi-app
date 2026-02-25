import streamlit as st
import cv2
import numpy as np
import pytesseract
import requests
import re
from PIL import Image
from pyzbar import pyzbar

# Tesseract Yolu (Windows için)
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Genişletilmiş Katkı Maddesi Sözlüğü
E_SOZLUK = {
    "E102": "Tartrazin: Alerjik reaksiyonlara neden olabilir.",
    "E211": "Sodyum Benzoat: Koruyucudur. C vitamini ile riskli olabilir.",
    "E330": "Sitrik Asit: Limon tuzu, asitlik düzenleyici.",
    "E621": "MSG (Çin Tuzu): Lezzet artırıcı, hassasiyet yapabilir.",
    "E322": "Lecithin: Emülgatör (Soya/Ayçiçek).",
    "E471": "Yağ asitlerinin mono- ve digliseritleri.",
    "E202": "Potasyum Sorbat: Koruyucudur."
}

st.set_page_config(page_title="YenirMi? Web Pro", page_icon="🛡️")

st.title("🛡️ YenirMi? Akıllı Denetçi v1.1")

# --- 1. DÜZELTME: BARKOD GİRİŞ ALANI ---
st.subheader("⌨️ Barkod Girişi")
manual_barcode = st.text_input("Barkodu buraya yazın veya okutun:", placeholder="Örn: 8690504018255")


# --- ANALİZ FONKSİYONU (Geliştirilmiş Karakter Temizleme) ---
def detailed_analysis(text):
    # Karakter karmaşasını önlemek için metni temizle
    clean_text = text.replace('\n', ' ').strip()
    t_upper = clean_text.upper()

    e_codes = re.findall(r'E[- ]?\d{3,4}', t_upper)
    risk_list = []
    for c in set(e_codes):
        code = c.replace("-", "").replace(" ", "")
        desc = E_SOZLUK.get(code, "Bu madde için henüz açıklama eklenmedi.")
        risk_list.append(f"• **{code}:** {desc}")

    kcal = re.search(r'(\d+)\s*KCAL', t_upper)
    enerji = f"{kcal.group(1)} kcal" if kcal else "Saptanamadı"
    return risk_list, enerji, clean_text


# --- BARKOD İŞLEME MANTIĞI ---
if manual_barcode:
    with st.spinner('Ürün aranıyor...'):
        r = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{manual_barcode}.json")
        if r.status_code == 200 and r.json().get("status") == 1:
            p = r.json()["product"]
            isim = p.get('product_name_tr', p.get('product_name', 'Bilinmeyen Ürün'))
            icerik = p.get('ingredients_text_tr') or p.get('ingredients_text', 'İçerik yok')

            st.success(f"📦 Ürün: {isim}")
            riskli, nrg, _ = detailed_analysis(icerik)

            st.warning(f"⚡ Enerji: {nrg}")
            if riskli:
                st.error("🧪 Saptanan Katkı Maddeleri:")
                for r_item in riskli: st.markdown(r_item)
            else:
                st.balloons()
                st.success("✅ Riskli içerik bulunamadı.")
        else:
            st.error("Ürün bulunamadı veya barkod hatalı.")

st.markdown("---")

# --- 2. DÜZELTME: RESİMDEN OKUMA VE KARAKTER SORUNU ---
st.subheader("📷 Resimden Analiz")
img_file = st.file_uploader("İçerik fotoğrafı yükle veya çek...", type=['jpg', 'png', 'jpeg'])

if img_file:
    image = Image.open(img_file)
    st.image(image, caption='Yüklenen Resim', width=400)

    if st.button("🔍 Yazıları Çöz ve Analiz Et"):
        with st.spinner('Tesseract karakterleri işliyor...'):
            # PSM 6 ve Türkçe desteği ile karakter karmaşasını minimize et
            custom_config = r'--oem 3 --psm 6 -l tur'
            text = pytesseract.image_to_string(image, config=custom_config)

            riskli, nrg, raw = detailed_analysis(text)

            st.info("📊 Analiz Sonucu")
            st.markdown(f"**⚡ Enerji:** {nrg}")
            if riskli:
                st.error("🧪 Katkı Maddesi Detayları:")
                for r_item in riskli: st.markdown(r_item)

            with st.expander("Okunan Ham Metni Gör"):
                st.write(raw)