import json, os
from datetime import date
import pandas as pd
import streamlit as st
from fpdf import FPDF
import unicodedata
def fmt(x, n=2):
    try:
        return f"{float(x):.{n}f}"
    except:
        return safe_text(x)
def safe_text(s):
    if s is None:
        return ""
    # sostituisce caratteri “tipografici” che bloccano il PDF
    return (
        str(s)
        .replace("–", "-").replace("—", "-")
        .replace("’", "'").replace("‘", "'")
        .replace("“", '"').replace("”", '"')
        .encode("latin-1", "ignore").decode("latin-1")
    )
st.set_page_config(page_title="AgriSmartPro – Demo Web", page_icon="🌾", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "trattamenti": os.path.join(DATA_DIR, "trattamenti.json"),
    "magazzino": os.path.join(DATA_DIR, "magazzino.json"),
    "fertilizzazioni": os.path.join(DATA_DIR, "fertilizzazioni.json"),
    "resi": os.path.join(DATA_DIR, "resi.json"),
    "azienda": os.path.join(DATA_DIR, "azienda.json"),
    "logo": os.path.join(DATA_DIR, "logo.png"),
}
# crea file vuoto se non esiste
if not os.path.exists(FILES["resi"]):
    with open(FILES["resi"], "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
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
def _norm_name(s):
    return str(s or "").strip().lower()

def _normalize_record(p):
    nome = p.get("nome") or p.get("prodotto")
    return {
        "nome": str(nome or "").strip(),
        "lotto": str(p.get("lotto") or p.get("lotto_v2") or ""),
        "unita": (p.get("unita") or "kg"),
        "costo_unitario": float(p.get("costo_unitario", 0) or 0),
        "giacenza": float(p.get("giacenza", 0) or 0),
    }
import re

def _key_tuple(p):
    # Chiave composta (nome, lotto, unita) normalizzata
    return (
        _norm_name(p.get("nome") or p.get("prodotto") or ""),
        (p.get("lotto") or "").strip().lower(),
        (p.get("unita") or "kg").strip().lower(),
    )

def _find_index(lst, nome, lotto, unita):
    # Cerca l'indice di un prodotto nel magazzino in base alla chiave composta
    tgt = (_norm_name(nome or ""), (lotto or "").strip().lower(), (unita or "kg").strip().lower())
    for i, p in enumerate(lst):
        if _key_tuple(p) == tgt:
            return i
    return None

def _label_prodotto(p):
    # Etichetta leggibile per la scelta prodotto
    return f"{p.get('nome') or p.get('prodotto') or ''} | lotto {(p.get('lotto') or '-') } | {(p.get('unita') or 'kg')} | giacenza {p.get('giacenza', 0)}"
def _load_magazzino_list():
    raw = load_json(FILES["magazzino"])
    if isinstance(raw, dict):
        lst, wrap = raw.get("prodotti", []), True
    elif isinstance(raw, list):
        lst, wrap = raw, False
    else:
        lst, wrap = [], False
    return [_normalize_record(p) for p in lst], wrap

def _save_magazzino_list(prod_list, wrap):
    if wrap:
        save_json(FILES["magazzino"], {"prodotti": prod_list})
    else:
        save_json(FILES["magazzino"], prod_list)        
def registra_reso(nome, lotto, unita, quantita, data_iso, operatore, note, segno=1):
    """
    Registra un reso aggiornando la GIACENZA del prodotto giusto
    (match su nome + lotto + unita) e aggiunge la riga nel file 'resi'.
    segno = +1 per rientro in magazzino, -1 per reso a fornitore (scarico)
    """

    # --- Carica il magazzino ---
    prod_list, wrap = _load_magazzino_list()

    # Trova la riga esatta su nome+lotto+unità (normalizzati)
    idx = _find_index(prod_list, nome, lotto, unita)

    # Se non esiste, crea una nuova riga coerente
    if idx is None:
        prod_list.append({
            "nome": nome.strip(),
            "lotto": lotto.strip(),
            "unita": (unita or "kg").strip(),
            "costo_unitario": float(0),
            "giacenza": 0.0,
        })
        idx = len(prod_list) - 1

    # --- Aggiorna la GIACENZA rispettando il segno ---
    nuova = float(prod_list[idx].get("giacenza", 0.0)) + segno * float(quantita)
    if nuova < 0:
        nuova = 0.0  # evita valori negativi
    prod_list[idx]["giacenza"] = nuova

    # --- Salva il magazzino aggiornato ---
    _save_magazzino_list(prod_list, wrap)

    # --- Registra la riga nel file 'resi' ---
    resi = load_json(FILES["resi"])
    if not isinstance(resi, list):
        resi = []

    resi.append({
        "data": data_iso,
        "prodotto": nome.strip(),
        "lotto": lotto.strip(),
        "unita": (unita or "").strip(),
        "quantita": float(quantita) * segno,
        "operatore": operatore or "",
        "note": note or "",
    })

    save_json(FILES["resi"], resi)
# --- LOG SEMPLICE ---
import datetime
def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[LOG {ts}] {msg}")

# === MAGAZZINO su LISTA di righe ===
def load_magazzino():
    """Carica il magazzino (lista di record)."""
    try:
        rows = load_json(FILES["magazzino"])
    except Exception:
        rows = []
    if not isinstance(rows, list):
        # se per caso era in formato vecchio (dict), estrai la lista
        rows = rows.get("prodotti", [])
    return rows


def save_magazzino(rows):
    """Salva il magazzino come lista."""
    save_json(FILES["magazzino"], rows)
    log("[SAVE] magazzino.json aggiornato (lista)")


def scarica_da_magazzino(nome, kg_da_scalare):
    """Scarico per fertilizzazione.
       Cerca per 'prodotto' o 'nome' (case-insensitive) e scala 'giacenza'."""
    rows = load_magazzino()

    # trova il prodotto ignorando maiuscole/spazi
    key_match = str(nome).strip().lower()
    rec = next(
        (r for r in rows
         if str(r.get("prodotto", r.get("nome", ""))).strip().lower() == key_match),
        None
    )

    if rec is None:
        st.warning(f"Prodotto non trovato in magazzino: {nome}")
        log(f"[WARN] Prodotto non trovato in magazzino: {nome}")
        return None

    # usa il campo 'giacenza'
    attuale = float(rec.get("giacenza") or 0)
    to_sub = float(kg_da_scalare or 0)

    if attuale < to_sub:
        log(f"[WARN] Giacenza insufficiente per {nome}: richiesta {to_sub} kg, presenti {attuale} kg")

    rec["giacenza"] = max(0.0, round(attuale - to_sub, 3))
    save_magazzino(rows)

    log(f"[RUN] Scaricati {to_sub} kg di {nome}. Nuova giacenza={rec['giacenza']}")
    return rec
def load_company():
    data = load_json(FILES["azienda"])
    if not data:
        return {"ragione_sociale": "", "piva": "", "indirizzo": "", "telefono": "", "email": ""}
    return data

def save_company(data):
    save_json(FILES["azienda"], data)
class PDF(FPDF):
    # Intercetta e pulisce TUTTO quello che FPDF scrive (testi, metadati, ecc.)
    def _out(self, s):
        if isinstance(s, str):
            s = safe_text(s)
        return super()._out(s)

    def cell(self, w=0, h=0, txt="", *args, **kwargs):
        return super().cell(w, h, safe_text(txt), *args, **kwargs)

    def multi_cell(self, w, h, txt="", *args, **kwargs):
        return super().multi_cell(w, h, safe_text(txt), *args, **kwargs)

    def write(self, h, txt):
        return super().write(h, safe_text(txt))
    def footer(self):
        # spazio riservato in fondo pagina
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.cell(0, 8, safe_text(f"Generato il {date.today().strftime('%d/%m/%Y')} con AgriSmartPro"), 0, 0, "C")
def generate_treatments_pdf(company, logo_path, rows):
    pdf =PDF()
    pdf.add_page()

    def safe_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    # --- Intestazione azienda completa con logo ---
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=20)  # logo a sinistra

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe_text(company.get("azienda", "Azienda agricola")), align="R", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, safe_text(company.get("piva", "")), align="R", ln=1)

    contatti = []
    if company.get("telefono"):
        contatti.append(safe_text(company.get("telefono")))
    if company.get("email"):
        contatti.append(safe_text(company.get("email")))
    if contatti:
        pdf.cell(0, 5, " ".join(contatti), align="R", ln=1)

    if company.get("indirizzo"):
        pdf.cell(0, 5, safe_text(company.get("indirizzo")), align="R", ln=1)

    pdf.ln(8)  # spazio sotto intestazione

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
        pdf.cell(widths[3], 6, fmt(r.get("dose_l_ha")), border=1, align="R")
        pdf.cell(widths[4], 6, fmt(r.get("ettari")), border=1, align="R")
        pdf.cell(widths[5], 6, safe_text(r.get("operatore", ""))[:28], border=1)
        pdf.ln()

    out_path = os.path.join(DATA_DIR, "trattamenti.pdf")
    pdf.output(out_path)
    return out_path
