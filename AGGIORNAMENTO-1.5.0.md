# Aggiornamento 1.5.0

Minecraft Java 1.16.5 / Forge 36.2.39. **Pacchetto sorgente, non JAR già compilato.**
Client e server devono avere la stessa versione (1.5.0). Protocollo di rete invariato (4).

## Gli Stand eseguono le abilità
- Lo Stand ha un'azione sincronizzata (`ANIM`): **pugni**, **tiro** o **potere**, e si sposta rispetto a te:
  pugni → davanti a te tra te e il bersaglio; tiro → un passo avanti con le braccia tese; potere → vicino a te
  con le braccia alzate; a riposo resta dietro a destra.
- Ogni mossa ha la sua posa: le raffiche (e Donut, Road Roller, Salto nel tempo, Scatto con lo stocco, Dolore
  amplificato) usano i pugni; i colpi a distanza (Star Finger, Coltelli, Crossfire Hurricane, Emerald Splash,
  Tentacoli, monete e Sheer Heart Attack di Killer Queen, Braccio zippato, Fili) usano la posa di tiro e i
  proiettili **partono dalle mani dello Stand** verso il punto che guardi; le altre mosse alzano le braccia.
  Il Time Stop tiene le braccia alzate per tutta la durata.
- Il renderer usa il modello «giocatore» (`PlayerModel`), con poses `BOW_AND_ARROW` e `THROW_SPEAR`.

## Spin 2: Sfera rimbalzante (al posto del Golden Spin)
La sfera rimbalza fino a 3 volte sul nemico valido più vicino (entro 9 blocchi, ogni bersaglio una volta sola),
con 6 danni e Wither a ogni colpo, poi torna da te come le altre tecniche. Lo scatto in avanti è stato tolto.

## Skin degli Stand (64x64, due strati)
Passaggio dal modello umanoide semplice al modello «giocatore» con secondo strato: cinture, fasce, guanti,
stivali, spallacci e stemmi sono in rilievo. Ridisegnate tutte e 11 (colori e tratti tipici di ciascuno).
Lo script `tools/generate_textures.py` rigenera texture degli Stand e icone dell'HUD.

## Oggetti ridisegnati a 32x32
- **Sfera d'acciaio**: acciaio lucido con riflesso e spirale dorata incisa.
- **Maschera di Pietra**: volto di pietra con arcate sopracciliari, occhi incavati, naso, bocca, incisioni e punte.
- **Freccia dello Stand**: punta d'acciaio con foro e alette, asta con fasce dorate, piume rosse e crema.
`tools/generate_item_textures.py` rigenera le texture degli oggetti.

## Verifiche e limiti
`tools/verify_project.py` e `tools/verify_hud.py` controllano struttura, traduzioni, texture e collegamenti: non
equivalgono a una compilazione né a una prova in gioco. Da provare: pose e spostamenti dello Stand (soprattutto
con movimenti rapidi), partenza dei proiettili dalle mani, rimbalzi della sfera, aspetto del modello a due strati.
