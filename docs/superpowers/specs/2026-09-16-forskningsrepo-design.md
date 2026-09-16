# Forskningsrepo: mall för doktorandforskning med agentstöd

Datum: 2026-09-16. Beställare: Fabian von Tiedemann. Mottagare: Amanda, doktorand, kör Codex och GitHub.

## Syfte

Ett mallrepo (GitHub template repository under `fabian-von-tiedemann/forskningsrepo`) som en doktorand kan skapa sitt eget forskningsrepo från och vara igång med på en timme. Repot bär en arbetsmetod, inte ett ämne: frågor med argumentkedja, prov med mått låsta före mätning, versionsbundna kunskapskedjor med källutdrag, beslutslogg och regler som agenten läser vid start.

Förlagan är `framtidens-arbetssatt`. Därifrån tas formen, inte innehållet.

## Vad som tas med från förlagan, och vad som lämnas

| Tas med | Lämnas |
|---|---|
| `harness/registry.py`, `harness/common.py` (de delar registry behöver), `tests/test_registry.py` | `runner`, `evaluator`, `transfer`, `requests`, `comparison`, `worker`, `http_worker`, `workflow`, `adapters`, `reasoning` och deras tester: kanalsimulator för U004, inte generellt |
| Formen på `BESLUT.md`, `metod/README.md`, `metod/mallar.md`, `metod/red-team-prompt.md` | Domänkörningsmetoden i sex steg, juridiska checklistor, mönsterregistret, handpåläggningskostnad |
| Formen på en undersökning: README med fråga, argumentkedja, "vad skulle få oss att ändra slutsatsen", numrerade prov med `underlag/` | Allt ämnesinnehåll |
| Arbetsreglerna i README som `AGENTS.md` | Jävsreglerna om Digitalist; ersätts med en allmän regel om egenintresse |
| `kunskap/` med `registry.json`, `snapshots/`, `INDEX.md` | De 33 källorna och 42 påståendena |

## Struktur

```
AGENTS.md                         regler agenten läser vid start; pekar in i metod/
CLAUDE.md                         en rad: läs AGENTS.md
README.md                         vad repot är, Första timmen, struktur, forskningsloopen
BESLUT.md                         beslutslogg
metod/README.md                   grundregler och avslutskontroll
metod/mallar.md                   mallar för undersökning, prov och kunskapspost
metod/red-team.md                 angreppslinjer mot en egen syntes
undersokningar/README.md          index över undersökningar
undersokningar/001-exempel/       ifylld exempelundersökning med prov-01
kunskap/README.md                 hur en källa och ett påstående läggs till
kunskap/registry.json             giltigt register med exempelundersökningens poster
kunskap/snapshots/                hashade källutdrag
kunskap/INDEX.md                  genererat av `harness index`
harness/__init__.py
harness/__main__.py               CLI
harness/common.py                 ContractError, read_json, digest, atomic_json, confined
harness/registry.py               validate_registry, build_index, context, impact
harness/prov.py                   skapa, utvardera
tests/test_registry.py
tests/test_prov.py
.agents/skills/ny-undersokning/SKILL.md
.agents/skills/avslut/SKILL.md
.gitignore
docs/superpowers/specs/           denna spec
```

## Komponenter

### Kunskapsregistret (`harness/registry.py`)

Kopieras från förlagan. Ändringar:

- `CLAIM_TYPES` blir `{'observation', 'hypothesis', 'interpretation', 'derivation', 'model_result', 'dated_analysis'}`. `dated_legal_analysis` och `requirement_candidate` och `design_hypothesis` utgår; `interpretation` och `derivation` ersätter `conditional_derivation`.
- Källtyper (`kind`) dokumenteras i `kunskap/README.md`: `literature`, `transcript`, `empirical_report`, `dataset`, `model_trial`, `analysis`, `note`. Regeln att en `observation` bara får `supports` från `transcript` eller `empirical_report`, och `model_result` bara från `model_trial`, behålls.
- `legal`-blocket och dess validering behålls som valfritt. Det kostar inget och Amanda kan behöva det.
- Felkoder, `STATUSES`, `REVIEW_STATUSES`, `SECTIONS` oförändrade.

