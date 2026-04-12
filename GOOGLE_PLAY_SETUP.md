# Terra Balance – Google Play Store Setup

This guide takes you from this repo to a live listing on Google Play.
The app is packaged as a **Trusted Web Activity (TWA)** — a native Android shell
that displays the GitHub Pages website with no browser chrome, indistinguishable
from a fully native app.

---

## Architecture

```
Google Play  →  Android APK/AAB (android/)
                    ↓  opens
             GitHub Pages  (https://honnikorn.github.io/terra-balance/)
                    ↓  verifies via
             Digital Asset Links  (.well-known/assetlinks.json)
```

---

## Prerequisites

| Tool | Download |
|------|----------|
| Java 17+ | https://adoptium.net |
| Android Studio (or SDK CLI) | https://developer.android.com/studio |
| Google Play Console account | https://play.google.com/console |

---

## Step 1 – Generate the signing keystore

> **Do this once. Keep the keystore file safe — you can never change it.**

```bash
cd android
bash setup-keystore.sh
```

This will:
- Generate `android/keystore/release.jks`
- Write `android/keystore.properties` (git-ignored)
- Update `.well-known/assetlinks.json` with your SHA256 fingerprint

---

## Step 2 – Deploy the Digital Asset Links file

Android verifies the TWA by fetching `assetlinks.json` from the **root domain**:

```
https://honnikorn.github.io/.well-known/assetlinks.json
```

Because the game lives in a subdirectory (`/terra-balance/`), you need to host
this file at the root of `honnikorn.github.io`. Do this by creating (or updating)
the **`honnikorn/honnikorn.github.io`** repository on GitHub:

```bash
# In a separate local clone of honnikorn/honnikorn.github.io:
mkdir -p .well-known
cp /path/to/terra-balance/.well-known/assetlinks.json .well-known/assetlinks.json
git add .well-known/assetlinks.json
git commit -m "chore: add Digital Asset Links for Terra Balance TWA"
git push
```

**Verify it is reachable:**
```
https://digitalassetlinks.googleapis.com/v1/statements:list
  ?source.web.site=https://honnikorn.github.io
  &relation=delegate_permission/common.handle_all_urls
```

> **Alternative:** Use a custom domain (e.g. `terrabalance.no`) where you fully
> control the root, then update `android:host` in `AndroidManifest.xml` and
> `launch_url` in `strings.xml` to match.

---

## Step 3 – Set up the Gradle wrapper

The `gradle-wrapper.jar` binary is not committed to git. Generate it with:

```bash
cd android
gradle wrapper --gradle-version 8.5
```

*(Requires Gradle to be installed. On macOS/Linux: `brew install gradle` or `sdk install gradle`)*

---

## Step 4 – Build the App Bundle (AAB)

```bash
cd android
./gradlew bundleRelease
```

Output: `android/app/build/outputs/bundle/release/app-release.aab`

---

## Step 5 – Create a Google Play Console listing

1. Go to https://play.google.com/console → **Create app**
2. Fill in:
   - **App name:** Terra Balance
   - **Default language:** English (United States)
   - **App or game:** Game
   - **Free or paid:** Free
3. Complete the **store listing** (see assets below)
4. Upload the **AAB** under Production → Releases → Create release
5. Answer the content rating questionnaire
6. Set the target audience (13+)
7. Declare no ads
8. Submit for review (typically 1–3 days)

---

## Store Listing Assets

### Short description (80 chars max)
```
An educational climate strategy game. Protect the planet. Build a civilisation.
```

