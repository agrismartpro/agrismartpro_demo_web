
import json, os
from datetime import date
import pandas as pd
import streamlit as st
from fpdf import FPDF
st.set_page_config(page_title="AgriSmartPro 🌿 – Quaderno Digitale", page_icon="🌿", layout="wide")
st.title("🌿 AgriSmartPro – Quaderno Digitale (MVP)")
st.caption("Versione demo pubblica: gestione Trattamenti, Magazzino e Fertilizzazioni con esportazione in PDF. Powered by Streamlit.")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "trattamenti": os.path.join(DATA_DIR, "trattamenti.json"),
    "magazzino": os.path.join(DATA_DIR, "magazzino.json"),
    "fertilizzazioni": os.path.join(DATA_DIR, "fertilizzazioni.json"),
    "azienda": os.path.join(DATA_DIR, "azienda.json"),
    "logo": os.path.join(DATA_DIR, "logo.png"),
}

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def load_company():
    data = load_json(FILES["azienda"])
    if not data:
        return {"ragione_sociale": "", "piva": "", "indirizzo": "", "telefono": "", "email": ""}
    return data

def save_company(data):
    save_json(FILES["azienda"], data)

def generate_treatments_pdf(company, logo_path, rows):
    pdf = FPDF()
    pdf.add_page()

    def safe_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    intest = safe_text(company.get("ragione_sociale", ""))
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 6, intest, ln=1, align="R")

    contatti = f"{company.get('telefono','')}  {company.get('email','')}"
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, safe_text(contatti), ln=1, align="R")
    pdf.ln(8)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_text("Registro trattamenti"), ln=1)

    pdf.set_font("Arial", "", 9)
    headers = ["Data", "Campo", "Prodotto", "Dose l/ha", "Ettari", "Operatore"]
    widths = [22, 35, 50, 22, 18, 35]

    for w, h in zip(widths, headers):
        pdf.cell(w, 7, safe_text(h), border=1)
    pdf.ln()

    for r in rows:
        pdf.cell(widths[0], 6, safe_text(r.get("data", "")), border=1)
        pdf.cell(widths[1], 6, safe_text(r.get("campo", ""))[:28], border=1)
        pdf.cell(widths[2], 6, safe_text(r.get("prodotto", ""))[:45], border=1)
        pdf.cell(widths[3], 6, safe_text(r.get("dose_l_ha", "")), border=1, align="R")
        pdf.cell(widths[4], 6, safe_text(r.get("ettari", "")), border=1, align="R")
        pdf.cell(widths[5], 6, safe_text(r.get("operatore", ""))[:28], border=1)
        pdf.ln()

    out_path = os.path.join(DATA_DIR, "trattamenti.pdf")
    pdf.output(out_path)
    return out_path
st.title("🌾 AgriSmartPro – Demo Web (MVP)")
st.caption("Versione dimostrativa: gestione Trattamenti, Magazzino, Fertilizzazioni con salvataggio su file JSON locali.")

tabs = st.tabs(["Trattamenti", "Magazzino", "Fertilizzazioni", "Impostazioni", "Export"])

# --- Trattamenti ---
with tabs[0]:
    st.subheader("Registro trattamenti")
    dati = load_json(FILES["trattamenti"])
    df = pd.DataFrame(dati)
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Aggiungi trattamento"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_t = st.date_input("Data", value=date.today())
            campo = st.text_input("Campo/Parcella", "")
            operatore = st.text_input("Operatore", "")
        with col2:
            prodotto = st.text_input("Prodotto", "")
            dose = st.number_input("Dose (L/ha)", min_value=0.0, step=0.1)
            ettari = st.number_input("Ettari", min_value=0.0, step=0.1)
        with col3:
            note = st.text_area("Note", height=80)
            if st.button("Salva trattamento"):
                nuovo = {
                    "data": str(data_t),
                    "campo": campo.strip(),
                    "prodotto": prodotto.strip(),
                    "dose_l_ha": dose,
                    "ettari": ettari,
                    "operatore": operatore.strip(),
                    "note": note.strip(),
                }
                dati.append(nuovo)
                save_json(FILES["trattamenti"], dati)
                st.success("Trattamento salvato! Ricarica la pagina per aggiornare la tabella.")

