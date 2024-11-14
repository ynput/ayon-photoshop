# Photoshop Integration

### Implemented features

- publishing workfile
- publishing image product type
  - for each layer
  - for all visible layers altogether
- loading image/image sequences
- referencing image
- manage version of loaded containers

## Setup

The Photoshop integration requires two components to work; `extension` and `server`.

### Extension

There need to be done several setup steps first before running the AYON integration. First your active project need to have Photoshop (PS) defined in the project anatomy as an available tool including its filepath to the executable (being set by default). Secondly its neccessary to install PS extension manager which simplifies future extensions installation / management for PS. We skip the first step due to the fact it should be already preset by TD / Admin. And we jump to the second step instead right away.

To install the extension manager , open the following link and download it first Anastasyi's Extension Manager. Open Anastasyi's Extension Manager and select Photoshop in the menu. Then go to {path to PS addon}hosts/photoshop/api/extension.zxp. Current location will be most likely in /User/AppData, on WINDOWS it would be something like c:\Users\YOUR_USER\AppData\Local\Ynput\AYON\addons\core_xx.xx.xx\ayon_core\hosts\photoshop\api. On Linux look in ~/.local/share/Ynput/AYON/addons, on Mac ~/Library/Application Support/Ynput/AYON/addons


### Server

The easiest way to get the server and Photoshop launch is with:

```
python -c ^"import ayon_photoshop;ayon_photoshop.launch(""C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe"")^"
```

`ayon_photoshop.launch` launches the application and server, and also closes the server when Photoshop exists.

## Usage

The Photoshop extension can be found under `Window > Extensions > Ayon`. Once launched you should be presented with a panel like this:

![Ayon Panel](panel.png "AYON Panel")


## Developing

### Extension
When developing the extension you can load it [unsigned](https://github.com/Adobe-CEP/CEP-Resources/blob/master/CEP_9.x/Documentation/CEP%209.0%20HTML%20Extension%20Cookbook.md#debugging-unsigned-extensions).

When signing the extension you can use this [guide](https://github.com/Adobe-CEP/Getting-Started-guides/tree/master/Package%20Distribute%20Install#package-distribute-install-guide).

```
ZXPSignCmd -selfSignedCert NA NA Ayon Ayon-Photoshop Ayon extension.p12
ZXPSignCmd -sign {path to ayon-photoshop}\client\ayon-photoshop\api\extension {path to ayon-photoshop}\client\ayon-photoshop\api\extension.zxp extension.p12 ayon
```

### Plugin Examples

These plugins were made with the [polly config](https://github.com/mindbender-studio/config). To fully integrate and load, you will have to use this config and add `image` to the [integration plugin](https://github.com/mindbender-studio/config/blob/master/polly/plugins/publish/integrate_asset.py).

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