### Full description (4000 chars max)
```
Can you build a thriving civilisation without destroying the planet?

Terra Balance is an educational climate strategy game where every decision matters.
Choose a region, pick a difficulty, and guide your world through 20–50 years of
climate challenges — balancing energy, food, nature, water, economy, and biodiversity.

KEY FEATURES
• 37 buildings – from coal plants to fusion reactors and kelp farms
• 20 policies based on real climate laws: carbon tax, plastic bans, fishing quotas
• 20 technologies across a 5-tier research tree (unlock Fusion Energy to win!)
• 51 crisis events with real-world climate science
• 6 regions with unique starting conditions: Europe, Africa, Asia, Americas, Australia
• 16 achievements to unlock
• 20-entry climate encyclopedia
• Flagship species tracker across 6 continents
• Interactive 3D globe
• 2-player hot-seat mode
• Offline play after first load
• Available in English and Portuguese

EDUCATIONAL FOCUS
Every building, policy, and crisis event is grounded in real climate science.
Quiz questions appear as you build, unlocking a learning report at game end.

DIFFICULTY LEVELS
• Guardian – 50 years, gentle start
• Civiliser – 35 years, balanced (recommended)
• Crisis Manager – 25 years, pressure-cooker
• Last Chance – 18 years, nearly impossible

Can you achieve Perfect Harmony before the clock runs out?
```

### Category
Education / Strategy Games

### Content rating
**Everyone 10+** — mild fantasy themes, educational content

### Required graphics

| Asset | Size | Notes |
|-------|------|-------|
| App icon | 512×512 px PNG | Already at `icons/icon-512.png` |
| Feature graphic | 1024×500 px JPG/PNG | Create screenshot of globe view |
| Phone screenshots | 2–8 screenshots | Min 320px, max 3840px |
| Tablet screenshots | Optional | 7-inch and 10-inch |

**Tip for screenshots:** Open https://honnikorn.github.io/terra-balance/ in Chrome DevTools
at a 390×844 viewport, take screenshots of the globe view, build menu, and event screen.

---

## Updating the App

When the game content changes (new features in `index.html`):

1. Push the updated `index.html` — GitHub Pages auto-deploys within ~60 seconds.
2. Increment `versionCode` and `versionName` in `android/app/build.gradle`.
3. Run `./gradlew bundleRelease` again.
4. Upload the new AAB to Play Console → Production → Create new release.

> **No TWA code changes needed** — the Android app always loads the latest
> version of the website automatically.

---

## Google Play App Signing

Google Play can manage your signing key for you (recommended):

1. In Play Console: **Setup → App signing → Use Google Play app signing**
2. Upload your **upload certificate** (derived from your keystore) as the upload key
3. Google re-signs the app before distribution — your upload key is the only
   thing that needs to remain secret

To get your upload certificate SHA1 for Play Console:
```bash
keytool -list -v -keystore android/keystore/release.jks -alias terrabalance
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Address bar still visible | `assetlinks.json` not yet verified. Wait 24h after deploy. |
| App crashes on launch | Check `logcat` — usually a missing TWA dependency |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Uninstall debug build before installing release |
| Build fails on missing `gradle-wrapper.jar` | Run `gradle wrapper --gradle-version 8.5` |

---

## File Structure

```
terra-balance/
├── index.html                  ← The entire game (web app)
├── manifest.json               ← PWA manifest (required for TWA)
├── sw.js                       ← Service worker (offline support)
├── icons/                      ← App icons for all sizes
│   ├── icon-*.png
│   ├── icon-512-maskable.png
│   └── generate-icons.py       ← Regenerate icons if needed
├── .well-known/
│   └── assetlinks.json         ← Digital Asset Links (TWA verification)
└── android/                    ← Android TWA project
    ├── app/
    │   ├── build.gradle
    │   └── src/main/
    │       ├── AndroidManifest.xml
    │       └── res/
    │           ├── drawable/   ← Vector icon + splash
    │           ├── mipmap-*/   ← PNG launcher icons
    │           └── values/     ← Strings, colours, styles
    ├── build.gradle
    ├── settings.gradle
    ├── gradlew
    ├── setup-keystore.sh       ← Run once to generate signing key
    └── keystore/               ← (git-ignored) signing credentials
```
