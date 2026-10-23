AYON Photoshop UXP Plugin notes
---

### Back to [UXP Readme.](../README.md)

Instead of relying on CSInterface.js, we rely on the internal `const uxp = require("uxp")` library.<br>
Note, that we are using CommonJS style import/export.

That means:

```js
// importing through structured binding from a 'require' statement
const {module1, module2} = require("photoshop");

// exporting through writing to a 'module.exports' object

/**
 * @param {number} my_number 
 */
async function my_glorious_function(my_number) {
    return await crunch(number);
}

module.exports = {
    my_glorious_function,
    ...
}
```

And generally a preference to keep things async.
Some operations that mutate state definitely need to "lock up" the program,<br>
and for this I've written a helper function.

```js
// Can be found in client_api.js

const {app, core} = require("photoshop")
// Helper to execute "Modal", Blocking
// Wrapper for functions that need to write.
/**
 * @param {function} func 
 * @param {string} commandName 
 */
async function execAsModal(func, commandName) {
    return await core.executeAsModal(async () => {
        return await func();
    }, {"commandName": commandName})
}
```

Be sure to make your command name unique!

One special thing about photoshop's handling of files in certain operations, is that in<br>
certain `batchPlay` operations (New way of executing 'Action' macros in JS in UXP / Photoshop),<br>
The pathname must first be made into a file entry and then opened into a with a session token.

Autocomplete will not show you this function, but it's documented [Here.](https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/FileSystemProvider/#createsessiontokenentry)

Another quirk of UXP, is that it's not able to arbitrarily read files that aren't packaged anymore.
Therefore we can't go and read stuff from our filesystem, in other textfiles that werent present
in the folder that is bundled.

Yet another quirk: **UXP Plugins can NOT read environment variables.**
This has led me to have to decide that this plugin will need to communicate over a fixed address.

The easiest way to get it to talk to the plugin for testing is to go to 
`client/ayon_photoshop/api/webserver.py`, line 45.

```py
class WebServerTool:
    """
        Basic POC implementation of asychronic websocket RPC server.
        Uses class in external_app_1.py to mimic implementation for single
        external application.
        'test_client' folder contains two test implementations of client
    """
    _instance = None

    def __init__(self):
        WebServerTool._instance = self

        self.client = None
        self.handlers = {}
        self.on_stop_callbacks = []

        port = None
        host_name = "localhost"
        websocket_url = "ws://localhost:8101/ws/" # Line 45 original: os.getenv("WEBSOCKET_URL")
```

If you want to change the port, please change it in the modified<br>
`client/ayon_photoshop/api/webserver.py` like above, <br>
the `manifest.json` 'requiredPermissions' key ->
```js
"requiredPermissions": {
    "network": {
      "domains": [
        "all", 
        "ws://localhost:8101" // <- Modify 8101 here to allow port through.
      ]
    },
    "localFileSystem": "fullAccess"
  }
```

and in the plugin itself, in `ayon-photoshop/extension_uxp/main.js`

```js
const get_RPC = require("./client_RPC").get_RPC
const setup_rpc = require("./client_RPC").setup_rpc

const WS_URL = "ws://localhost:8101/ws/"; // <- Modify 8101 here to allow port through.

let RPC = null;
```
