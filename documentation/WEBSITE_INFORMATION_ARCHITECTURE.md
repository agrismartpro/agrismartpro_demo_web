# Architettura informativa del sito AgriSmartPro

Versione: 1.0
Data: 23 luglio 2026
Stato: implementata in anteprima

## Tecnologia scelta

Il sito usa HTML e CSS statici generati da uno script Python standard.

### Confronto

| Soluzione | Vantaggi | Svantaggi | Decisione |
|---|---|---|---|
| HTML/CSS multipagina generato | nessuna dipendenza, GitHub Pages diretto, controllo completo, manutenzione semplice | il generatore è specifico del progetto | **Scelta** |
| Jekyll | integrato con GitHub Pages, layout condivisi | ambiente Ruby e convenzioni meno familiari al progetto | non scelto |
| Astro static export | componenti moderni, ottimo SEO, sviluppo evoluto | dipendenze Node e workflow di build aggiuntivo | rinviato |
| Altro generatore | possibile flessibilità | nessun vantaggio concreto nel perimetro corrente | non necessario |

La soluzione scelta mantiene il sito attuale e produce direttamente i file
serviti da GitHub Pages.

## Struttura

```text
site_config.json
site/
├── pages.json
├── content/
└── templates/
scripts/
├── build_site.py
└── check_site.py
assets/
index.html
<slug>/index.html
CNAME
```

## Mappa delle pagine

```text
Home
├── Funzionalità
├── Centro Conformità
├── Catalogo Regolatorio
├── Customer Zero
├── Prezzi
├── Chi siamo
├── FAQ
├── Contatti
└── Footer
    ├── Privacy
    ├── Termini
    └── Cookie
```

## Navigazione

La navigazione principale privilegia:

1. Funzionalità;
2. Centro Conformità;
3. Programma pilota;
4. Prezzi;
5. Chi siamo;
6. FAQ.

Accesso e Registrazione vengono generati soltanto se i relativi URL sono
presenti nella configurazione approvata.

## Richiesta demo

La prima versione usa `mailto:info@agrismartpro.com`. Non crea dati, account,
Trial o aziende.

Un futuro modulo dovrà prevedere:

- validazione;
- consenso Privacy obbligatorio;
- consenso marketing separato;
- protezione anti-spam;
- ricevuta;
- stato della richiesta;
- regole di conservazione;
- notifica interna.

## Rendering e pubblicazione

Lo script di build legge configurazione, metadati, contenuti e template,
generando HTML statico nella radice. `CNAME` resta invariato. Nessuna parte
dell'app Streamlit viene incorporata nel sito.
