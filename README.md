# Novità 1.2.0

Leggi `AGGIORNAMENTO-1.2.0.md` per GUI, HUD spostabile e sfere d’acciaio.

# Bizarre Mod 1.1.0 - Minecraft Java 1.16.5 / Forge 36.2.39

**Pacchetto sorgente aggiornato, non JAR già compilato.** Salva un backup del mondo.
La versione deve coincidere su client e server (protocollo di rete 2).

## Ottenere il JAR con GitHub Actions
1. Estrai lo ZIP e carica la struttura in un repository GitHub, includendo `.github`.
2. Apri Actions: il workflow **Compila la mod** parte al push; è disponibile anche l'avvio manuale.
3. I controlli statici vengono eseguiti prima di `gradle build`. Attendi che la build risulti riuscita.
4. Scarica l'artifact **bizarre-mod-1.16.5**: contiene `bizarremod-1.1.0.jar` reobfuscato.
5. Con Minecraft chiuso, sostituisci la vecchia versione nella cartella `mods` di Forge 1.16.5.
   Non tenere contemporaneamente due JAR della stessa mod. Aggiorna anche il server se presente.
Se fallisce, conserva l'artifact `log-compilazione`. Non rinominare lo ZIP in `.jar`.

Build locale, se hai Java 8 e Gradle 7.4.2: `gradle build --no-daemon`.
Il progetto richiede accesso ai repository Forge/Maven per scaricare le dipendenze.

## Controlli predefiniti (rimappabili da Opzioni > Comandi)
| Tasto | Azione |
|---|---|
| R | Evoca / richiama lo Stand |
| G | Seleziona una delle 4 mosse dello Stand |
| V | Usa la mossa selezionata dello Stand |
| B | Seleziona una delle 4 tecniche dello stile |
| C | Usa la tecnica selezionata dello stile |
| X | Abilità della razza |

Le selezioni dello Stand e dello stile sono indipendenti. La barra mostra nome,
costo e ricarica quando selezioni una tecnica. Le ricariche della tabella sono
in secondi a 20 tick/s; tra due tecniche dello stile servono almeno 0,4 secondi.
Una tecnica fallita per assenza di bersaglio, energia o guanti non consuma energia.

## Pergamene e guanti
- **Pergamena Hamon**: click destro per attivare Hamon, poi si consuma in sopravvivenza.
- **Pergamena Spin**: click destro per attivare Spin, poi si consuma in sopravvivenza.
- Se lo stile è già attivo la pergamena NON viene consumata. Le pergamene non devono
  restare in mano dopo l'apprendimento. Sono state ridisegnate: sole oro / spirale verde.
- **Guanti da boxe**: click destro per attivare Pugilato; NON si consumano e non si usurano.
  Devi tenerli nella **mano principale o secondaria** per usare le 4 tecniche e la passiva.
  Nell'inventario o a terra non bastano. Sono un oggetto da tenere in mano, non un'armatura.
- Il **Manuale di Pugilato** esistente è ancora disponibile, ma richiede i guanti in una mano.
- Un solo stile è attivo alla volta: impararne un altro lo sostituisce. Si possono usare gli
  operatori `/jojo style hamon`, `/jojo style spin`, `/jojo style boxing` per le prove;
  il comando non elimina il requisito dei guanti per usare Pugilato.

Oggetti disponibili nella scheda creativa **Bizarre Mod**; per i guanti puoi anche
usare `/give @s bizarremod:boxing_gloves` con i permessi necessari.

### Ricette (griglia 3×3)
**Guanti:** `L L / LWL /  R ` - L = cuoio, W = lana rossa, R = filo.

**Hamon:** `PGP / PSP / PYP` - P = carta, G = lingotto d'oro, S = girasole, Y = colorante giallo.

**Spin:** `PIP / PEP / PGP` - P = carta, I = lingotto di ferro, E = perla di Ender, G = colorante verde.

Le ricette si sbloccano nel ricettario raccogliendo carta o cuoio.

## Tecniche degli stili
I danni indicati sono punti vita nominali prima di armatura, resistenze e altre modifiche.

