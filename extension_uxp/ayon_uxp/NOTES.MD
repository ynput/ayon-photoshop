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
This has led us to have to decide that this plugin will need to communicate over a fixed address.

When developing, in the Studio settings for (hopefully your dev bundle) set: <br>
"Install plugin automatically": Off
"Plugin Type": UXP

Then, when photoshop starts, use the UXP Developer tools to start up your plugin in "Load and Watch" mode. This allows you to expose a "Debug" window that lets you see what gets logged to console!

I hope you are ready to have lots of fun, as things can get quite confusing. There is a vast difference between plugin standards between CEP and UXP, and things that are trivial in one can be complicated in the other.
Some attributes like the document dit depth are read/write in CEP, you can trivially set the bit depth by changing a value, when in UXP this requires a batchPlay function.
Be really careful about this.

Enjoy, 

Sas