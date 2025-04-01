# ClipMail - macOS Tray App for Sending Clipboard to Email

**ClipMail** is a lightweight macOS tray app that lets you:

- Send selected text from your clipboard to one or more email addresses using Gmail (OAuth)
- Log each message to a date-stamped log file, automatically committed and pushed to a Git repo
- Trigger from a hotkey (`Cmd+Shift+C`)
- View logs from the tray menu (`Today`, `Yesterday`, `2 Days Ago`)
- Configure settings via a built-in GUI and securely store them encrypted in macOS Keychain

## Features

- **Global Hotkey**: Press `Cmd+Shift+C` to instantly send clipboard content
- **Secure Config Storage**: Uses macOS Keychain and Fernet encryption
- **Gmail Integration**: Uses Gmail API with OAuth2 (no passwords stored)
- **Daily Log Files**: Logs are rotated daily and pushed to a Git repo
- **GUI Pickers**: Choose files and folders easily when configuring
- **Log Viewer**: See the last 3 logs from the tray menu or open the log folder

## Installation

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/clipmail.git
cd clipmail
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
python3 clipboard_mail_tray.py
```

## First Time Setup

- Select your Gmail `credentials.json` (from Google Cloud Console)
- Choose a Git-tracked folder to store logs (should already have `git init` and a remote)
- Enter recipient email addresses
- ClipMail stores your config securely in Keychain

## Creating OAuth Credentials

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable Gmail API
3. Create OAuth Client ID (Desktop app)
4. Download `credentials.json`

## Git Logging Notes

- Log files are stored as `sent_email_log_YYYY-MM-DD.txt`
- Automatically added, committed, and pushed to the configured Git repo
- Uses the system’s Git CLI — make sure you’re authenticated with remotes

## Packaging (Optional)

You can bundle ClipMail into a `.app` using `py2app` or `pyinstaller` if you want it like a native app.

## License

MIT

## Contributions

Feel free to fork and extend this. PRs welcome!
