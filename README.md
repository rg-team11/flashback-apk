# Flashback (REminiscence) za Android TV box

Ovaj paket pravi APK od REminiscence 0.5.6 engine-a (izvorni kod: https://github.com/cyxx/REminiscence)
u GitHub oblaku. Ne treba ti ništa instalirati na računaru.

NAPOMENA: ovaj paket nisam mogao da isprobam (nema Android alata na mom serveru). Ako gradnja
padne, pošalji mi tekst greške iz loga i ispraviću.

## 1. Korak: GitHub nalog i repozitorijum
1. Otvori https://github.com i napravi besplatan nalog (Sign up).
2. Gore desno klikni **+** → **New repository**. Ime: `flashback-apk`. Ostavi **Public**
   (javni repozitorijumi imaju neograničeno besplatno građenje). Klikni **Create repository**.
3. Na stranici novog repozitorijuma klikni **uploading an existing file**.
4. Raspakuj ovaj zip na računaru i **prevuci SADRŽAJ foldera** (folder `.github`, folder `tools`
   i fajl `README.md`) u prozor pretraživača. Sačekaj da se sve ubaci i klikni **Commit changes**.
   - Ako ne vidiš folder `.github` (na Windows-u je "skriven"): uključi u Exploreru
     View → Show → Hidden items, pa ponovo prevuci.
   - Rezervno rešenje: **Add file → Create new file**, u polje imena upiši
     `.github/workflows/build.yml` i nalepi sadržaj fajla `build.yml`; zatim isto za `tools/prepare.py`.

## 2. Korak: gradnja APK-a
1. Gore u repozitorijumu klikni karticu **Actions**. Ako traži, potvrdi "I understand my workflows, enable them".
2. Levo izaberi **Build Flashback APK** → desno **Run workflow** → **Run workflow**.
   (Pokreće se i sam posle svakog uploada.)
3. Sačekaj 10–20 minuta. Zelena kvačica = uspelo. Crveno X = nije; klikni na to pokretanje,
   zatim na korak koji je crven, kopiraj poslednjih ~40 linija loga i pošalji mi.
4. Kad je zeleno, otvori to pokretanje i dole u odeljku **Artifacts** klikni **Flashback-APK**.
   Preuzima se zip; u njemu je `app-debug.apk`.

## 3. Korak: instalacija na TV box
- Prebaci `app-debug.apk` na box (USB fleš, ili aplikacija "Send files to TV", ili Downloader).
- Dozvoli instalaciju iz nepoznatih izvora za aplikaciju kojom otvaraš APK, pa instaliraj.
- Aplikacija se zove **Flashback**.

## 4. Korak: fajlovi igre (Macintosh)
Napravi folder na unutrašnjoj memoriji boxa:

    /sdcard/REminiscence/DATA

i u njega stavi sve fajlove igre (Macintosh verzija: `FLASHBACK.BIN` ili `FLASHBACK.RSRC`
i ostali fajlovi iz foldera sa podacima, bez menjanja imena).
Pri prvom pokretanju Android pita za dozvolu pristupa memoriji: dozvoli, pa ponovo pokreni igru.
Ako fajlovi nisu nađeni, igra prikaže poruku sa spiskom foldera koje je proveravala.
Sačuvane pozicije (Ctrl+S) idu u privatni folder aplikacije.

## Komande
- Strelice na daljinskom: kretanje; centralno dugme (OK): Enter (koristi predmet iz inventara)
- Back dugme: Escape (meni sa opcijama)
- Shift (razgovor/koristi/trči/pucaj) nedostaje na većini daljinskih: ovde je dodeljen tasterima
  **Menu**, **Page Up**; **Page Down** = inventar (kao Tab)
- Najudobnije: gejmpad (USB/Bluetooth) ili USB tastatura; gejmpad engine podržava po defaultu.
