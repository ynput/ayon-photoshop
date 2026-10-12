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

### Automatic installation

Enable the project setting **Install AYON UXP Plugin** (`install_uxp_plugin`,
off by default). A pre-launch hook then installs the packaged
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

### Note: This plugin is hardcoded to use a specific websocket port/adress:
The adress we use is: `ws://localhost:8101/ws/`

Modify Line 45 in `client/ayon_photoshop/api/webserver.py`

```py
# in class WebServerTool, __init__(...
websocket_url = "ws://localhost:8101/ws/" # Line 45 original: os.getenv("WEBSOCKET_URL")
```

This is to cause no collision with the existing CEP plugin, but also because<br>
**UXP Plugins can NOT read environment variables.**

This, next to the need to EXPLICITLY allow `ws://localhost:8101` in the manifest allowed domains<br>
('all' is not enough since that only counts for http / https connections),<br>
makes it far less viable to dynamically inject a port number.

When using the UXP plugin, this should be taken into account. 

### Further setup documentation can be found in the NOTES: [Here!](./ayon_uxp/NOTES.MD)

(It's quite complicated and different so I would recommend it.)

Much love, Sas