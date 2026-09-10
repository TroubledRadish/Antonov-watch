# antonov-watch

Watches one aircraft (ICAO hex `50801b`) on [adsb.fi](https://adsb.fi) and
sends a push notification to your iPhone the moment its transponder shows up
in ADS-B coverage — i.e. when it "turns on".

- **No Mac needed.** The "app" on your phone is [ntfy](https://ntfy.sh), a
  free open-source notification app on the App Store — no account, no cost.
- **No server to pay for.** A GitHub Actions cron job does the polling on
  GitHub's free runners.
- **What "turns on" means here:** the plane is powered up *and* within range
  of a volunteer ADS-B receiver. Over Russia, oceans, or other coverage gaps
  it can be flying and still not appear — that is the same limit the
  globe.adsb.fi map itself has.

---

## 1. Phone side (2 minutes)

1. Install **ntfy** from the App Store.
2. Open it → tap **+** → **Subscribe to topic**.
3. Enter a long, random topic name so nobody else guesses it, e.g.
   `antonov-50801b-9f3a1c7e42`. Leave the server as `ntfy.sh`. Tap
   **Subscribe**.
4. Keep that exact topic string — you'll paste it into GitHub next.
5. (Optional test) On any computer:
   `curl -d "hello" https://ntfy.sh/antonov-50801b-9f3a1c7e42` — the phone
   should buzz.

## 2. GitHub side (5 minutes)

1. Create a free GitHub account if you don't have one.
2. Make a **new repository**. Make it **Public** — public repos get
   unlimited free Actions minutes (a private repo would blow past the free
   2000 min/month at this poll rate). Your ntfy topic stays private anyway
   because it goes in an encrypted secret, not the code.
3. Upload these four things to the repo (drag-and-drop in the web UI works):
   - `watch.py`
   - `state.json`
   - `.github/workflows/watch.yml`  (keep that folder path)
   - `README.md` (optional)
4. In the repo: **Settings → Secrets and variables → Actions → New
   repository secret**.
   - Name: `NTFY_TOPIC`
   - Value: your topic string from step 1 (just the topic, not a URL)
5. Open the **Actions** tab, enable workflows if prompted, pick
   **antonov-watch**, and click **Run workflow** once to confirm it works.
   Check the run log — it should say `50801b still off` (or notify you if
   the plane happens to be up right now).

That's it. From then on it checks every ~5 minutes on its own and pushes a
notification on the first sighting after a quiet spell.

---

## How it behaves

- Notifies on the **off → on** transition only, not repeatedly while the
  plane stays visible.
- If the signal drops out briefly (coverage gap), it waits for 3 consecutive
  empty checks (~15 min) before re-arming, so a flaky signal won't spam you.
- `state.json` is committed back to the repo by the action to remember
  whether the plane was last seen up or down. The `[skip ci]` commits are
  normal.
- The notification includes callsign, altitude, speed, position, and tapping
  it opens `globe.adsb.fi` focused on the aircraft.

## Notes / limits

- GitHub's scheduled runs can be delayed 5–15 min under load, and very
  rarely skipped. Fine for a multi-hour cargo flight; not a countdown timer.
- GitHub disables cron workflows after **60 days** with no *human* commits to
  the repo. For a one-off watch that's plenty; if you need longer, push any
  small commit to reset the clock.
- Anyone who learns your ntfy topic can send you fake alerts or read yours.
  The only defense is keeping the topic name random and unshared. Nothing
  sensitive is involved, so this is low-stakes.
- Change the aircraft by editing `ADSB_HEX` in `.github/workflows/watch.yml`.

## Running it on your PC instead (alternative)

If you'd rather not use GitHub and your PC is on when it matters: edit
`run-local.ps1` to set your topic, then run it in PowerShell. It polls every
5 minutes until you close it. Needs Python 3 installed.

---

Data © [adsb.fi](https://adsb.fi), used for personal, non-commercial purposes.
