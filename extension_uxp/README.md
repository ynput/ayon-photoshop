# uxp-ayon-photoshop

Migration of AYON CEP to UXP!

It's a new way to do things.<br>
Developed at Submarine, by Sas van Gulik, as commissioned by Thierry Paalman,<br>
in order to let M-series Macs participate in projects without having to work off pipe due to CEP not being allowed on these platforms, and CEP being marked as deprecated.

This fork is meant to open discussion on migrating or offering a CEP / UXP hybrid.

This folder contains everything you need to start developing with the JS stubs provided by Adobe.

Make sure that this directory (extension_uxp_develop) is your current directory, and
simply run:

`npm install`

to download the packages present in the `package.json`.

To use the plugin, you need to bundle it or "inject it" into photoshop while it's running.

First of all, check which version ayon_photoshop expects to be in the manifest.
This is the version that is found in `ayon_photoshop/api/extension/CSXS/manifest.xml`, <br>
and you would be looking for ExtensionBundleVersion. As of writing this, 0.4.4+dev,
the expected version is `1.1.11`. The bundled .ccx package has a baked in manifest version for 1.1.1 for example.

Then you can adjust the manifest.json in `extension_uxp/manifest.json` to reflect
this same version.

### Choosing between CEP and UXP

The project setting **Panel type** (`panel_type` in the Photoshop settings,
`cep` by default) selects the panel Photoshop uses. Only one can be active:
both would connect to the same server and requests would go to whichever
answered first.

With **Install panel automatically** (`auto_install_extension`) on, a
pre-launch hook installs the selected panel **and removes the other one**:

| Panel type | CEP extension | UXP plugin |
|---|---|---|
| `cep` | installed | removed |
| `uxp` | removed | installed |

Panels are only changed when Photoshop is launched from AYON. A Photoshop that
is already running keeps the panel it has until it is restarted. Existing
projects that had the old `install_uxp_plugin` switch on are converted to
`panel_type: uxp`.

The UXP plugin is installed from the packaged
`client/ayon_photoshop/api/com.ayon.photoshop_PS.ccx` with Adobe's own
command line installer, `UnifiedPluginInstallerAgent`, which comes with the
Creative Cloud desktop app. The hook is
`hooks/pre_launch_install_ayon_uxp_plugin.py`, the logic is in
`ayon_photoshop/uxp_installer.py` (standard library only).

What it does, every launch:

- same version already installed: nothing happens (a plugin the user disabled
  stays disabled)
- missing, older, newer or duplicated versions: every registered AYON version
  is removed, the packaged one is installed, then the result is read back
- installer not found or an install fails: a warning is logged and Photoshop
  starts anyway

To use a Creative Cloud in a non-standard place, set
`AYON_PHOTOSHOP_UPIA_PATH` to the executable.

Use the UXP developer tool (available in Adobe Creative Cloud desktop app) to develop or bundle this.
[Docs on UXP Developer tools](https://developer.adobe.com/photoshop/uxp/2022/guides/devtool/)

Using this tool you can either bundle the app after opening the folder with the manifest.json in it,
or you can `Load & Watch` it while you are running photoshop from Ayon or anywhere else.

If you bundle a .ccx, you can usually double click it to add it to your bundles,
and it will automatically load on startup.

### Websocket port

The UXP plugin can NOT read environment variables, so its address is written
into the plugin: `ws://localhost:8101/ws/`. The CEP panel reads
`WEBSOCKET_URL`, default `ws://localhost:8099/ws/`.

The server has to listen where the selected panel connects, so the hook
`hooks/pre_launch_panel_websocket.py` sets `WEBSOCKET_URL` from the panel
type: 8101 for `uxp`, 8099 for `cep` (a custom `WEBSOCKET_URL` is kept for
`cep` only).

The number lives in `ayon_photoshop/panel_type.py` (`UXP_WEBSOCKET_PORT`) and
**must match three places inside the plugin**, which is why changing it means
rebuilding the `.ccx`:

- `ayon_uxp/main.js` (`WS_URL`)
- `ayon_uxp/client_RPC.js` (`default_url`)
- `ayon_uxp/manifest.json`: `ws://localhost:8101` has to be listed explicitly
  in the network domains, `"all"` only covers http and https

### Further setup documentation can be found in the NOTES: [Here!](./ayon_uxp/NOTES.MD)

(It's quite complicated and different so I would recommend it.)

Much love, Sas