Kommandon: `validate`, `index`, `context <ids> [--audience public] [--sources-only]`, `impact [ids] [--as-of]`. Semantik som i förlagan.

### Provmotorn (`harness/prov.py`)

Ny, generell. Ett prov är ett fryst protokoll plus ett resultat plus en separat utvärdering.

**Protokoll** (`protokoll.json`), valideras vid `skapa`:

```json
{
  "schema_version": 1,
  "id": "U001-01",
  "undersokning": "U001",
  "fraga": "…",
  "hypotes": "…",
  "rival": "…",
  "matt": [{"id": "m1", "beskrivning": "…", "enhet": "…"}],
  "tolkningsregel": {
    "matt": "m1",
    "stodjer_hypotes_om": {"op": ">=", "varde": 0.7},
    "stodjer_rival_om": {"op": "<=", "varde": 0.4}
  },
  "paverkar": ["K001"],
  "underlag": ["underlag/data.csv"],
  "begransningar": "…"
}
```

`op` är en av `>=`, `>`, `<=`, `<`, `==`. Värden mellan trösklarna ger `oavgjort`. `paverkar` är ID:n i registret; `skapa` kontrollerar att de finns om registret finns. `underlag` är relativa sökvägar från protokollets katalog och måste ligga innanför den (`confined`).

**`skapa <protokoll.json> --out <katalog>`**: kopierar protokoll och underlag till `<katalog>/`, skriver `manifest.json` med `schema_version`, `id`, `skapad`, `hashes` (relativ fil till SHA256) och `status: "fryst"`. Fel om katalogen finns.

**`utvardera <katalog> [--write]`**: läser `manifest.json`, kontrollerar alla hashar (ändrad fil är kontraktsfel, kod 2), läser `resultat.json` som forskaren eller ett skript lagt i katalogen efter frysning: `{"matt": {"m1": 0.82}, "kommentar": "…"}`. Tillämpar tolkningsregeln, skriver `evaluation.json` med `id`, `utvarderad`, `matt`, `utfall` (`stodjer_hypotes`, `stodjer_rival`, `oavgjort`), `regel` (kopia), `begransningar` (från protokollet), `manifest_sha256`. Saknat mått är kontraktsfel. Ett negativt eller oavgjort utfall är inte ett körfel (kod 0).

**`demo`**: kör `skapa` på `undersokningar/001-exempel/prov-01/protokoll.json` till en tillfällig katalog under `korningar/lokalt/`, kopierar in exempelprovets `resultat.json`, kör `utvardera --write`, skriver utfallet till stdout. Gitignorerad utdata.

Felkoder som förlagan: 0 lyckat, 2 ogiltigt underlag eller kontrakt, 3 ofullständigt.

### Metod (`metod/`)

`README.md`: grundregler, ämnesneutrala. Kärnan från förlagan: tomt blad från frågan, rival formulerad innan belägg samlas, mått och tolkningsregel låsta före data, beläggsvalör redovisad (publicerat före egna anteckningar före egen erfarenhet), red team innan syntes, egenintresse anges (finansiär, handledare, egen tidigare position), inga ändrade regler utan post i `BESLUT.md`, avslutskontroll. Ungefär tio regler. Ingen regel om Digitalist eller kommuner.

`mallar.md`: mall för undersökningens README (frågan och varför, argumentkedjan, vad som skulle ändra slutsatsen, prov-tabell, syntes), mall för prov-README (vad prövas, protokoll, resultat, bedömning, begränsningar), mall för kunskapspost i registret.

