# OneWealth on your iPhone

The **OneWealth** app is the full website in an iPhone app. It has every role and every page, its own icon, and no Safari bar.
It loads https://oneweath.ngrok.app, so whatever is deployed there shows up in the app. You never rebuild the app for that.

It is free and needs no developer account. You need:
- your iPhone and its USB cable;
- a computer (Windows or Mac);
- a free Apple ID (the one already on your phone works).

It takes about 10 minutes the first time.

## 1. Download two things

1. **The app:** `OneWealth.ipa` from https://oneweath.ngrok.app/download/ (open it on the computer).
2. **Sideloadly:** from https://sideloadly.io. It signs the app with your Apple ID and puts it on the phone.
   - **Windows only:** also install **iTunes** and **iCloud** from Apple's website, the "download from apple.com" versions,
     **not** the Microsoft Store ones. Sideloadly links to the right ones.
   - **Mac:** nothing else is needed.

## 2. Install

1. Plug the iPhone into the computer and unlock it. If the phone asks **"Trust This Computer?"**, tap **Trust** and enter your passcode.
2. Open Sideloadly. Your iPhone appears at the top.
3. Drag `OneWealth.ipa` onto Sideloadly.
4. Type your Apple ID email and click **Start**. Enter your Apple ID password, and the 6-digit code if Apple sends one.
5. Wait until it says **Done**. The OneWealth icon is now on the phone.

## 3. Allow it on the iPhone (first time only)

1. Go to **Settings → Privacy & Security → Developer Mode**, turn it **On**, and restart when asked.
   After the restart, tap **Turn On** again.
2. Go to **Settings → General → VPN & Device Management**. Tap your Apple ID under "Developer App", then **Trust**.
3. Open **OneWealth** and sign in. The demo buttons work as on the website.

**Example:** open the app, tap the **RM** demo account, and the RM desk opens full screen.
Pull down to reload, and swipe from the left edge to go back.

## Every 7 days

A free Apple ID signs apps for 7 days. After that the app will not open. To renew it, plug in the phone and repeat
**step 2** with the same file. Your sign-in and settings stay.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| Sideloadly does not show the iPhone | Unlock the phone and tap **Trust**. Try another cable. On Windows, reinstall iTunes from apple.com, not the Store. |
| "Untrusted Developer" when opening the app | Do step 3.2. The phone needs internet for this. |
| No **Developer Mode** in Settings | It appears only after the first install from step 2. Install, then look again. |
| "Maximum number of apps" | A free Apple ID allows 3 such apps at a time. Delete an old one from the phone. |
| "Không mở được OneWealth" in the app | The demo server or the ngrok tunnel is off. Start it again, then tap **Thử lại**. |
| The app stopped opening after a week | The 7 days are up. Repeat step 2. |

Your Apple ID only goes to Apple, to sign the app. If you'd rather not use your main one, create a spare Apple ID for
this.

---

### For developers

- The code is in `ios-shell/`, a SwiftUI app around a `WKWebView`. XcodeGen builds the project from `project.yml`.
- `.github/workflows/ios-shell.yml` builds it on a GitHub macOS runner with each push to `app/ios-shell`.
  Each run:
  - runs the tests;
  - takes screenshots of every role, light and dark;
  - uploads the unsigned `.ipa` as a run artifact.
- The server address is `Server.url` in `OneWealth/Links.swift`.
