const {app, action, core, constants, LayerKind, Layer, Document} = require("photoshop")
const uxp_storage = require("uxp").storage
const batchPlay = action.batchPlay;

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

/**
 * @param {string} path 
 */
async function fileOpen(path) {
    return await execAsModal(async () => {
        const fileEntry = await uxp_storage.localFileSystem.getEntryWithUrl(`file:${path}`);
        await app.open(fileEntry);
        return path;
    }, "Open Document");
}

async function save() {
    return await execAsModal(async () => {
        app.activeDocument.save();
    }, "Save Document");
}

async function getActiveDocument() {
    const doc = app.activeDocument;
    if (!doc){
        return null;
    }
    return doc;
}

async function getActiveDocumentFullName() {
    const doc = await getActiveDocument();
    if (doc) {
        return doc.path;
    } else {
        return null;
    }
}

async function getActiveDocumentName() {
    const doc = await getActiveDocument();
    if (doc) {
        return doc.name;
    } else {
        return null;
    }
}

async function getColorProfileName() {
    const doc = await getActiveDocument();
    if (doc) {
        return doc.colorProfileName;
    } else {
        return null;
    }
}

function getLayerTypeWithName(layerName) {
    const namePrefix = layerName.split('_')[0].toLowerCase();
    switch (namePrefix) {
        case 'guide':
        case 'tl':
        case 'tr':
        case 'bl':
        case 'br':
            return 'GUIDE';
        case 'fg':
            return 'FG';
        case 'bg':
            return 'BG';
        case 'obj':
        default:
            return 'OBJ';
    }
}

async function getLayers() {
    if (app.documents.length === 0) {
        return "[]";
    }

    // 1) Get the number of layers in the active document
    const [docInfo] = await batchPlay(
        [{
            _obj: "get",
            _target: [
                { _property: "numberOfLayers" },
                { _ref: "document", _enum: "ordinal", _value: "targetEnum" }
            ]
        }],
        { synchronousExecution: true }
    );
    const count = docInfo.numberOfLayers;

    // 2) Build one batchPlay call that fetches every layer's descriptor at once.
    //    This is dramatically faster than calling batchPlay per layer.
    const getCommands = [];
    for (let i = count; i >= 1; i--) {
        getCommands.push({
            _obj: "get",
            _target: [{ _ref: "layer", _index: i }]
        });
    }
    const descriptors = await batchPlay(getCommands, { synchronousExecution: true });

    // 3) Walk the descriptors top-to-bottom (highest index first), tracking parents
    const layers = [];
    const parents = [];

    for (const desc of descriptors) {
        const layerSection = desc.layerSection?._value; // "layerSectionContent" | "layerSectionStart" | "layerSectionEnd"

        // Group end marker: pop parent and skip (don't emit a layer)
        if (layerSection === "layerSectionEnd") {
            parents.pop();
            continue;
        }

        const layer = {
            id: desc.layerID,
            name: desc.name,
            color_code: desc.color?._value ?? "none",
            group: false,
            parents: parents.slice(),
            type: getLayerTypeWithName(desc.name),
            visible: desc.visible
        };

        if (layerSection === "layerSectionStart") {
            layer.group = true;
            parents.push(layer.id);
        }

        layers.push(layer);
    }

    // 4) Background layer (if any)
    try {
        const bg = app.activeDocument.backgroundLayer;
        if (bg) {
            layers.push({
                id: bg.id,
                name: bg.name,
                color_code: "none",
                group: false,
                parents: [],
                type: "background",
                visible: bg.visible
            });
        }
    } catch (e) {
        // no background layer
    }

    return JSON.stringify(layers);
}

/**
 * Delete the layer with the given id.
 */
async function deleteLayer(layer_id) {
    await execAsModal(async () => {
        await batchPlay([{
            _obj: "delete",
            _target: [{ _ref: "layer", _id: layer_id }],
            _options: { dialogOptions: "dontDisplay" }
        }], { synchronousExecution: true });
    }, "Delete Layer");
}

async function isSaved() {
    return app.activeDocument.saved;
}

/**
 * Revert to last saved state of document
 */
