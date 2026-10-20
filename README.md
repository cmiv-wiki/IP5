# IP5 Recorder

Program för att läsa ut och spela in data från en Philips IntelliVue Expression IP5 (MR400) via serieporten.

- Välj serieport och anslut
- Välj vilka parametrar som ska övervakas och spelas in (klicka i tabellen)
- Monitorfönster med realtidsgrafer (tidsfönster 1–120 min)
- Starta/stoppa inspelning, data sparas som TSV

## Inspelningsfiler

Filerna hamnar i vald mapp som `<prefix>_YYYYMMDD_HHMMSS.tsv`. En rad skrivs per post från IP5:an (ungefär 1 Hz)
och filen skrivs till disk efter varje rad, så inget går förlorat om programmet kraschar.

| Kolumn | Innehåll |
|---|---|
| `Time (s)` | Sekunder sedan inspelningens första rad (enligt IP5:ans klocka) |
| `Device time` | Tidsstämpel från IP5:an |
| `PC time` | När datorn tog emot posten |
| `<Parameter> (<enhet>)` | Värde, tomt om det saknas (`?` från enheten eller ej skickat, t.ex. NIBP mellan mätningar) |

Byter en inspelad parameter enhet under inspelningen fortsätter inspelningen i en ny fil (`…_part2.tsv`) med nya rubriker.

## Utveckling

```bash
conda env create -f environment.yml
conda activate ip5
pip install -e .
ip5 --demo        # --demo lägger till en simulerad IP5 i portlistan
pytest tests
```

## Bygga appen

```bash
conda activate ip5
./build_app.sh
```

- macOS: `dist/IP5 Recorder.app`
- Windows: kör `pyinstaller --noconfirm ip5.spec` i en Windows-miljö → `dist/IP5 Recorder/IP5 Recorder.exe`

PyInstaller korskompilerar inte; appen måste byggas på det operativsystem den ska köras på.
Appen är inte signerad, så första gången på en annan Mac: högerklicka → Öppna.

Inställningar (senaste port, mapp, valda parametrar) sparas i `~/.ip5/settings.json`.
