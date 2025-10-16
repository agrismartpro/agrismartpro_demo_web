import json
import pandas as pd
import streamlit as st
from pathlib import Path

# Cartella base del repo e cartella dati
BASE_DIR = Path(_file).parent if "file_" in globals() else Path.cwd()
DATA_DIR = BASE_DIR / "data"   # <-- qui deve esistere la cartella 'data'

def load_json(filename, default):
    path = DATA_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

st.set_page_config(page_title="AgriSmartPro – Demo Web", layout="wide")
st.title("🌾 AgriSmartPro – Demo Web")

# Checkbox di debug per capire subito cosa vede l'app
with st.expander("🔧 Debug (clicca per aprire)"):
    st.write("DATA_DIR:", str(DATA_DIR))
    try:
        st.write("File presenti:", [p.name for p in DATA_DIR.glob("*.json")])
    except Exception as e:
        st.write("Errore nel leggere la cartella dati:", e)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📘 Fertilizzazioni")
    fert = load_json("fertilizzazioni.json", {"records": []}).get("records", [])
    st.dataframe(pd.DataFrame(fert))

with col2:
    st.subheader("🌱 Trattamenti")
    tratt = load_json("trattamenti.json", {"records": []}).get("records", [])
    st.dataframe(pd.DataFrame(tratt))

with col3:
    st.subheader("🏷 Magazzino")
    mag = load_json("magazzino.json", {"prodotti": []}).get("prodotti", [])
    st.dataframe(pd.DataFrame(mag))

st.markdown("---")
st.caption("AgriSmartPro Demo Web © 2025")
