# Schlage Integration for Unfolded Circle Remote 2/3

Control your **Schlage Wi-Fi smart locks** (Encode, Encode Plus, Sense) directly from your Unfolded Circle Remote 2 or Remote 3. Lock and unlock, set the auto-lock delay, toggle the beeper and lock-and-leave, and monitor battery level and lock status - all from your Schlage Home account.

![Schlage](https://img.shields.io/badge/Schlage-Smart%20Lock-C8102E)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-schlage?style=flat-square)](https://github.com/mase1981/uc-intg-schlage/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-schlage?style=flat-square)](https://github.com/mase1981/uc-intg-schlage/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-schlage/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)

## Supported Devices

Schlage Wi-Fi smart locks that work with the **Schlage Home** app, including **Encode**, **Encode Plus**, and **Sense** Wi-Fi deadbolts.

## Features

- **🔒 Lock control** - lock and unlock each lock as a switch (on = locked).
- **⏱️ Auto-lock selector** - set the auto-lock delay (Off, 15 s, 30 s, 1 / 2 / 4 / 5 min).
- **🔔 Beeper switch** - turn the keypad beeper on or off.
- **🚪 Lock & Leave switch** - toggle the lock-and-leave feature.
- **📊 Sensors** - battery level, lock status (Locked / Unlocked / Jammed), and who last operated the lock.
- **Multi-lock** - every lock on your account is added automatically.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

## How It Works

Schlage Wi-Fi locks are cloud-connected. This integration signs in to your Schlage Home account and talks to the same cloud service the Schlage Home app uses:

- **One account, all locks** - every lock on the account is added.
- **State follows the lock** - lock status, battery, and last-operated-by are polled from the cloud.
- **Commands are re-checked** - after a lock/unlock, the lock's state is re-read from the cloud rather than assumed.

> Because this is a cloud integration, your Remote must have internet access and the Schlage cloud must be reachable.

## Requirements

- A Schlage Home account with at least one Wi-Fi lock.
- Your Schlage Home **username (email) and password**.
- Unfolded Circle Remote 2 / 3 with firmware supporting custom integrations.

## Installation

### Option 1: Remote Web Interface (Recommended)

1. Download the latest `uc-intg-schlage-<version>.tar.gz` from the [**Releases**](https://github.com/mase1981/uc-intg-schlage/releases) page.
2. Open your Remote's web interface (`http://your-remote-ip`).
3. Go to **Settings → Integrations → Add Integration → Install Custom** and upload the `.tar.gz`.

### Option 2: Docker (Advanced Users)

**Image**: `ghcr.io/mase1981/uc-intg-schlage:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-schlage:
    image: ghcr.io/mase1981/uc-intg-schlage:latest
    container_name: uc-intg-schlage
    network_mode: host
    volumes:
      - ./config:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-intg-schlage --restart unless-stopped --network host -v $(pwd)/config:/config -e UC_CONFIG_HOME=/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-schlage:latest
```

## Configuration

1. Start setup and enter your Schlage Home **username (email)** and **password**.
2. The integration signs in and adds every lock on the account.

For each lock the integration creates:

| Entity | Purpose |
|--------|---------|
| **Switch** (`<name>`) | Lock / unlock (on = locked). |
| **Select** (`<name> Auto-Lock`) | Auto-lock delay. |
| **Switch** (`<name> Beeper`) | Keypad beeper on/off. |
| **Switch** (`<name> Lock & Leave`) | Lock-and-leave on/off. |
| **Sensors** | Battery level, lock status, and last operated by. |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Could not sign in to Schlage" | Check the username (email) and password (the same you use in the Schlage Home app). |
| "No locks were found" | Make sure the lock is set up and visible in the Schlage Home app first. |
| Lock shows unavailable | The lock is offline (no Wi-Fi) or the Schlage cloud is unreachable; it recovers automatically when connectivity returns. |
| Status shows "Jammed" | The lock reported a jam; check the deadbolt physically. |

## Credits

- **Developer**: Meir Miyara
- **Schlage cloud API**: based on the [pyschlage](https://github.com/dknowles2/pyschlage) library and the Home Assistant Schlage integration.
- **Unfolded Circle**: Remote 2/3 integration framework ([ucapi](https://github.com/unfoldedcircle/integration-python-library) / [ucapi-framework](https://github.com/JackJPowell/ucapi-framework)).

## License

Mozilla Public License 2.0 (MPL-2.0) - see the LICENSE file.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-schlage/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara
