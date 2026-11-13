# Photoshop Integration

### Implemented features

- publishing workfile
- publishing image product type
  - for each layer
  - for all visible layers altogether
- loading image/image sequences
- referencing image
- manage version of loaded containers
- M-Series chips compatibility through UXP

## Setup

The Photoshop integration requires two components to work; `extension` and `server`.

**Using the extension:**

In the AYON Studio Settings for Photoshop, use the **Plugin Type** option to select either CEP or UXP (CEP is default). The easiest way to make the plugin available, is through turning on **Install plugin automatically** (On by default). Before launching Photoshop, the integration will make sure the right plugin is available within your launched instance of Photoshop.

### About the Extensions

There need to be done several setup steps first before running the AYON integration. First your active project need to have Photoshop (PS) defined in the project anatomy as an available tool including its filepath to the executable (being set by default). Secondly its neccessary to install PS extension manager which simplifies future extensions installation / management for PS. We skip the first step due to the fact it should be already preset by TD / Admin. And we jump to the second step instead right away.

The AYON integration has been extended to cover 2 standards, the (heading towards legacy and deprecation) CEP standard, and the newer UXP standard.

**CEP (Windows, x86_64 MacOs):**

To install the extension manager , open the following link and download it first Anastasyi's Extension Manager. Open Anastasyi's Extension Manager and select Photoshop in the menu. Then go to {path to PS addon}hosts/photoshop/api/extension.zxp. Current location will be most likely in /User/AppData, on WINDOWS it would be something like c:\Users\YOUR_USER\AppData\Local\Ynput\AYON\addons\core_xx.xx.xx\ayon_core\hosts\photoshop\api, on Mac ~/Library/Application Support/Ynput/AYON/addons

**UXP (All modern platforms):**

The Creative Cloud offers "UXP Developer Tools": **[UXP Developer tools Installation guide](https://developer.adobe.com/photoshop/uxp/2022/guides/devtool/installation)**. This tool allows one to select the `manifest.json` and run a UXP package inside the targeted software after startup. Installed UXP plugins are deployed using the `UniversalPluginInstallerAgent (UPIA)` utility that Creative Cloud ships with. The main Creative Cloud application can be used to manage and uninstall plugins manually should you desire.

### Server

The easiest way to get the server and Photoshop launch is with:

```
python -c ^"import ayon_photoshop;ayon_photoshop.launch(""C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe"")^"
```

`ayon_photoshop.launch` launches the application and server, and also closes the server when Photoshop exists.

## Usage

**CEP:**

The Photoshop CEP extension can be found under `Window > Extensions > Ayon`. Once launched you should be presented with a panel with white buttons.

**UXP:**

The Photoshop UXP extension can be found under `Plugins > AYON > AYON`. Once Launched, you should be presented with a panel with blue buttons.

## Developing

### Extension

**CEP:**

When developing the extension you can load it [unsigned](https://github.com/Adobe-CEP/CEP-Resources/blob/master/CEP_9.x/Documentation/CEP%209.0%20HTML%20Extension%20Cookbook.md#debugging-unsigned-extensions).

When signing the extension you can use this [guide](https://github.com/Adobe-CEP/Getting-Started-guides/tree/master/Package%20Distribute%20Install#package-distribute-install-guide).

```
ZXPSignCmd -selfSignedCert NA NA Ayon Ayon-Photoshop Ayon extension.p12
ZXPSignCmd -sign {path to ayon-photoshop}\client\ayon-photoshop\api\extension {path to ayon-photoshop}\client\ayon-photoshop\api\extension.zxp extension.p12 ayon
```

**UXP:**

The easiest way is to use aforementioned UXP developer tools, NodeJS + ESLint, with the npm package `adobe-uxp-types/photoshop`. Just `cd ./extension_uxp` and run `npm install` to automatically collect all dependencies. Detailed information on developing and packaging with UXP is available **[here](./extension_uxp/README.md)** with further development notes / peculiarities mentioned **[in the UXP notes](./extension_uxp/ayon_uxp/NOTES.MD)**.

### Plugin Examples

The CEP plugin was made with the [polly config](https://github.com/mindbender-studio/config). To fully integrate and load, you will have to use this config and add `image` to the [integration plugin](https://github.com/mindbender-studio/config/blob/master/polly/plugins/publish/integrate_asset.py).

For easier debugging of Javascript:
https://community.adobe.com/t5/download-install/adobe-extension-debuger-problem/td-p/10911704?page=1
Add --enable-blink-features=ShadowDOMV0,CustomElementsV0 when starting Chrome
then localhost:8078 (port set in `ayon-photoshop}\client\ayon-photoshop\api\.debug`)

Or use Visual Studio Code https://medium.com/adobetech/extendscript-debugger-for-visual-studio-code-public-release-a2ff6161fa01

Or install CEF client from https://github.com/Adobe-CEP/CEP-Resources/tree/master/CEP_9.x

## Resources
  - https://github.com/lohriialo/photoshop-scripting-python
  - https://www.adobe.com/devnet/photoshop/scripting.html
  - https://github.com/Adobe-CEP/Getting-Started-guides
  - https://github.com/Adobe-CEP/CEP-Resources
