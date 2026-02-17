# Mao Simulator

Això és un simulador del Mao. Simula una partida del Mao amb el joc base.
Per això, important: **SI NO SAPS JUGAR AL MAO, NO MIRIS LES NORMES AQUI VES-T'EN**

Tenim els següents fitxers:
- `base/clases.py`: Conté les classes necessàries per definir una carta, una mà de cartes (les piles són baralles d'on es poden transferir cartes al cap i a la fi) i les estratègies (derivades de `Strategy`)

- `base/logger.py`: Un logger molt estupid, tbh. Logeja debug a un file `{nom_del_programa}_{num_players}_{num_baralles}_{Estrategies_Separades_Per_Guio}.log` i per consola fent servir `coloredlogs`.

- `base/sim.py`: El simulador. Mucho texto, funciona com hauria de funcionar i si no ho fa digueu-me, continua llegint per saber coses necessàries.

- `scripts/remove_junk.sh`: Script simple per eliminar tots els `.log` i `.json` a la carpeta. Important cridar-ho a la carpeta adecuada.

- `scripts/update_all_strategies.py` i el que hi ha a `.github/**` es per fer que les PR es facin via jam

---

# Mao Jam
Com sap la melmelada de Mao? No ho sé, per això anem a descobrir-ho

## Fitxers enfocats a la Jam:
- `test_simulator.py`: Un exemple de com es crida el simulador.

- `my_strategies.py`: Un exemple de quins mètodes s'han d'implementar.

- `all_strategies.py`: Fitxer on s'afegiran les estratègies. S'importen i s'afegeixen a `strategies` per poder-les avaluar. 

- `simulator_combined_stategies.py`: Fitxer que avaluarà el rendiment de les estratègies amb les competidores, ho farà mitjançant les combinacions de estratègies. Qui guanyi més, guanyarà. 

## Funcionament:

`git pull` aquest repo, fas `strategies/alies_strategies.py` on `alies` és el teu àlies (nom, username de github, el que tu vulguis), el testejes tot el que vulguis, fas una pull request que serà automàticament acceptada si només has editat `strategies/alies_strategies.py`. **Important: ha d'acabar en `_strategies.py` i ha de estar a `strategies/`**

No pots canviar res més (a no ser que sigui un error del simulador que fa algo quan no toca), només allò.

### Deadlines:
No n'hi ha. Quan hi vegi un canvi, ho executaré. 

### Limits:
No n'hi ha però si veig que triga massa al meu ordinador o no tinc suficient memòria, coses de l'estil, ho descartaré.

## Leaderboard:
S'inaugurarà el 23 de febrer. 
| Posició | Àlies |Estratègia  | Victòries |
|---------|---|---------------|----------|
| 1 | NO | Encara no | 42
