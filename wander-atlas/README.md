# Wander Atlas

A travel atlas for your PC: mark the countries, cities and landmarks you have visited, keep a bucket list, drop your own pins and plan trips on a world map. It works offline.

## Run it

**As a Python app** (Windows, macOS, Linux; Python 3.8 or newer, nothing to install):

1. Download this repository (**Code → Download ZIP**) and unzip it.
2. In the `wander-atlas` folder, run:

   ```bash
   python wander_atlas.py
   ```

Wander Atlas opens in your browser, and a small window lets you reopen or quit it.

**As a Windows exe** (no Python needed):

- Download `WanderAtlas.exe` from the repository's **Releases** page, or from the latest **Actions → Build Wander Atlas exe** run (artifact `WanderAtlas-windows`), and double-click it.
- Windows may show a SmartScreen warning because the exe is not signed; choose **More info → Run anyway**.

To build the exe yourself on Windows:

```bash
pip install pyinstaller
```

```bash
pyinstaller --noconfirm --onefile --windowed --name WanderAtlas --add-data "web;web" wander_atlas.py
```

To publish a new release with the exe attached, push a tag named `wander-atlas-v<version>` (for example `wander-atlas-v1.0`).

## Your data

Your travel log is saved on your computer, not online:

- Windows: `%APPDATA%\WanderAtlas\atlas.json`
- macOS: `~/Library/Application Support/WanderAtlas/atlas.json`
- Linux: `~/.local/share/WanderAtlas/atlas.json`

Copy that file to back it up or move it to another PC. It starts empty: places saved in the online version are not carried over.

Options: `--port <number>` to use another local port, `--no-browser` to start without opening the browser.

## Credits

Borders from Natural Earth, cities from GeoNames (CC BY 4.0). Map rendering by [Leaflet](https://leafletjs.com) (BSD-2-Clause) and [topojson-client](https://github.com/topojson/topojson-client) (ISC); their licenses are in `web/vendor`.