def generate_magazzino_pdf(company, logo_path, rows):
    pdf = PDF()
    pdf.add_page()
    # --- Intestazione azienda (come Trattamenti) ---
    # logo (se presente)
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=20)  # logo a sinistra

    # dati azienda a destra
    pdf.set_font("Arial", "B", 12)
    nome_azienda = company.get("azienda", "")
    pdf.set_font("Arial", "B", 12)
    if nome_azienda:
        pdf.cell(0, 6, f"Azienda agricola {safe_text(nome_azienda)}", align="R", ln=1)
    else:
        pdf.cell(0, 6, "Azienda agricola", align="R", ln=1)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, safe_text(company.get("piva", "")), align="R", ln=1)
    
    contatti = []
    if company.get("telefono"):
        contatti.append(safe_text(company.get("telefono")))
    if company.get("email"):
        contatti.append(safe_text(company.get("email")))
    if contatti:
        pdf.cell(0, 5, " • ".join(contatti), align="R", ln=1)
    # aggiungi indirizzo se presente
    if company.get("indirizzo"):
        pdf.cell(0, 5, safe_text(company.get("indirizzo")), align="R", ln=1)
    pdf.ln(8)  # spazio sotto intestazione
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Magazzino", ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.ln(4)

    headers = ["Prodotto", "Unità", "Giacenza", "Costo unitario"]
    widths = [60, 25, 30, 30]

    for w, h in zip(widths, headers):
        pdf.cell(w, 7, safe_text(h), border=1, align="C")
    pdf.ln()

    for r in rows:
        pdf.cell(widths[0], 6, safe_text(r.get('prodotto', '')), border=1)
        pdf.cell(widths[1], 6, safe_text(r.get('unita', '')), border=1)
        pdf.cell(widths[2], 6, safe_text(r.get('giacenza', '')), border=1, align="R")
        pdf.cell(widths[3], 6, safe_text(r.get('costo_unitario', '')), border=1, align="R")
        pdf.ln()

    out_path = os.path.join(DATA_DIR, "magazzino.pdf")
    pdf.output(out_path)
    return out_path


