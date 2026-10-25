# Aggiornamento 1.2.0 — GUI JoJo + HUD mobile

## Controlli
- J: menu abilità viola/oro. Schede Stand/Stile, quattro tecniche selezionabili, costo, ricarica e stato.
- K: editor HUD. Trascina con il mouse, rotella per scala (60–150%), frecce per 1 pixel, Shift+frecce per 10 pixel, R per ripristinare.
- Salva/Esci oppure Esc salva posizione, scala e visibilità in config/bizarremod-hud.json.
- Tasti modificabili nel menu Controlli di Minecraft. R/G/V e B/C/X rimangono invariati nel mondo.
- Nell’editor il pannello resta visibile anche quando è impostato su nascosto: serve a poterlo riattivare.

## Inventory HUD+
Non è un'integrazione con l'editor di Inventory HUD e non è richiesta alcuna sua dipendenza. L'HUD di Bizarre ha un editor autonomo: spostalo con K per evitare sovrapposizioni con Inventory HUD+. La mod non modifica file, tasti o rendering di Inventory HUD. La coesistenza NON è stata verificata avviando Minecraft. Se un tasto è occupato, riassegnalo nei Controlli. Il pannello è ancorato in percentuale allo spazio disponibile, viene limitato ai bordi e si adatta ai cambi di risoluzione. Il menu abilità usa lo spazio GUI standard (almeno 320x240).

## Sfere d’acciaio
- Oggetto bizarremod:steel_ball con texture e ricetta: quattro lingotti di ferro a croce e una pepita centrale.
- Necessario nella mano principale O secondaria per TUTTE e quattro le tecniche Spin; non basta averlo nell’inventario.
- Il server controlla l’oggetto prima di energia, ricarica o attacco. Non viene consumato e non insegna da solo lo Spin: serve la pergamena.
- Le tecniche esistenti restano invariate: questa modifica aggiunge l’oggetto richiesto, non una nuova entità proiettile recuperabile.

## Dati e compatibilità
L'HUD riceve dati dal server ogni 5 tick (energia, tecniche, ricariche, equipaggiamento e Stand). Non usa la cache server sul client. Protocollo aggiornato: usare questa stessa versione su client e server. Nessuna dipendenza da Inventory HUD+. La barra di stato ripetuta ogni 3 secondi è rimossa; gli avvisi di combattimento rimangono. L'HUD è nascosto con F1 e quando sono aperti altri menu; non cancella gli eventi overlay delle altre mod.

## Verifiche da eseguire in Minecraft
1. Compilare con il workflow GitHub Actions incluso; installare il JAR Forge 1.16.5 ottenuto, non questo ZIP.
2. Server dedicato: login/logout, morte e cambio dimensione; nessun caricamento di classi client sul server.
3. Imparare Spin: provare C senza sfera, con sfera in inventario, in mano principale e in secondaria. Controllare che solo negli ultimi due casi sia utilizzabile; provare tutte le tecniche.
4. J: selezionare una carta, usare tecnica, controllare energia e ricariche. Provare Stand non evocato e guanti mancanti.
5. K: trascinare, variare scala, nascondere/mostrare, Esc e riavviare il gioco; verificare persistenza. Cambiare risoluzione e scala GUI.
6. Installare la versione Forge 1.16.5 di Inventory HUD+ scelta dall’utente: attivare entrambi gli HUD e spostarli separatamente. Verificare assenza di sovrapposizioni e conflitti tasti.
7. Evocare e congedare tutti gli Stand: la correzione precedente è preservata, ma non è stata provata in gioco.

Nessuna compilazione Forge o prova in gioco è stata eseguita in questo ambiente (Java e Gradle non disponibili). I controlli statici non dimostrano la compatibilità binaria/API né l'assenza di crash.