async function revertToPrevious() {
    await execAsModal(async () => {
        await batchPlay(
            [{
                _obj: "revert",
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );
    }, "Revert");
}

/**
 * @param {Layer} layer
*/
async function isLayerGroup(layer) {
    return (layer.kind == LayerKind.GROUP);
}

async function getSelectedLayers() {
    if (app.documents.length === 0) return "[]";
    try{
    const selected = app.activeDocument.activeLayers;
    const result = selected.map(layer => ({
        id: layer.id,
        name: layer.name,
        group: layer.kind == LayerKind.GROUP,
        long_name: _get_parents_names(layer, layer.name)
    }));

    return JSON.stringify(result);
    } catch (err) {
        console.log(err)
    }
    return "[]"
}

/**
 * @param {Document} doc 
 * @param {number} id 
 * @returns {Layer}
 */
function findLayerById(doc, id) {
    function walk(layers) {
        for (const l of layers) {
            if (l.id === id) return l;
            if (l.layers) {
                const found = walk(l.layers);
                if (found) return found;
            }
        }
    }
    return walk(doc.layers);
}

/**
 * Sets layer with given id to the given visibility.
 * @param {number}  layer_id
 * @param {boolean} visibility - true = show, false = hide
 */
async function setVisible(layer_id, visibility) {
    const layer = findLayerById(app.activeDocument, layer_id);
    if (!layer) return false;

    await execAsModal(async () => {
        layer.visible = !!visibility;
    }, "Set Layer Visibility");

    return true;
}

/**
 * Imprints data into the headline of the current document's metadata.
 */
async function imprint(payload) {
    await execAsModal(async () => {
        await batchPlay(
            [
                {
                    _obj: "set",
                    _target: [
                        {
                            _ref: "property",
                            _property: "fileInfo"
                        },
                        {
                            _ref: "document",
                            _enum: "ordinal",
                            _value: "targetEnum"
                        }
                    ],
                    to: {
                        _obj: "fileInfo",
                        headline: payload
                    }
                }
            ],
            { synchronousExecution: true }
        );
    }, "Imprint Headline");
}

/**
 * Returns the headline of the current document's metadata.
 */
async function getHeadline() {
    if (app.documents.length === 0) {
        return "";
    }

    const result = await batchPlay(
        [{
            _obj: "get",
            _target: [
                { _property: "fileInfo" },
                { _ref: "document", _enum: "ordinal", _value: "targetEnum" }
            ]
        }],
        { synchronousExecution: true }
    );

    return result[0]?.fileInfo?.headline ?? "";
}

function _get_parents_names(layer, itself_name) {
    const long_names = [itself_name];
    let current = layer.parent;

    // Walk up while we're still inside a group
    while (current && current.kind === LayerKind.GROUP) {
        long_names.push(current.name);
        current = current.parent;
    }
    return long_names;
}

/**
 * Selects layers from list of ids
 */
async function selectLayers(selectedLayers) {
    if (typeof selectedLayers === "string") {
        selectedLayers = JSON.parse(selectedLayers);
    }

    // Build list of currently existing IDs to filter against
    const existing = JSON.parse(await getLayers());
    const existingIds = new Set(existing.map(l => l.id));

    const refs = selectedLayers
        .filter(id => existingIds.has(id))
        .map(id => ({ _ref: "layer", _id: id }));

    if (refs.length === 0) return;

    await execAsModal(async () => {
        await batchPlay(
            [{
                _obj: "select",
                _target: refs,
                makeVisible: false,
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );
    }, "Select Layers");
}

/**
 * Rename the layer with the given id.
 */
async function renameLayer(layer_id, new_name) {
    const layer = findLayerById(app.activeDocument, layer_id);
    if (!layer) return false;
    await execAsModal(async () => {
        layer.name = new_name;
    }, "Rename Layer");
    return true;
}

/**
 * Create a new empty group at the document root.
 * @returns {number} id of the new group
 */
async function createGroup(name) {
    let group;
    await execAsModal(async () => {
        group = await app.activeDocument.createLayerGroup({ name });
    }, "Create Group");
    return group.id;
}



/**
 * Groups currently-selected layers into a new group.
 * Returns JSON representation of the created group layer.
 */
async function groupSelectedLayers(doc, name) {
    doc = doc || app.activeDocument;
    let group;

    await execAsModal(async () => {
        await batchPlay(
            [{
                _obj: "make",
                _target: [{ _ref: "layerSection" }],
                from: { _ref: "layer", _enum: "ordinal", _value: "targetEnum" },
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );

        group = doc.activeLayers[0];
        if (name) {
            group.name = name;
        }
    }, "Group Selected Layers");

    return JSON.stringify({
        id: group.id,
        name: name,
        group: true,
        long_name: _get_parents_names(group, name)
    });
}

/**
 * Select a PS layer by id. Returns nothing; caller can read app.activeDocument.activeLayers.
 * NOTE: must be called inside an executeAsModal scope.
 */
async function selectObject(id) {
    await batchPlay(
        [{
            _obj: "select",
            _target: [{ _ref: "layer", _id: id }],
            _options: { dialogOptions: "dontDisplay" }
        }],
        { synchronousExecution: true }
    );
}

/**
 * Delete a layer set and move its child layers to the parent.
 */
async function dissolveLayerSet(layerSetId) {
    await execAsModal(async () => {
        await selectObject(layerSetId);
        const layerSet = app.activeDocument.activeLayers[0];

        // Snapshot the children (the list mutates as we move them)
        const children = layerSet.layers.slice();

        // Move each child out to the document root (end of stack)
        for (const child of children) {
            await child.move(app.activeDocument, constants.ElementPlacement.PLACEATEND);
        }

        // Delete the now-empty group
        await batchPlay(
            [{
                _obj: "delete",
                _target: [{ _ref: "layer", _id: layerSetId }],
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );
    }, "Dissolve Layer Set");
}

/**
 * Merge all layer sets inside the given parent (or at root if not given),
 * preserving each merged result's visibility.
 */
async function mergeAllLayerSets(parentSetId) {
    await execAsModal(async () => {
        let layerSets;

        if (parentSetId !== undefined && parentSetId !== null && parentSetId !== "undefined") {
            await selectObject(parentSetId);
            const parent = app.activeDocument.activeLayers[0];
            layerSets = parent.layers.filter(l => l.kind === constants.LayerKind.GROUP);
        } else {
            layerSets = app.activeDocument.layers.filter(l => l.kind === constants.LayerKind.GROUP);
        }

        // Iterate in reverse so indices stay valid as we mutate the stack
        for (let i = layerSets.length - 1; i >= 0; i--) {
            const ls = layerSets[i];
            const visibility = ls.visible;
            const merged = await ls.merge();
            merged.visible = visibility;
        }
    }, "Merge All Layer Sets");
}

/**
 * Place an image as a smart object.
 *      path: absolute path to file
 *      name: optional name for the new layer
 *      link: if true, place as a linked smart object instead of embedded
 */
async function importSmartObject(path, name, link) {
    let normalizedPath = path.replace(/\\/g, "/");
    let layer;
    // Somehow, "▼" shows up in names coming from ayon leading to illegal readouts.
    name = name.replace("▼","")
    //if (os.platform() === "win32") {
    //    normalizedPath = "file:///" + normalizedPath; 
    //} else {
    //    normalizedPath = "file://" + normalizedPath;
    //}

    await execAsModal(async () => {
        //const fileEntry = await uxp_storage.localFileSystem.createEntryWithUrl(normalizedPath, { overwrite: true });
        //console.log(fileEntry, typeof fileEntry)
        console.log(normalizedPath)
        const fileEntry = await uxp_storage.localFileSystem.createEntryWithUrl(normalizedPath, { overwrite: true });
        let sessionToken = uxp_storage.localFileSystem.createSessionToken(fileEntry);
        const command = {
            _obj: "placeEvent",
            null: { _path: sessionToken, _kind: "local" },
            freeTransformCenterState: {
                _enum: "quadCenterState",
                _value: "QCSAverage"
            },
            offset: {
                _obj: "offset",
                horizontal: { _unit: "pixelsUnit", _value: 0.0 },
                vertical:   { _unit: "pixelsUnit", _value: 0.0 }
            },
            _options: { dialogOptions: "dontDisplay" }
        };

        if (link) {
            command.linked = true;
        }

        await batchPlay([command], { synchronousExecution: true });

        layer = app.activeDocument.activeLayers[0];
        if (name) {
            layer.name = name;
        }
    }, "Import Smart Object");

    return JSON.stringify({
        id: layer.id,
        name: layer.name
    });
}


/**
 * Replace the content of an existing smart-object layer.
 */
async function replaceSmartObjects(layer_id, path, name) {
    let normalizedPath = path.replace(/\\/g, "/");
    name = name.replace("▼","")
    return await execAsModal(async () => {
        const fileEntry = await uxp_storage.localFileSystem.createEntryWithUrl(normalizedPath, { overwrite: true });
        let sessionToken = uxp_storage.localFileSystem.createSessionToken(fileEntry);
        await batchPlay(
            [{
                _obj: "placedLayerReplaceContents",
                _target: [{ _ref: "layer", _id: layer_id }],
                null: { _path: sessionToken, _kind: "local" },
                pageNumber: 1,
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );

        if (name) {
            const layer = app.activeDocument.activeLayers[0];
            layer.name = name;
        }
    }, "Replace Smart Object");
}

async function saveAs(imagePath, ext, asCopy) {
    asCopy = !!asCopy;
    const format = (ext || "").toLowerCase();
    const url = "file:" + imagePath.replace(/\\/g, "/");

    await execAsModal(async () => {
        const doc = app.activeDocument;

        switch (format) {
            case "jpg":
            case "jpeg": {
                const entry = await uxp_storage.localFileSystem.createEntryWithUrl(url, { overwrite: true });
                await doc.saveAs.jpg(entry, {
                    quality: 12,
                    embedColorProfile: true,
                    formatOptions: "progressive",
                    scans: 5,
                    matte: "noMatte"
                }, asCopy);
                break;
            }

            case "png": {
                const entry = await uxp_storage.localFileSystem.createEntryWithUrl(url, { overwrite: true });
                await doc.saveAs.png(entry, {
                    compression: 6,
                    interlaced: true
                }, asCopy);
                break;
            }

            case "psd": {
                const entry = await uxp_storage.localFileSystem.createEntryWithUrl(url, { overwrite: true });
                await doc.saveAs.psd(entry, {
                    embedColorProfile: true,
                    alphaChannels: true,
                    layers: true,
                    annotations: true,
                    spotColors: true,
                    maximizeCompatibility: true
                }, asCopy);
                break;
            }

            case "psb": {
                const entry = await uxp_storage.localFileSystem.createEntryWithUrl(url, { overwrite: true });
                await doc.saveAs.psb(entry, {
                    embedColorProfile: true,
                    alphaChannels: true,
                    layers: true,
                    annotations: true,
                    spotColors: true,
                    maximizeCompatibility: true   // required for PSB
                }, asCopy);
                break;
            }

            case "tga":
                await batchPlay([{
                    _obj: "save",
                    as: {
                        _obj: "targaFormat",
                        depth: 32,
                        alphaChannels: true,
                        rleCompression: true
                    },
                    in: { _path: imagePath, _kind: "local" },
                    copy: asCopy,
                    lowerCase: true,
                    _options: { dialogOptions: "dontDisplay" }
                }], { synchronousExecution: true });
                break;

            default:
                throw new Error("saveAs: unsupported extension '" + ext + "'");
        }
    }, "Save As");

    return imagePath;
}

/**
 * Duplicate the active document.
 * @param {string} newName - name for the duplicated document
 * @returns {number} - id of the duplicated document
 */
async function duplicateDocument(newName) {
    let newDoc;
    await execAsModal(async () => {
        newDoc = await app.activeDocument.duplicate(newName);
    }, "Duplicate Document");
    return newDoc.id;
}

/**
 * Close document with given ID. If no ID, closes the active document.
 * @param {number} [documentId]
 * @throws if a documentId is given but not found
 */
async function closeDocument(documentId) {
    let document;
    if (documentId === undefined || documentId === null) {
        document = app.activeDocument;
    } else {
        document = app.documents.find(d => d.id === documentId);
        if (!document) {
            throw new Error("Document with ID " + documentId + " not found.");
        }
    }

    if (!document) return false;   // no active document case

    await execAsModal(async () => {
        await document.closeWithoutSaving();
    }, "Close Document");

    return true;
}

/**
 * Returns version number from manifest.json (UXP)
 */
async function getExtensionVersion() {
    try {
        const pluginFolder = await uxp_storage.localFileSystem.getPluginFolder();
        const manifestEntry = await pluginFolder.getEntry("manifest.json");
        const manifestText = await manifestEntry.read();

        // Parse manifest JSON
        const manifest = JSON.parse(manifestText);
        // UXP version field
        return manifest.version || null;

    } catch (err) {
        console.error("getExtensionVersion failed:", err);
        return null;
    }
}

async function closeApp() {
    await app.terminate();
}

module.exports = {
    execAsModal,
    fileOpen,
    save,
    getActiveDocument,
    getActiveDocumentFullName,
    getActiveDocumentName,
    getColorProfileName,
    getLayerTypeWithName,
    getLayers,
    deleteLayer,
    isSaved,
    revertToPrevious,
    isLayerGroup,
    getSelectedLayers,
    findLayerById,
    setVisible,
    imprint,
    getHeadline,
    selectLayers,
    renameLayer,
    createGroup,
    groupSelectedLayers,
    selectObject,
    dissolveLayerSet,
    mergeAllLayerSets,
    importSmartObject,
    replaceSmartObjects,
    saveAs,
    duplicateDocument,
    closeDocument,
    getExtensionVersion,
    closeApp,
};