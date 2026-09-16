# Till Amanda

Hej! Här är repot jag lovade. Det är en mall, inte ett färdigt projekt: en form för hur frågor, studier, källor och beslut hänger ihop, byggd så att en kodagent kan bära arbetet mellan punkterna. Det lutar sig mot sådant du redan känner igen: förregistrering (OSF, Registered Reports), spårbara källor, CRediT och jävsdeklaration.

**Så här kommer du igång, tar ungefär en timme:**

1. Gå till https://github.com/fabian-von-tiedemann/research-harness-template och klicka **Use this template**. Döp ditt repo och klona det.
2. Kör i repots rot:
   ```sh
   python3 -m harness validate
   python3 -m harness demo
   python3 -m unittest discover -s tests
   ```
   Allt ska gå igenom. `demo` kör ett exempel från fryst protokoll till utvärdering.
3. Läs `method/README.md`. Tio regler och en avslutskontroll. Femton minuter.
4. Starta Codex i repot. Det läser `AGENTS.md` först. Skriv `$new-investigation` och svara på frågorna: din fråga, din hypotes, den konkurrerande hypotesen, ditt första mått, dina intressen. Sedan lägger du in data, fryser protokollet med `python3 -m harness create` och committar `frozen/` innan du analyserar något. Den committen är din förregistrering.
5. När din första undersökning finns: ta bort `investigations/001-example/` och dess poster i `knowledge/registry.json`, kör `validate` igen.

**Två saker jag vill be dig om:**

- Repot är på engelska, men du skriver dina egna texter på vilket språk du vill. Codex följer ditt språk.
- När något i metoden, mallarna eller verktyget är i vägen, skicka det tillbaka som ett issue. `close-out`-skillen frågar dig om det varje gång en undersökning avslutas och skriver utkastet. Det är så mallen blir bättre för nästa person.

Fråga när du kör fast. Hälsningar, Fabian
