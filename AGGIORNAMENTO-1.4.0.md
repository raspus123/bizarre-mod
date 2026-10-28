# Aggiornamento 1.4.0

Minecraft Java 1.16.5 / Forge 36.2.39. **Pacchetto sorgente, non JAR già compilato.**
Nuove entità e nuovi oggetti nel registro: client e server devono avere la stessa versione (1.4.0).

## Spin: la sfera parte e torna da te
Tutte e quattro le tecniche dello Spin lanciano la sfera d'acciaio, e la sfera rientra sempre:
1. **Lancio della sfera**: vola dritta (9 danni, rallentamento); dopo l'impatto o 9 tick torna da te
   colpendo di nuovo (5 danni) chi incontra al ritorno.
2. **Golden Spin**: lancio rotante con Wither mentre ti lanci in avanti; la sfera ritorna.
3. **Vortice rotante**: due sfere orbitano a 4 blocchi per 2,5 s, poi tornano.
4. **Rotazione difensiva**: tre sfere orbitano vicino per 4 s e colpiscono chi si avvicina; poi tornano.
La sfera in mano non viene mai consumata. Le sfere seguono il giocatore e spariscono se lui muore o esce.

## Raffica di pugni come prima mossa
La prima mossa di ogni Stand è una raffica di pugni, ora a ondate: lo Stand muove il braccio e colpisce
una volta ogni 2 tick (stesso danno totale di prima, distribuito in circa mezzo secondo).
Hierophant Green aveva Emerald Splash come prima mossa: ora ha *Raffica di pugni* in prima posizione,
*Emerald Splash* in seconda, Tentacoli in terza e Rete di tentacoli in quarta (**Infiltrazione è stata tolta**).

## Mosse a distanza = proiettili
Star Finger, Coltelli (5, a ventaglio), Crossfire Hurricane (3 palle di fuoco), Emerald Splash (10 smeraldi),
Tentacoli (trascina), Bomba su entità/blocco di Killer Queen (monete che esplodono all'impatto),
Sheer Heart Attack (3 bombe che inseguono i mostri), Braccio zippato, Fili e gli occhi del Vampiro
non sono più colpi istantanei ma proiettili visibili (entità `stand_shot`, sprite dell'oggetto scelto).

## Texture
- Nuove, a mano: Freccia dello Stand, Pergamena dell'Hamon, Pergamena dello Spin, Manuale di Pugilato,
  Maschera di Pietra, Pietra Rossa di Aja, Sfera d'acciaio (prima quasi invisibile).
- Tre oggetti nascosti per gli sprite dei proiettili (coltello, stella, cerniera): niente creativo né ricette.
- `python3 tools/generate_item_textures.py` rigenera le texture degli oggetti.

## Verifiche e limiti
`tools/verify_project.py` e `tools/verify_hud.py` (eseguiti anche dal workflow) controllano struttura,
traduzioni, texture e collegamenti: **non equivalgono a una compilazione né a una prova in gioco**.
Parti più delicate da provare: movimento fluido delle sfere in orbita/ritorno, sprite dei proiettili e
animazione dei pugni dello Stand.
