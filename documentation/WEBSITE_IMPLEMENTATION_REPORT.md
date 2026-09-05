# Rapporto di implementazione del redesign

Data: 23 luglio 2026
Branch: `feature/public-website-redesign`
Stato: anteprima locale, non pubblicata

## Stato iniziale

- dominio `www.agrismartpro.com`;
- GitHub Pages;
- un solo `index.html`;
- repository `agrismartpro/agrismartpro_demo_web`;
- prezzi e Payment Link pubblicati;
- collegamento a demo Streamlit legacy basata su file JSON;
- nessuna pagina legale collegata.

Il file online iniziale misurava 6.426 byte e aveva SHA-256:

`b70dbe41f0e62b6c2e1abd811b966d090b550a1374f4e48881d74d5d27d68f8a`.

## Backup

È stato creato il tag locale annotato:

`backup/public-website-before-redesign-2026-07-23`

sul commit:

`a0555182702b7b8b446e66dc634d3c9c22cbae6b`.

Il tag non è stato pubblicato.

## Implementazione

- generatore statico senza dipendenze;
- template condivisi;
- configurazione esterna dei collegamenti applicativi;
- design mobile-first;
- dodici pagine;
- metadata SEO e Open Graph;
- favicon e manifest;
- immagine reale agricola;
- controlli automatici di struttura e contenuto;
- nessun backend;
- nessuna scrittura Firebase;
- nessun collegamento Stripe.

## Collegamenti applicativi

Nessun URL applicativo, di login, registrazione o Pilot viene configurato o
generato: le richieste di accesso passano dal canale pubblico di contatto.

## Richiesta demo

Usa un collegamento email. Non persiste dati e non crea account.

## Confini

Non sono stati modificati:

- sito online;
- DNS;
- branch `main`;
- app Streamlit;
- Firebase;
- catalogo regolatorio;
- dati Customer Zero;
- Stripe.

## Elementi da approvare

- copy della Home;
- stato pubblico di ogni funzione;
- testi Chi siamo;
- Privacy, Termini e Cookie;
- URL applicativi;
- eventuali profili social;
- modalità futura della richiesta demo.
