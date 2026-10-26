# Checklist di prova in Minecraft - Bizarre Mod 1.1.0

Questi sono test DA ESEGUIRE, non risultati già verificati. Usare un mondo di prova
con backup e Forge 1.16.5-36.2.39. Prima provare senza altre mod.

## 1. Build e controlli statici
- Eseguire `python3 tools/verify_project.py` (sola libreria standard Python).
- Compilare con Java 8, Gradle 7.4.2 e `gradle build --no-daemon` o GitHub Actions.
- Verificare che il JAR sia reobfuscato e che la versione sia 1.1.0.
- I test statici controllano struttura e risorse, non eseguono le abilità Java.

## 2. Evocazione: regressione crash
- Per ciascuno degli 11 ID assegnare `/jojo stand <id>`:
  star_platinum, the_world, crazy_diamond, killer_queen, gold_experience,
  silver_chariot, magicians_red, hierophant_green, king_crimson,
  sticky_fingers, stone_free. Confermare gli ID con l'autocompletamento del comando.
- Premere R, verificare che modello e texture appaiano; aspettare almeno 30 secondi.
- Alternare rapidamente R, camminare, nuotare, volare in creativa e attaccare.
- Provare G e V; nessun errore attributi null nel log, nessun duplicato permanente.
- Con Stand evocato: morte/respawn, portale Nether, logout/login, chiusura/riapertura
  del mondo, cambio Stand da comando e da freccia. R deve evocare normalmente dopo.
- Su server dedicato con due client: ognuno deve vedere entrambi gli Stand;
  scollegare un proprietario non deve lasciare il suo Stand attivo.

## 3. Pergamene e ricette
- In sopravvivenza imparare Hamon e Spin: una pergamena consumata solo se cambia stile.
- Usare nuovamente lo stesso stile: nessun consumo, messaggio esplicito.
- In creativa: niente consumo. Controllare immagini, tooltip e traduzioni it_it/en_us.
- Eseguire le tre ricette e controllare lo sblocco nel ricettario dopo carta/cuoio.

## 4. Guanti e Pugilato
- Click destro sui guanti: impara Pugilato senza consumare i guanti.
- Attaccare un bersaglio: B seleziona fra 4 tecniche, C usa la selezionata.
- Provare guanti in mano principale, poi secondaria: entrambe devono funzionare.
- Spostarli nell'inventario, gettarli o usare `/clear`: tutte le tecniche vanno bloccate
  senza spesa di energia; il bonus passivo deve cessare al tick successivo.
- Usare `/jojo style boxing` senza guanti non deve aggirare il blocco delle tecniche.
- Manuale di Pugilato: richiede guanti nell'altra mano e si consuma solo al cambio stile.
- Cambiare stile con guanti ancora in mano: il bonus passivo Pugilato deve cessare.

## 5. Moveset, energia e bersagli
- Per ogni stile selezionare tutte le 4 tecniche con B e usarle con C.
- La selezione B non deve modificare G e viceversa; controllare nomi/costi/ricariche.
- Dopo una tecnica, spammare C e cambiare B: ricariche individuali e gate 0,4 s rispettati.
- Con energia insufficiente: nessuna azione. Colpi senza bersaglio: nessuna spesa.
- La Respirazione Hamon deve funzionare solo per Umani, senza spesa sugli altri.
- Spin, Lancio della sfera: con la sfera in mano, tecnica 1 dello Spin. Deve partire un proiettile
  visibile (sprite della sfera) che colpisce mostri e giocatori consentiti, sparisce contro un muro e
  dopo circa 2 secondi, e NON consuma la sfera in mano. Senza sfera in mano non deve partire nulla.
- Spin, Golden Spin: ora è la tecnica 2 (scatto con Wither); Vortice e Rotazione difensiva restano 3 e 4.
- Alleati di squadra e giocatori con PvP disabilitato non devono essere danneggiati
  dalle nuove tecniche. Ripetere per le tecniche Hamon/Spin/Pugilato preesistenti.
- Uscire e rientrare: stile e selezione preservati, Stand non attivo finché non si preme R.

## 6. HUD in stile Minecraft e skin (1.3.0)
- L'HUD mostra due righe (Stand, stile): casella con il ritratto/icona e 4 slot grigi come la hotbar.
  La tecnica scelta ha la cornice bianca e sotto compare `[V] nome` (Stand) o `[C] nome` (stile) in azzurro.
- Cambiare tecnica con G/B: la cornice bianca deve spostarsi e il nome cambiare.
- Dopo l'uso di una tecnica: velo bianco di ricarica che scende nello slot e secondi al centro.
- Con energia insufficiente o Stand non evocato: le icone devono apparire attenuate.
- Barra verde dell'energia come la barra dell'esperienza; K sposta l'HUD, J apre la schermata abilità.
- Su un server dedicato i nomi di Stand e stile devono comparire tradotti (non come `stand.bizarremod...`).
- Skin: evocare ciascuno degli 11 Stand (`/jojo stand <id>`, tasto R) e controllare volto, capelli/cresta,
  petto e fasce; il modello deve apparire con i colori dello Stand, senza texture viola/nera a quadri.

## In caso di errore
Conservare versione Java/Forge, artifact log-compilazione per errori di build, oppure
crash-reports e latest.log per errori in gioco. I test non eseguiti non vanno segnati riusciti.
