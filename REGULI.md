# REGULI – clipuri Novum Sol (comune pentru Claude și GPT)

Aceste reguli sunt obligatorii pentru orice clip produs în acest proiect.
Dacă o regulă nu poate fi respectată, clipul NU se face – se raportează motivul.

## 1. Firma
- **Novum Sol** – novumsol.ro, Arad. Produse de protecția plantelor, tratamente sămânță, îngrășăminte.
- Vânzare en-detail și direct către fermieri.
- Îndemn final obligatoriu: **novumsol.ro** și **0754 460 345**.

## 2. Format
- Vertical 1080×1920, 15–30 s, MP4 (H.264 + AAC), sub 50 MB.
- Text mare, lizibil pe telefon, fără sunet (subtitrat / text pe ecran).
- Fiecare clip pentru Facebook, Instagram (Reels) și TikTok.

## 3. Identitate
- **Logo-ul oficial Novum Sol** (`data/logo.*`) apare în fiecare clip – nu logo text desenat.
- **Doar poze oficiale** de pe novumsol.ro (`data/images/`). Producătorii au dat acordul pentru marketing.
- Nu se desenează ambalaje inventate și nu se modifică etichetele produselor.
- **Fără oameni realiști generați cu AI.**

## 4. Informații
- Doar informații oficiale: pagina produsului de pe novumsol.ro sau eticheta producătorului.
- **Fără doze, culturi, efecte sau promisiuni inventate.** Dacă nu e în sursă, nu apare.
- **Prețurile se iau din `data/products.json` în ziua clipului** (sincronizat zilnic). Nu se folosesc prețuri vechi.
- Promoția se afișează doar dacă produsul e `on_sale` în ziua clipului.
- **STOCUL REAL se verifică în aplicația Control Novum Sol (Nexus)**, nu pe site: produsul intră în clip doar dacă are stoc liber > 0 în MICRO sau DEP. DIVA SOL, în ziua clipului. Site-ul poate arăta „în stoc” la produse care nu mai există fizic.
- Cantitățile din stoc NU se publică și NU se urcă în acest proiect (e public). În `surse.md` se notează doar „în stoc, verificat <data>”.

## 5. Pesticide (Reg. UE 1107/2009, art. 66)
- Pe ORICE clip care conține un produs de protecția plantelor (fungicid, insecticid, erbicid, tratament sămânță etc.) apare, lizibil, pe tot parcursul scenelor cu produsul și în final:

  > **Utilizați produsele fitosanitare în condiții de siguranță. Citiți întotdeauna eticheta și informațiile despre produs înainte de utilizare.**

  (Textul exact e în `config/legal.json` – se ia de acolo, nu se rescrie.)
- **Interzis** în text, voce sau descriere: „netoxic”, „inofensiv”, „risc scăzut”, „sigur pentru sănătate”, „natural deci sigur” sau orice formulare echivalentă.
- Dacă cineva manevrează produsul (ilustrație/foto): **echipament de protecție** (mănuși, ochelari, combinezon) – altfel nu se arată.

## 6. Idei
- **Idee nouă la fiecare clip** – verificați propriul jurnal ȘI jurnalul celuilalt (`claude/JURNAL.md`, `gpt/JURNAL.md`) ca să nu repetați unghiul, produsul principal și hook-ul din ultimele 4 săptămâni.
- Scopul: atragerea de clienți (comenzi, mesaje, apeluri), nu doar vizualizări.
- Ideea se alege după: sezonul agricol, avertizările fitosanitare (zona de vest/Arad), promoțiile de pe site, rezultatele postărilor anterioare.

## 7. Aprobare și publicare
- **Nimic nu se postează fără acordul lui Bogdan.**
- Fluxul: clip + text postare → trimis spre aprobare → modificări → doar după „OK” se programează în Buffer (Facebook, Instagram, TikTok), în jurul orei **19:30**.

## 8. Experimentul
- 4 clipuri / săptămână: 2 Claude (`claude/`), 2 GPT (`gpt/`), făcute independent.
- Comparație după 1–3 luni: vizualizări, % vizionare, distribuiri + salvări, mesaje + apeluri.
- Fiecare agent lucrează doar în folderul propriu. `data/`, `config/`, `REGULI.md` sunt comune – nu se modifică fără acord.

## 9. Structura proiectului
```
data/products.json      produse, prețuri, promoții (zilnic, automat)
data/images/<id>.*      poza principală a fiecărui produs (max 1000 px)
data/logo.*             logo oficial
data/prices/AAAA-LL-ZZ.csv  istoric prețuri
config/legal.json       fraza obligatorie art. 66
claude/  gpt/           clipuri, cod, jurnal – separat pentru fiecare
```
Fiecare clip: `<agent>/clipuri/AAAA-LL-ZZ-<slug>/` cu `clip.mp4`, `postare.txt`, `surse.md` (de unde vin informațiile și prețurile).
