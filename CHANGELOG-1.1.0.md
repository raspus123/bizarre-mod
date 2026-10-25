# Bizarre Mod 1.1.0 - modifiche

- 4 tecniche per ciascuno stile: 12 in totale, 9 nuove. B seleziona, C usa.
- Ricariche per tecnica, breve blocco comune di 0,4 secondi; costo solo ad azione riuscita.
- Guanti da boxe permanenti, necessari in una mano per tecniche e passiva Pugilato.
- Click destro sui guanti insegna Pugilato; il vecchio manuale resta compatibile.
- Pergamene Hamon/Spin ridisegnate, descrizioni, ricette e mancato consumo se stile già attivo.
- Attributi base completi dello Stand (incluse estensioni Forge), evento attributi dedicato,
  pacchetto spawn Forge, IA disabilitata, stato attivo solo dopo spawn riuscito.
- UUID evocazione per evitare duplicati; pulizia a morte/cambio dimensione/logout.
- Entità Stand transitorie escluse dal salvataggio; nessuna modifica agli ID esistenti.
- Protocollo di rete 2: aggiornare sia server sia client.

## Limiti della verifica
Il pacchetto contiene sorgenti, NON un JAR compilato. Nell'ambiente di preparazione
non sono disponibili Java, Gradle o Minecraft. I controlli statici non certificano
compilazione o assenza di crash in gioco. Consultare TEST-MANUALE.md e compilare con
il workflow GitHub incluso. Conservare un backup del mondo prima di sostituire la mod.
