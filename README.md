<img width="462" height="579" alt="image" src="https://github.com/user-attachments/assets/861c842f-fbd4-4af5-9c63-66cf18ca1e01" />

### Features

* **Interactive Dial:** Smooth, drag-to-set circular timer.
* **Quick Controls:** `+/- 10s`, `+/- 1m`, and a `MAX` button for fast, precise tuning.
* **Custom Presets:** Save, load, and delete your favorite times.
* **Auto-Reset (Rep Mode):** Dismissing the alarm instantly resets the clock to your last used time—perfect for workout sets.
* **Bring-to-Front:** The window automatically pops to the foreground when the timer goes off.
* **Double-Tap Failsafe:** Prevents accidental pauses; requires a double-click (or Spacebar/Enter) to pause an active timer.
* **5 Color Themes:** Switch between Red, Cyan, Purple, Green, and Gold.
* **Auto-Save:** Automatically remembers your theme and presets for your next session.
* **Standalone `.exe`:** A single, lightweight desktop app with a futuristic glass UI.

how to compile:
1) update chrono_sync.py
2) open terminal then run:
pyinstaller --noconsole --onefile --icon=chrono_sync.ico chrono_sync.py
3) find .exe in dist
