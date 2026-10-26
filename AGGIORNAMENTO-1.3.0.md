# Aggiornamento 1.3.0

Minecraft Java 1.16.5 / Forge 36.2.39. **Pacchetto sorgente, non JAR già compilato.**
Protocollo di rete 4: client e server devono avere la stessa versione (1.3.0).

## Spin
- **Lancio della sfera** (tecnica 1, 20 energia, 3 s): lancia una vera sfera d'acciaio. È un proiettile
  rettilineo (entità `steel_ball`, sprite dell'oggetto Sfera d'acciaio) con 9 danni e rallentamento.
  Sparisce all'impatto o dopo 2 secondi; la sfera che tieni in mano non viene consumata.
- **Golden Spin** (il vecchio scatto) passa alla tecnica 2. Vortice rotante e Rotazione difensiva
  restano le tecniche 3 e 4. Il vecchio colpo istantaneo "Steel Ball" è stato sostituito dal lancio.

## HUD in stile Minecraft
- Slot grigi con bordo smussato come la hotbar, cornice bianca sulla tecnica selezionata,
  etichetta azzurra con il tasto tra parentesi (`[V] Star Finger`), numero dello slot in basso a destra.
- Ricarica come per gli oggetti di Minecraft (velo bianco che scende + secondi), icone attenuate
  quando la tecnica non è usabile, barra dell'energia verde come quella dell'esperienza.
- Ritratto dello Stand (volto ricavato dalla sua skin) e icona dello stile nella prima casella.
- I nomi di Stand e stile sono ora tradotti dal client (il pacchetto invia l'id): sui server dedicati
  non compaiono più le chiavi di traduzione. Posizione e scala restano modificabili con K.

## Skin degli Stand
Ridisegnate a mano (64x32) con i tratti riconoscibili di ciascuno: capelli neri e fasce di Star
Platinum, orologio e fascia di The World, cuori di Crazy Diamond, teschio e orecchie di Killer Queen,
coccinella di Gold Experience, elmo con cimiero rosso di Silver Chariot, becco e piume di Magician's
Red, losanghe di Hierophant Green, macchie e secondo volto di King Crimson, cerniere di Sticky
Fingers, fili cuciti di Stone Free. Lo script `tools/generate_textures.py` rigenera tutte le immagini.

## Verifiche e limiti
`python3 tools/verify_project.py` e `python3 tools/verify_hud.py` (eseguiti anche dal workflow) controllano
struttura, traduzioni, texture e collegamenti. **Non equivalgono a una compilazione né a una prova in
Minecraft**: il codice nuovo (proiettile, HUD, render) va compilato con GitHub Actions e provato in gioco.