`red-team.md`: fem angreppslinjer: bekväm slutsats, urval av belägg, mått som inte mäter det påstådda, rival som är en halmgubbe, generalisering bortom materialet.

### AGENTS.md och skills

`AGENTS.md`: ungefär tjugo rader. Läs `metod/README.md` innan arbete. Skriv på svenska. Driv arbetet utan tillståndsfrågor per steg men stanna vid riktningsändringar. Varje avslut kör avslutskontrollen. Ändra aldrig en fryst körkatalog. Gör inga modellanrop med kostnad utan uttrycklig instruktion. Lägg aldrig personuppgifter från intervjuer i registret utan att forskaren beslutat om avidentifiering.

`.agents/skills/ny-undersokning/SKILL.md`: frontmatter `name`, `description`. Skapar `undersokningar/NNN-<slug>/README.md` från mallen, frågar forskaren om fråga, hypotes, rival och första prov, skapar `prov-01/protokoll.json`, kör `python3 -m harness validate`.

`.agents/skills/avslut/SKILL.md`: kör avslutskontrollen: skriv beslut i `BESLUT.md`, uppdatera undersökningens README, `python3 -m harness validate`, `python3 -m harness index > kunskap/INDEX.md`, `python3 -m unittest discover -s tests`, kontrollera att README speglar besluten.

### Exempelundersökning (`undersokningar/001-exempel/`)

Ett litet, ämnesneutralt men verkligt prov som visar hela varvet: fråga, hypotes, rival, ett mått, ett protokoll, ett underlag (en liten CSV), ett `berakna.py` som räknar måttet och skriver `resultat.json`, och en README som bedömer utfallet och skriver in en kunskapspost. Registret innehåller därför en källa (snapshot av underlaget, `kind: dataset`) och ett påstående (`K001`, typ `derivation`, status `provisional`, `review_status: unreviewed`, med `reconsider_if` som pekar på att data är syntetisk).

Ämne för exemplet: "Ger en litteratursökning med två söksträngar fler relevanta träffar än med en?" Underlaget är en påhittad CSV med 40 träffar, kolumner `sokstrang`, `relevant`. Måttet är andel relevanta per söksträng. Data märks som syntetisk i protokollet och i README, och slutsatsen skrivs ut som ett exempel på formen, inte som ett fynd.

### README.md

Avsnitt: Vad repot är (tre meningar). Första timmen (skapa från mall, klona, tre kommandon, starta Codex, `$ny-undersokning`). Forskningsloopen (fråga, rival, prov låst före data, resultat, utvärdering, kunskapspost, beslut). Struktur (tabell). Kommandon. Var förlagan finns.

## Testning

- `tests/test_registry.py` från förlagan, med de nya `CLAIM_TYPES`.
- `tests/test_prov.py`: `skapa` fryser och hashar; ändrad fil efter frysning ger kod 2; `utvardera` ger `stodjer_hypotes`, `stodjer_rival` och `oavgjort` för tre resultat; saknat mått ger kontraktsfel; `paverkar` mot okänt ID ger kontraktsfel; `demo` går igenom.
- I ren klon ska `python3 -m unittest discover -s tests`, `python3 -m harness validate` och `python3 -m harness demo` gå igenom. Enbart standardbibliotek. Python 3.10 eller senare.

## Leverans

1. Repot byggs lokalt i `~/Developer/forskningsrepo`, committas i steg.
2. `gh repo create fabian-von-tiedemann/forskningsrepo --public --source . --push`, därefter markeras som template via `gh api`.
3. Ett kort meddelande till Amanda skrivs i `docs/brev-till-amanda.md`: vad repot är, hur hon skapar sitt eget från mallen, de tre kommandona, och att `AGENTS.md` är det första Codex läser.

## Avgränsning

Ingen modelladapter, ingen sandbox, ingen kömodell. Vill Amanda senare köra språkmodeller i prov är `prov.py` gränssnittet: ett skript som skriver `resultat.json` in i en fryst katalog.
