import streamlit as st
import json, os
import pandas as pd

st.set_page_config(page_title="AgriSmartPro – Demo Web", layout="wide")

# Percorsi
DATA_DIR = os.path.join(os.path.dirname(__file__), "dati")

def load_json(nome_file, default):
    path = os.path.join(DATA_DIR, nome_file)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# Titolo pagina
st.title("🌾 AgriSmartPro – Demo Web")

# Sezioni
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📘 Fertilizzazioni")
    fert = load_json("fertilizzazioni.json", {"records": []})["records"]
    st.dataframe(pd.DataFrame(fert))

with col2:
    st.subheader("🌱 Trattamenti")
    tratt = load_json("trattamenti.json", {"records": []})["records"]
    st.dataframe(pd.DataFrame(tratt))

with col3:
    st.subheader("🏷 Magazzino")
    mag = load_json("magazzino.json", {"prodotti": []})["prodotti"]
    st.dataframe(pd.DataFrame(mag))

st.markdown("---")
st.caption("AgriSmartPro Demo Web © 2025")
