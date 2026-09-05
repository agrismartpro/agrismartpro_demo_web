# Sito pubblico AgriSmartPro

Repository del sito istituzionale pubblicato su GitHub Pages all'indirizzo
`www.agrismartpro.com`.

Il sito pubblico è separato dall'applicazione operativa. Le pagine sono
generate come HTML statico, senza backend e senza dipendenze esterne:

```bash
python3 scripts/build_site.py
python3 -m http.server 8080
```

La configurazione dei canali per richiedere una demo o informazioni sul
programma pilota si trova in `site_config.json`. Il sito pubblico non espone
collegamenti diretti all'applicazione, all'accesso o alla registrazione.
