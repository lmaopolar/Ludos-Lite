# Ludos — Privacy Toolkit (Made by Polar)

Ludos is a minimal, dark, rounded desktop app that helps you manage online privacy the right way. It does not hack or bypass provider systems. It focuses on what actually works: strong passwords, local TOTP codes (from your own exported secrets), formal takedown letters, and fast access to official removal and opt-out portals.

## Features
- Dark, minimal, rounded UI
- Strong password generator with optional rotation log
- TOTP authenticator codes using your exported Base32 secrets (stored via OS keyring)
- DMCA takedown letter generator
- GDPR or CCPA/CPRA deletion request generator
- One-click openers for account deletion, search/cache removal, and data-broker opt-outs

## Installation
1. Install Python 3.9 or newer.
2. Install dependencies using pip:
   pip install -r requirements.txt
3. Run the app:
   python ludos_gui.py

## Requirements
- Python 3.9+
- customtkinter
- pyotp
- keyring

## Usage notes
- Passwords: generate, copy, and optionally enable a rotation log written to your user directory.
- TOTP: only for accounts where you legitimately exported your Base32 secret. Labels and secrets are stored locally via the OS keyring.
- Letters: generate DMCA or GDPR/CCPA deletion requests and save them as text files you can send to platforms or hosts.
- Portals: open official account-deletion pages, search removal tools, and major data-broker opt-out forms in your default browser.

## Legal and ToS
Ludos does not and cannot erase server logs, delete third-party content, or bypass security. It streamlines legitimate workflows. You are responsible for complying with laws and each platform’s Terms of Service.

## Attribution
Made by Polar