| Stile | Tecnica | Energia | Ricarica | Effetto principale |
|---|---|---:|---:|---|
| Hamon | Sunlight Yellow Overdrive | 30 | 3 s | Onda a 5 blocchi; bonus contro non morti, piccola cura |
| Hamon | Scarlet Overdrive | 25 | 4 s | Bersaglio a 4,5 blocchi, 8 danni (14 ai non morti) e fuoco |
| Hamon | Respirazione Hamon | 20 | 10 s | Cura 4 punti vita, rigenerazione 5 s, resistenza 3 s; solo Umani |
| Hamon | Onda solare | 35 | 6 s | Cono a 6 blocchi, 6 danni, rallentamento e debolezza |
| Spin | Golden Spin | 30 | 3 s | Scatto rotante con 7 danni sui bersagli davanti e Wither |
| Spin | Steel Ball | 20 | 3 s | Colpo istantaneo a 14 blocchi, 8 danni e rallentamento |
| Spin | Vortice rotante | 30 | 6 s | Area a 4 blocchi, 6 danni, respinta e rallentamento |
| Spin | Rotazione difensiva | 25 | 9 s | Resistenza II per 5 s e velocità per 3 s |
| Pugilato | Jab combinati | 20 | 2 s | Quattro colpi da 2 danni a 3 blocchi, breve velocità |
| Pugilato | Gancio pesante | 30 | 4,5 s | 10 danni, forte respinta e debolezza a 3 blocchi |
| Pugilato | Montante | 25 | 3,5 s | 7 danni, sollevamento e rallentamento a 3 blocchi |
| Pugilato | Guardia del pugile | 20 | 8 s | Resistenza II per 4 s, rallentamento per 2 s |

La Steel Ball è una tecnica hitscan con particelle: non aggiunge un proiettile o un
oggetto palla separato. Le tecniche rispettano visuale libera, squadre e PvP disabilitato.
Passiva Pugilato: +20% alla velocità mentre i guanti sono tenuti in mano;
il modificatore viene rimosso al tick successivo quando li togli.
Le abilità consumano energia, che si rigenera da sola. Hamon rigenera più energia al sole.

## Stand e razze
- Freccia dello Stand: click destro, assegna uno degli 11 Stand.
- Maschera di Pietra: Umano → Vampiro; Pietra Rossa di Aja: Vampiro → Uomo del Pilastro;
  Siero dell'Umanità: ritorno a Umano.
- Operatori: `/jojo stand star_platinum`, `/jojo race vampire`.
- Dopo morte, cambio dimensione o riconnessione, premi R per evocare di nuovo lo Stand.

## Correzione evocazione e limiti della verifica
La precedente mappa attributi dello Stand veniva costruita da zero e non ereditava
attributi Forge richiesti, inclusa la gravità. Ora eredita il builder completo di MobEntity;
sono stati aggiunti evento attributi dedicato, pacchetto spawn Forge e gestione sicura
dello stato evocato. Non viene salvata un'entità Stand orfana nel mondo.

I controlli statici NON equivalgono a compilazione o prova in Minecraft. In questa
preparazione non è stato eseguito un client/server Minecraft e non è stato prodotto
un JAR. Vedi **TEST-MANUALE.md** e **CHANGELOG-1.1.0.md**. Se il crash continua dopo
una build riuscita, conserva `crash-reports/*.txt` e `logs/latest.log` insieme alla
versione Forge e all'elenco delle altre mod.

## Moveset degli Stand (ordine di selezione con G: raffica, poi le 3 abilita')
- Star Platinum: ORA ORA | Star Finger (colpo a 12 blocchi) | Inala (trascina i nemici) | Time Stop 2s
- The World: MUDA MUDA | Coltelli (a distanza, sanguinamento) | Road Roller (onda d'urto) | Time Stop 5s
- Crazy Diamond: DORA DORA | Restore (cura, ripara) | Onda curativa (giocatori vicini) | Guardia (assorbimento)
- Killer Queen: Kill Barrage | Bomba su entita' | Bomba su blocco | Sheer Heart Attack (3 mostri vicini)
- Gold Experience: MUDA MUDA | Life Giver (piante + rigenerazione) | Dolore amplificato | Senso della vita (fa brillare i viventi)
- Silver Chariot: stoccate a lungo raggio | Armor Off | Scatto con lo stocco | Parata
- Magician's Red: pugni di fuoco | Crossfire Hurricane | Red Bind (cerchio di fuoco) | Muro di fuoco
- Hierophant Green: Emerald Splash (raffica a distanza) | Tentacoli (trascina) | Rete di tentacoli (rallenta area) | Infiltrazione (veleno)
- King Crimson: Death Chop | Donut | Erase Time | Salto nel tempo (colpo alle spalle)
- Sticky Fingers: ARI ARI | Zipper (teletrasporto) | Braccio zippato (indebolisce) | Onda zip (lancia in aria)
- Stone Free: ORA ORA | Fili (immobilizza) | Ali di filo | Rampino di filo
