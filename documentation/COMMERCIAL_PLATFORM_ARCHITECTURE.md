# Architettura commerciale AgriSmartPro

Versione: 1.0
Data di approvazione: 23 luglio 2026
Stato: architettura commerciale di riferimento

## Scopo

La piattaforma commerciale accompagna il cliente lungo il percorso:

`Visitatore → Registrazione → Trial → Customer Zero/Pilota → Scelta piano →
Checkout → Attivazione → Area Cliente → Rinnovo o disdetta`.

Il sito istituzionale, l'applicazione operativa, l'identità, la fatturazione e
le autorizzazioni applicative restano componenti separati.

## Principi

1. Stripe non è la fonte di verità dell'identità o dei permessi.
2. Il browser non sceglie liberamente azienda, piano o prezzo.
3. Un redirect di pagamento non concede accesso.
4. Gli eventi commerciali devono essere confermati lato server e processati in
   modo idempotente.
5. La cancellazione non elimina automaticamente i dati aziendali.
6. Trial e programma pilota non richiedono un prodotto Stripe.
7. Il dominio commerciale deve rimanere indipendente dal fornitore di
   pagamento.
8. Test, anteprima e produzione sono ambienti separati.
9. Nessuna modalità Stripe live viene attivata senza autorizzazione dedicata.

## Componenti

```text
Sito istituzionale
  → Identità e account
    → Customer Journey
      → Dominio commerciale
        → Porta del provider di pagamento
          → Adapter Stripe
```

### Fonti di verità

| Informazione | Fonte |
|---|---|
| Identità utente | servizio di identità dell'app |
| Azienda e membership | dominio AgriSmartPro |
| Trial | dominio commerciale AgriSmartPro |
| Piano assegnato | sottoscrizione interna riconciliata |
| Pagamento e fatture | provider di pagamento |
| Funzioni abilitate | servizio autorizzativo AgriSmartPro |
| Decisioni normative | futuro motore di conformità |

## Sito pubblico

Il sito pubblico:

- presenta il prodotto e il programma pilota;
- distingue funzioni disponibili, in validazione, pianificate e future;
- non contiene dati operativi;
- non dipende da Streamlit per essere renderizzato;
- collega Accesso e Registrazione solo dopo il collaudo degli URL;
- usa un canale non persistente per le prime richieste demo;
- non pubblica prezzi non approvati;
- non crea account, Trial o aziende.

## Percorso commerciale

Stati principali previsti:

```text
VISITOR
→ REGISTERED_UNVERIFIED
→ REGISTERED_VERIFIED
→ TRIAL_ACTIVE
→ PILOT_ACTIVE
→ PLAN_SELECTION_REQUIRED
→ CHECKOUT_PENDING
→ SUBSCRIPTION_PENDING_CONFIRMATION
→ SUBSCRIPTION_ACTIVE
→ PAST_DUE
→ GRACE_PERIOD
→ RESTRICTED
→ CANCELLATION_SCHEDULED
→ CANCELED
→ REACTIVATED
```

Gli stati commerciali sono distinti dallo stato di onboarding dell'azienda.

## Trial e programma pilota

La prima proposta prevede un Trial applicativo senza carta:

- durata e limiti ancora da approvare;
- nessun rinnovo automatico;
- nessuna sottoscrizione Stripe creata all'avvio;
- conversione esplicita futura.

Customer Zero e programma pilota sono percorsi interni di validazione, non
piani Stripe.

## Integrazione Stripe futura

L'integrazione prevista comprende:

- Checkout ospitato;
- Customer Portal;
- fatture;
- rinnovi;
- upgrade e downgrade;
- cancellazione e riattivazione;
- gestione dei mancati pagamenti;
- webhook verificati;
- riconciliazione periodica.

Gli identificativi dei prezzi non saranno codificati nell'interfaccia e non
saranno accettati liberamente dal browser.

## Sicurezza

- chiavi segrete esclusivamente lato server;
- firma dei webhook verificata;
- elaborazione idempotente;
- contesto aziendale derivato dalla sessione autorizzata;
- audit delle azioni commerciali;
- nessun dato di pagamento conservato da AgriSmartPro;
- separazione completa tra ambiente di prova e ambiente live.

## Decisioni necessarie prima di Stripe

- soggetto venditore e forma giuridica;
- perimetro B2B/B2C;
- mercato iniziale;
- prezzi definitivi;
- fatturazione mensile o annuale;
- durata del Trial;
- gestione IVA e fatturazione elettronica;
- grace period;
- rimborsi;
- conservazione dei dati dopo cancellazione;
- testi contrattuali.

## Roadmap commerciale

1. sito pubblico;
2. dominio commerciale;
3. adapter Stripe esclusivamente in ambiente di prova;
4. Area Cliente;
5. ciclo completo di pagamento simulato;
6. revisione fiscale, legale e di sicurezza;
7. attivazione controllata con autorizzazione separata.

## Stato

L'Incremento 1 riguarda esclusivamente il sito pubblico. Stripe, prezzi reali,
pagamenti, Firebase e dati Customer Zero restano fuori dal perimetro.