def generate_fertilizzazioni_pdf(company, logo_path, rows):
    pdf = PDF()
    pdf.add_page()
    # --- Intestazione azienda completa con logo ---
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=20)  # logo a sinistra

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe_text(company.get("azienda", "Azienda agricola")), align="R", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, safe_text(company.get("piva", "")), align="R", ln=1)

    contatti = []
    if company.get("telefono"):
        contatti.append(safe_text(company.get("telefono")))
    if company.get("email"):
        contatti.append(safe_text(company.get("email")))
    if contatti:
        pdf.cell(0, 5, " ".join(contatti), align="R", ln=1)

    if company.get("indirizzo"):
        pdf.cell(0, 5, safe_text(company.get("indirizzo")), align="R", ln=1)

    pdf.ln(8)  # spazio sotto intestazione
    pdf.cell(0, 10, "Registro Fertilizzazioni", ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.ln(4)

    headers = ["Data", "Campo", "Prodotto", "Dose kg/ha", "Ettari", "Operatore"]
    widths = [22, 35, 50, 25, 18, 35]

    for w, h in zip(widths, headers):
        pdf.cell(w, 7, safe_text(h), border=1, align="C")
    pdf.ln()

    for f in rows:
        pdf.cell(widths[0], 6, safe_text(f.get('data', '')), border=1)
        pdf.cell(widths[1], 6, safe_text(f.get('campo', '')), border=1)
        pdf.cell(widths[2], 6, safe_text(f.get('prodotto', '')), border=1)
        pdf.cell(widths[3], 6, fmt(f.get('dose_kg_ha', 0)), border=1, align="R")
        pdf.cell(widths[4], 6, fmt(f.get('ettari', 0)), border=1, align="R")
        pdf.cell(widths[5], 6, safe_text(f.get('operatore', '')), border=1)
        pdf.ln()

    out_path = os.path.join(DATA_DIR, "fertilizzazioni.pdf")
    pdf.output(out_path)
    return out_path
st.title("🌾 AgriSmartPro – Demo Web (MVP)")
# --- Hero Section ---
st.markdown(
    """
    <div style='text-align: center; padding: 40px 0; background: linear-gradient(180deg, #e8f5e9 0%, #ffffff 100%); border-radius: 10px;'>
        <h1 style='color: #2e7d32; font-size: 42px; font-weight: 700;'>
            Gestione Agricola Intelligente
        </h1>
        <p style='font-size: 20px; color: #333;'>
            Ottimizza i trattamenti, i fertilizzanti e il magazzino con AgriSmartPro AI
        </p>
        <div style='margin-top: 20px;'>
            <a href='#' style='background-color:#2e7d32; color:white; padding:12px 24px; text-decoration:none; border-radius:6px; margin-right:10px;'>Inizia</a>
            <a href='#export' style='background-color:#1e88e5; color:white; padding:12px 24px; text-decoration:none; border-radius:6px;'>Visualizza Demo</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
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
            lotto_t = st.text_input("Lotto (opzionale)", key="lotto_t")
            dose = st.number_input("Dose (L/ha)", min_value=0.0, step=0.1)
            ettari = st.number_input("Ettari", min_value=0.0, step=0.1)
        with col3:
            note = st.text_area("Note", height=80)
            if st.button("Salva trattamento"):
                nuovo = {
                    "data": str(data_t),
                    "campo": campo.strip(),
                    "prodotto": prodotto.strip(),
                    "lotto": lotto_t.strip(),
                    "dose_l_ha": dose,
                    "ettari": ettari,
                    "operatore": operatore.strip(),
                    "note": note.strip(),
                }
                dati.append(nuovo)
                save_json(FILES["trattamenti"], dati)
                st.success("Trattamento salvato! Ricarica la pagina per aggiornare la tabella.")
                # --- SCARICO AUTOMATICO DAL MAGAZZINO (TRATTAMENTI, LITRI) ---
                try:
                    qtot = float(dose or 0) * float(ettari or 0)   # L totali usati
                except Exception:
                    qtot = 0.0

                if prodotto and qtot > 0:
                    # usa la tua funzione già esistente (quella che usiamo per le fertilizzazioni)
                    p = scarica_da_magazzino(prodotto, qtot)
                    if p:
                        st.toast(f"Scaricati {qtot} L di {prodotto}. Giacenza residua: {p.get('giacenza', 0)}")
                        st.session_state["_refresh_mag"] = True
                    else:
                        st.warning(f"Prodotto '{prodotto}' non trovato in magazzino: nessuno scarico eseguito.")

                st.rerun()   # aggiorna subito le tabelle    

# --- Magazzino ---
with tabs[1]:
    st.subheader("Magazzino fitosanitari/fertilizzanti")

    raw_mag = load_json(FILES["magazzino"])

    # ✅ compatibilità tra formato desktop ({"prodotti": [...]}) e web (lista [])
    if isinstance(raw_mag, dict):
        dati = raw_mag.get("prodotti", [])
    else:
        dati = raw_mag

    df = pd.DataFrame(dati)
    st.dataframe(df, use_container_width=True)
    with st.expander("➕ Aggiungi/aggiorna voce di magazzino"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            prodotto = st.text_input("Prodotto", "", key="m_prodotto")
            lotto = st.text_input("Lotto (n°/sigla)", value="", key="m_lotto_v2", placeholder="-")
        with col2:
            unita = st.selectbox("Unità", ["L", "kg", "pz"], key="m_unita")
            giacenza = st.number_input("Giacenza", min_value=0.0, step=0.1, key="m_giacenza")
        with col3:
            costo = st.number_input("Costo unitario (€)", min_value=0.0, step=0.01, key="m_costo")
        with col4:
            azione = st.selectbox("Azione:", ["Aggiungi", "Sostituisci/aggiorna"], key="m_azione")

        # --- Pulsanti e logica Magazzino ---

        # 1) SALVA
        if st.button("Salva magazzino", key="m_salva"):

            esistente_idx = _find_index(dati, prodotto, lotto, unita)

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
                    dati[esistente_idx]["giacenza"] = float(dati[esistente_idx].get("giacenza", 0)) + float(giacenza)
                    if costo:
                        dati[esistente_idx]["costo_unitario"] = costo
                else:  # Sostituisci/aggiorna
                    dati[esistente_idx] = voce

            save_json(FILES["magazzino"], dati)
            st.success("Voce di magazzino salvata!")
            st.session_state["_refresh_mag"] = True
            st.rerun()

        # 2) PULISCI
        if st.button("Pulisci campi", key="m_pulisci"):
            for k in ("m_prodotto", "m_lotto_v2", "m_unita", "m_giacenza", "m_costo", "m_azione", "m_lotto"):
                st.session_state.pop(k, None)

            # Dopo il ciclo, reimposta eventuali default
            st.session_state["m_prodotto"] = ""
            st.session_state["m_lotto_v2"] = ""
            st.session_state["m_lotto"] = ""
            st.session_state["m_unita"] = "kg"
            st.session_state["m_giacenza"] = 0.0
            st.session_state["m_costo"] = 0.0
            st.session_state["m_azione"] = "Aggiungi"

            st.success("Campi puliti ✅")
            st.rerun()
# --- BOLLA DI RESO ---
st.divider()
st.subheader("Bolla di reso")

raw = load_json(FILES["magazzino"])

# Normalizza la lista di prodotti (supporta entrambi i formati)
if isinstance(raw, dict):
    prodotti = raw.get("prodotti", [])
elif isinstance(raw, list):
    prodotti = raw
else:
    prodotti = []

# Prende il nome indipendentemente dal campo usato
def _nome(p):
    return str(p.get("prodotto") or p.get("nome") or "").strip()

def _label_prodotto(p):
    nome = p.get("prodotto") or p.get("nome") or ""
    lotto = p.get("lotto") or ""
    unita = p.get("unita") or ""
    giac = p.get("giacenza") or 0
    return f"{nome} | Lotto: {lotto} | {unita} | Giacenza: {giac}"

etichette_prodotti = [_label_prodotto(p) for p in prodotti]

with st.form("form_reso", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        data_reso = st.date_input("Data reso")
    with col2:
        prodotto_sel = st.selectbox("Prodotto", options=(etichette_prodotti or ["(scrivi nome nuovo)"]))
        nuovo_nome = st.text_input("Oppure inserisci nome", value="")
        prodotto_finale = nuovo_nome.strip() if nuovo_nome.strip() else prodotto_sel.split("|")[0].strip()
    with col3:
        quantita_reso = st.number_input("Quantità resa", min_value=0.0, step=1.0)
    # --- Tipo reso (decide se + o -) ---
    tipo_reso = st.selectbox(
        "Tipo reso",
        ["Rientro da campo (+ magazzino)", "Reso a fornitore (- magazzino)"],
        index=0,
        key="m_tipo_reso",
    )
    
    segno = +1 if "Rientro" in tipo_reso else -1
    col4, col5 = st.columns(2)
    with col4:
        operatore_reso = st.text_input("Operatore", value="")
    with col5:
        note_reso = st.text_input("Note", value="")

    st.caption("Il reso aggiornerà automaticamente la giacenza del magazzino.")

    if st.form_submit_button("✓ Registra reso"):
        if not prodotto_finale or float(quantita_reso) <= 0:
            st.error("Inserisci un prodotto valido e una quantità > 0.")
        else:
            # mappa etichetta -> record originale per estrarre lotto/unita
            mappa = { _label_prodotto(p): p for p in prodotti }
        
            # prendi il record selezionato (se esiste)
            rec_sel = mappa.get(prodotto_sel, {})
            nome = (nuovo_nome.strip() if nuovo_nome.strip() else rec_sel.get("nome", prodotto_sel).strip())
            lotto = rec_sel.get("lotto", "")
            unita = rec_sel.get("unita", "kg")
        
            registra_reso(
                nome=nome,
                lotto=lotto,
                unita=unita,
                quantita=quantita_reso,
                data_iso=str(data_reso),
                operatore=operatore_reso,
                note=note_reso,
                segno=segno   # +1 rientro, -1 reso a fornitore
            )
            st.success(f"Reso registrato: {('+' if segno>0 else '')}{quantita_reso} su '{nome}' (lotto {lotto}, {unita}).")
            st.rerun()

# elenco resi registrati (utile per verifica)
st.caption("Resi registrati")
try:
    import pandas as pd
    st.dataframe(pd.DataFrame(load_json(FILES["resi"])), use_container_width=True)
except Exception:
    st.write(load_json(FILES["resi"]))
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
                
                # --- SCARICO AUTOMATICO DAL MAGAZZINO ---
                nome = nuovo.get("prodotto")

                # kg totali usati = dose_kg_ha * ettari
                try:
                    dose = float(nuovo.get("dose_kg_ha") or 0)
                    ett  = float(nuovo.get("ettari") or 0)
                    qkg  = dose * ett
                except Exception:
                    qkg = 0.0

                # (opzionale) messaggio di debug: commenta o rimuovi dopo il test
                st.info(f"DEBUG → nome='{nome}'  dose={dose}  ettari={ett}  qkg_totale={qkg}")

                if nome and qkg > 0:
                    p = scarica_da_magazzino(nome, qkg)
                    if p:
                        save_json(FILES["magazzino"], load_json(FILES["magazzino"]))
                        st.toast(f"Scaricati {qkg} kg di {nome}. Giacenza aggiornata nel magazzino.")
                        st.session_state["_refresh_mag"] = True
                        st.rerun()
                    if p:
                        st.toast(
                            f"Scaricati {qkg} kg di {nome}. Giacenza residua: {p.get('giacenza', p.get('giacenza_kg'))} kg"
                        )
                        st.session_state["_refresh_mag"] = True
                else:
                    st.warning("Prodotto o quantità mancanti: scarico magazzino non eseguito.")
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
def generate_resi_pdf(company, logo_path, rows):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)

    # logo + intestazione
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=25)
        pdf.ln(18)
    pdf.cell(0, 8, safe_text(f"Azienda: {company.get('ragione_sociale','')}"), ln=1)
    pdf.cell(0, 8, "Bolle di reso", ln=1)
    pdf.ln(4)

    # intestazione tabella
    headers = ["data", "prodotto", "quantita", "operatore", "note"]
    colw = [28, 60, 25, 35, 40]
    pdf.set_font("Arial", "B", 10)
    for h, w in zip(headers, colw):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()

    # righe
    pdf.set_font("Arial", "", 10)
    for r in rows:
        pdf.cell(colw[0], 6, str(r.get("data","")), border=1)
        pdf.cell(colw[1], 6, safe_text(str(r.get("prodotto",""))), border=1)
        pdf.cell(colw[2], 6, str(r.get("quantita","")), border=1, align="R")
        pdf.cell(colw[3], 6, safe_text(str(r.get("operatore",""))), border=1)
        pdf.cell(colw[4], 6, safe_text(str(r.get("note",""))), border=1)
        pdf.ln()

    out_path = os.path.join(DATA_DIR, "resi.pdf")
    pdf.output(out_path)
    return out_path
with tabs[4]:
    st.subheader("Esportazioni")
    # --- PDF completo ---
    st.markdown("---")
    st.subheader("📘 Quaderno Completo")

    if st.button("📄 Genera Quaderno Completo PDF"):
        trattamenti = load_json(FILES["trattamenti"])
        magazzino = load_json(FILES["magazzino"])
        fertilizzazioni = load_json(FILES["fertilizzazioni"])
        company = load_company()

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", "", 12)
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Azienda: {company.get('ragione_sociale', '')}", ln=1)
        # --- Intestazione grafica ---
        company_logo_path = os.path.join(DATA_DIR, "logo_agrismartpro.png")
        if os.path.exists(company_logo_path):
            pdf.image(company_logo_path, x=10, y=8, w=25)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, safe_text("Quaderno di Campagna Completo"), ln=1, align="C")
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, safe_text("AgriSmartPro · Quaderno Digitale"), ln=1, align="C")
        pdf.set_draw_color(0, 128, 0)
        pdf.set_line_width(0.6)
        pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
        pdf.ln(6)

        # --- Trattamenti ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Registro Trattamenti", ln=1)
        pdf.set_font("Arial", "", 9)
        for r in trattamenti:
            pdf.cell(
                0, 6,
                safe_text(
                    f"{r.get('data','')} | {r.get('campo','')} | {r.get('prodotto','')} | "
                    f"{fmt(r.get('dose_l_ha'))} | {fmt(r.get('ettari'))} | {r.get('operatore','')}"
                ),
                ln=1
            )
        pdf.ln(4)

        # --- Magazzino ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Magazzino", ln=1)
        pdf.set_font("Arial", "", 9)
        for m in magazzino:
            pdf.cell(
                0, 6,
                safe_text(
                    f"{m.get('prodotto','')} | {m.get('unita','')} | {fmt(m.get('giacenza'))} | {fmt(m.get('costo_unitario'))}"
                ),
                ln=1
            )

        pdf.ln(4)

        # --- Fertilizzazioni ---
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Fertilizzazioni", ln=1)
        pdf.set_font("Arial", "", 9)
        for f in fertilizzazioni:
            pdf.cell(
                0, 6,
                safe_text(
                    f"{f.get('data','')} | {f.get('campo','')} | {f.get('prodotto','')} | "
                    f"{fmt(f.get('dose_kg_ha'))} | {fmt(f.get('ettari'))} | {f.get('operatore','')}"
                ),
                ln=1
            )

        pdf.ln(4)

        out_path = os.path.join(DATA_DIR, "quaderno_completo.pdf")
        pdf.output(out_path)

        with open(out_path, "rb") as f:
            st.download_button(
                "⬇ Scarica Quaderno Completo",
                f,
                file_name="quaderno_completo.pdf",
                mime="application/pdf"
            )

        st.caption("Puoi anche scaricare i registri in CSV qui sotto.")

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
    # --- PDF MAGAZZINO ---
    st.subheader("Esporta PDF Magazzino")
    if st.button("📦 Genera PDF magazzino", key="pdf_mag"):
        comp = load_company()
        pdf_path = generate_magazzino_pdf(comp, FILES["logo"], load_json(FILES["magazzino"]))
        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇ Scarica magazzino.pdf",
                data=f.read(),
                file_name="magazzino.pdf",
                mime="application/pdf"
            )
        st.success("PDF Magazzino generato.")

    # --- PDF FERTILIZZAZIONI ---
    st.subheader("Esporta PDF Fertilizzazioni")
    if st.button("🌾 Genera PDF fertilizzazioni", key="pdf_fert"):
        comp = load_company()
        pdf_path = generate_fertilizzazioni_pdf(comp, FILES["logo"], load_json(FILES["fertilizzazioni"]))
        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇ Scarica fertilizzazioni.pdf",
                data=f.read(),
                file_name="fertilizzazioni.pdf",
                mime="application/pdf"
            )
        st.success("PDF Fertilizzazioni generato.")
    # --- PDF RESI ---
    st.subheader("Esporta PDF Resi")
    resi_rows = load_json(FILES["resi"])
    comp = load_company()
    
    if not resi_rows:
        st.info("Nessun reso registrato al momento.")
    else:
        if st.button("📄 Genera PDF resi", key="pdf_resi"):
            pdf_path = generate_resi_pdf(comp, FILES["logo"], resi_rows)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇ Scarica resi.pdf",
                    data=f.read(),
                    file_name="resi.pdf",
                    mime="application/pdf",
                )
            st.success("PDF Resi generato.")   
