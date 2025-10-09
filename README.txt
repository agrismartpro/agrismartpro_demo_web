
# AgriSmartPro – Demo Web (Streamlit)

Questa è una demo web **molto semplice** per mostrare i moduli base:
- Trattamenti
- Magazzino
- Fertilizzazioni
- Esportazione CSV

I dati sono salvati in `data/*.json`.

## Come avviare in locale
1) Installa i pacchetti
```
pip install -r requirements.txt
```
2) Avvia l'app
```
streamlit run app.py
```
Si aprirà una pagina web locale (es. http://localhost:8501).

## Note
- La demo non ha autenticazione: è solo per provare rapidamente il flusso.
- Per il deploy veloce puoi usare Streamlit Community Cloud oppure un server tuo.
- In una versione successiva potremo aggiungere login, PDF export e FastAPI backend.
