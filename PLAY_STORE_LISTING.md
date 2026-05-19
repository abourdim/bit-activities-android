# Play Store listing — Bit Activities (أنشطة البِت)

Draft copy for Google Play Console "Main store listing" page. Play Console accepts separate translations per language — upload all three.

---

## Metadata (common to all languages)

- **Package name**: `org.workshopdiy.bitactivities`
- **Category**: `Books & Reference` (primary), `Education` (secondary if allowed)
- **Tags**: Islamic studies, Arabic, trilingual, education, al-Ghazali
- **Contact email**: `abdelhak.bourdim@gmail.com`
- **Website**: `https://workshop-diy.org`
- **Privacy policy URL**: REQUIRED — host a simple page (see template at end of this file).
- **Content rating**: Everyone (no violence, no gambling, no mature content).
- **Ads**: No.
- **In-app purchases**: No.
- **Data safety**: No data collected, no data shared.

---

## Arabic (ar) — primary

### App name (≤30 chars)
```
أنشطة البِت
```

### Short description (≤80 chars)
```
٤٨ نشاطًا تطبيقيًا لميكروبيت — مصابيح وحساسات وبلوتوث وروبوتات.
```

### Full description (≤4000 chars)
```
🎯 أنشطة البِت — ٤٨ نشاطًا تفاعليًا

ثمانية وأربعون نشاطًا موجَّهًا لميكروبيت BBC.

✨ المزايا
• من أول وميض لمصباح حتى الروبوتات
• اتصال BLE بنقرة واحدة
• ذكاء اصطناعي على الجهاز
• واجهة ثلاثية اللغات (AR/EN/FR)
• ٩ سمات بصرية

من workshop-diy.org
```

---

## English (en)

### App name
```
Bit Activities — Bit Activities
```

### Short description
```
48 hands-on micro:bit activities — LEDs, sensors, BLE, robotics, AI.
```

### Full description
```
🎯 Bit Activities — 48 Hands-On micro:bit Lessons

Forty-eight guided activities for the BBC micro:bit.

✨ Features
• From first LED blink to BLE-driven robots
• On-device AI experiments
• One-click BLE pairing
• Trilingual EN/FR/AR interface
• 9 theme palettes, zero dependencies

From workshop-diy.org
```

---

## French (fr)

### App name
```
Bit Activities — Bit Activities
```

### Short description
```
48 activités micro:bit — LEDs, capteurs, BLE, robotique et IA.
```

### Full description
```
🎯 Bit Activities — 48 leçons micro:bit

Quarante-huit activités guidées pour le BBC micro:bit.

✨ Fonctionnalités
• Du premier clignotement aux robots BLE
• IA embarquée
• Appairage BLE en un clic
• Interface trilingue EN/FR/AR
• 9 thèmes graphiques

De workshop-diy.org
```

---

## Graphics needed (minimum)

| Asset | Size | Source |
|---|---|---|
| App icon | 512×512 PNG | `store-assets/play-store-icon-512.png` (regenerate per book) |
| Feature graphic | 1024×500 PNG | `store-assets/feature-graphic.png` (render from `feature-graphic.html`) |
| Phone screenshots | min 2, 320–3840px, 16:9 portrait | Capture from emulator / real device |
| 7" tablet screenshots (optional) | min 2, 1024×600+ | Run emulator with tablet profile |

Screenshots to capture (book-specific — adjust list to actual app screens):
1. Home / cover / introduction
2. Main content navigation
3. Reading or interaction mode
4. Quiz or self-assessment (if applicable)
5. Theme switch (optional — shows the 3 variants)

---

## Privacy policy template

Copy to a public page (GitHub Pages works). Change email + date.

```
Privacy Policy — Bit Activities
Last updated: 2026-05-19

The Bit Activities app does not collect, store, transmit, or share any personal
data. All content is bundled with the app and runs entirely on your device.
The app does not use analytics, advertising networks, crash reporters, or
third-party SDKs.

The app requires no special permissions beyond internet access, which is
used only to load the occasional external link (e.g. workshop-diy.org) if
you tap it — never silently in the background.

If you have questions, contact: abdelhak.bourdim@gmail.com
```
