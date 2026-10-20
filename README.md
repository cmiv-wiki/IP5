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

## Installation

Kräver [Git](https://git-scm.com/downloads) och [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (eller Anaconda).

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
conda env create -f environment.yml
conda activate ip5
pip install -e .
ip5               # eller: ip5 --demo för att testa utan IP5
```

### Windows

- Kör kommandona ovan i **Anaconda Prompt** (från Start-menyn).
- En USB–seriell-adapter behöver oftast en drivrutin (t.ex. FTDI eller Prolific). Porten syns sedan som `COM3` e.d.
  i Enhetshanteraren och i programmets portlista.

### Linux

- Serieporten heter `/dev/ttyUSB0` (USB–seriell-adapter) eller `/dev/ttyS0`.
- Användaren måste ha behörighet till serieporten. Lägg till dig i gruppen `dialout` (Debian/Ubuntu)
  eller `uucp` (Arch) och logga ut/in:
  ```bash
  sudo usermod -aG dialout $USER
  ```
- "Visa i mapp" använder `xdg-open`, som finns på de flesta skrivbordsmiljöer.

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
- Windows: kör `pyinstaller --noconfirm --clean ip5.spec` i Anaconda Prompt → `dist\IP5 Recorder\IP5 Recorder.exe`
- Linux: `./build_app.sh` → `dist/IP5 Recorder/IP5 Recorder`

På Windows och Linux är appen en mapp; kopiera hela mappen `IP5 Recorder`, inte bara den körbara filen.

PyInstaller korskompilerar inte; appen måste byggas på det operativsystem den ska köras på.
Appen är inte signerad:
- macOS: första gången, högerklicka → Öppna.
- Windows: om SmartScreen varnar, klicka "Mer information" → "Kör ändå".

Inställningar (senaste port, mapp, valda parametrar) sparas i `~/.ip5/settings.json`
(Windows: `C:\Users\<namn>\.ip5\settings.json`). Inspelningar hamnar som standard i `~/Documents/IP5 recordings`.