# --- Magazzino ---
with tabs[1]:
    st.subheader("Magazzino fitosanitari/fertilizzanti")
    dati = load_json(FILES["magazzino"])
    df = pd.DataFrame(dati)
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Aggiungi/aggiorna voce di magazzino"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            prodotto = st.text_input("Prodotto", "", key="m_prodotto")
            lotto = st.text_input("Lotto", "", key="m_lotto")
        with col2:
            unita = st.selectbox("Unità", ["L", "kg", "pz"], key="m_unita")
            giacenza = st.number_input("Giacenza", min_value=0.0, step=0.1, key="m_giacenza")
        with col3:
            costo = st.number_input("Costo unitario (€)", min_value=0.0, step=0.01, key="m_costo")
        with col4:
            azione = st.selectbox("Azione", ["Aggiungi", "Sostituisci/aggiorna"], key="m_azione")
            if st.button("Salva magazzino", key="m_salva"):
                esistente_idx = None
                for i, r in enumerate(dati):
                    if r.get("prodotto")==prodotto and r.get("lotto")==lotto:
                        esistente_idx = i
                        break
                voce = {
                    "prodotto": prodotto.strip(),
                    "lotto": lotto.strip(),
                    "unita": unita,
                    "giacenza": giacenza,
                    "costo_unitario": costo
                }
                if esistente_idx is None:
                    dati.append(voce)
                else:
                    if azione == "Aggiungi":
                        dati[esistente_idx]["giacenza"] = float(dati[esistente_idx]["giacenza"]) + float(giacenza)
                        dati[esistente_idx]["costo_unitario"] = costo or dati[esistente_idx]["costo_unitario"]
                    else:
                        dati[esistente_idx] = voce
                save_json(FILES["magazzino"], dati)
                st.success("Magazzino aggiornato! Ricarica la pagina per vedere i cambiamenti.")

# --- Fertilizzazioni ---
with tabs[2]:
    st.subheader("Registro fertilizzazioni")
    dati = load_json(FILES["fertilizzazioni"])
    df = pd.DataFrame(dati)
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Aggiungi fertilizzazione"):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_f = st.date_input("Data", value=date.today(), key="data_f")
            campo = st.text_input("Campo/Parcella", "", key="campo_f")
            operatore = st.text_input("Operatore", "", key="op_f")
        with col2:
            prodotto = st.text_input("Prodotto", "", key="prod_f")
            dose = st.number_input("Dose (kg/ha)", min_value=0.0, step=1.0, key="dose_f")
            ettari = st.number_input("Ettari", min_value=0.0, step=0.1, key="ett_f")
        with col3:
            note = st.text_area("Note", height=80, key="note_f")
            if st.button("Salva fertilizzazione"):
                nuovo = {
                    "data": str(data_f),
                    "campo": campo.strip(),
                    "prodotto": prodotto.strip(),
                    "dose_kg_ha": dose,
                    "ettari": ettari,
                    "operatore": operatore.strip(),
                    "note": note.strip(),
                }
                dati.append(nuovo)
                save_json(FILES["fertilizzazioni"], dati)
                st.success("Fertilizzazione salvata! Ricarica la pagina per aggiornare la tabella.")
# --- Impostazioni ---
with tabs[3]:
    st.subheader("Impostazioni azienda")
    azienda = load_company()

    col1, col2 = st.columns([2,1])

    with col1:
        ragione = st.text_input("Ragione sociale", azienda.get("ragione_sociale",""), key="az_rs")
        piva = st.text_input("Partita IVA", azienda.get("piva",""), key="az_piva")
        indir = st.text_input("Indirizzo", azienda.get("indirizzo",""), key="az_indir")
        tel = st.text_input("Telefono", azienda.get("telefono",""), key="az_tel")
        mail = st.text_input("Email", azienda.get("email",""), key="az_mail")
        if st.button("💾 Salva impostazioni", key="az_salva"):
            save_company({
                "ragione_sociale": ragione.strip(),
                "piva": piva.strip(),
                "indirizzo": indir.strip(),
                "telefono": tel.strip(),
                "email": mail.strip(),
            })
            st.success("Impostazioni salvate!")

    with col2:
        st.caption("Logo (PNG/JPG)")
        up = st.file_uploader("Carica logo", type=["png","jpg","jpeg"], key="az_logo")
        if up is not None:
            content = up.read()
            with open(FILES["logo"], "wb") as f:
                f.write(content)
            st.success("Logo aggiornato!")
        if os.path.exists(FILES["logo"]):
            st.image(FILES["logo"], width=150, caption="Logo attuale")                

# --- Export ---
with tabs[4]:
    st.subheader("Esportazioni")
    st.caption("Scarica i registri in CSV per condividerli o importarli altrove.")

    for nome in ["trattamenti", "magazzino", "fertilizzazioni"]:
        path = FILES[nome]
        dati = load_json(path)
        df = pd.DataFrame(dati)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(f"⬇ Scarica {nome}.csv", data=csv, file_name=f"{nome}.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("Export PDF")
    if st.button("📄 Genera PDF trattamenti", key="pdf_tratt"):
        comp = load_company()
        out = generate_treatments_pdf(comp, FILES["logo"], load_json(FILES["trattamenti"]))
        with open(out, "rb") as f:
            st.download_button("⬇ Scarica trattamenti.pdf",
                               data=f.read(), file_name="trattamenti.pdf",
                               mime="application/pdf")
        st.success("PDF generato.")
