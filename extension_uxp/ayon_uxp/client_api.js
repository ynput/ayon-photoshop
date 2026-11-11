const {app, action, core, constants} = require("photoshop")
const uxp_storage = require("uxp").storage
const batchPlay = action.batchPlay;

// Photoshop's PSD maximum document dimension is 30,000 pixels.
const PSD_MAX_DIMENSION = 30000;

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

// File helpers

/**
 * Convert an absolute native path into a UXP file URL.
 *
 * Examples:
 *   C:\project\image.psd -> file:C:/project/image.psd
 *   /project/image.psd   -> file:/project/image.psd
 */
function toFileUrl(path) {
    const normalized = String(path).replace(/\\/g, "/");

    return normalized.startsWith("file:")
        ? normalized
        : `file:${normalized}`;
}

/**
 * Return an existing FileEntry, or null when it does not exist.
 */
async function getExistingFileEntry(fileUrl) {
    try {
        const entry = await uxp_storage.localFileSystem.getEntryWithUrl(fileUrl);

        if (!entry.isFile) {
            throw new Error(`Output path is not a file: ${fileUrl}`);
        }

        return entry;
    } catch (error) {
        // getEntryWithUrl throws for a non-existent file. Treat that case as
        // "not present"; the save operation will create the target.
        return null;
    }
}

/**
 * Get an existing output FileEntry, or create a new one.
 */
async function getOutputFileEntry(outputPath) {
    const fileUrl = toFileUrl(outputPath);
    const existing = await getExistingFileEntry(fileUrl);

    if (existing) {
        return {
            entry: existing,
            existedBefore: true
        };
    }

    const entry = await uxp_storage.localFileSystem.createEntryWithUrl(fileUrl);

    return {
        entry,
        existedBefore: false
    };
}

/**
 * Read output-file metadata, returning null if metadata cannot be read.
 */
async function getFileMetadata(fileEntry) {
    try {
        return await fileEntry.getMetadata();
    } catch (error) {
        return null;
    }
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
        await app.activeDocument.save();
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

async function getDocumentSize() {
    /**
     * Returns the size of the current document in pixels.
     *
     * Returns an object with width, height and unit, or null when no
     * document is open.
     **/

    if (app.documents.length === 0) {
        return null;
    }

    const doc = app.activeDocument;

    return {
        width: doc.width,
        height: doc.height,
        unit: "px"
    };
}

// TODO: once CEP support is dropped, report the raw UXP values ("RGBColorMode",
// "bitDepth8") and let validate_document_settings.py compare those directly.
// This lookup and that plugin's _normalize_mode/_normalize_bits helpers only
// exist to keep one validator working for both clients.
/**
 * Resolution, color mode and bit depth of the active document.
 *
 * mode and bitsPerChannel are the names of the enumeration values, e.g. "RGB"
 * and "EIGHT", which is what the publish validator compares against. UXP
 * constants are objects like {RGB: "<value>", CMYK: "<value>"} and a document
 * reports the value, not the name.
 *
 * @returns {Promise<string>} JSON with resolution, mode and bitsPerChannel.
 */
async function getDocumentSettings() {
    const doc = app.activeDocument;
    return JSON.stringify({
        resolution: doc.resolution,
        mode: Object.keys(constants.DocumentMode).find((key) => constants.DocumentMode[key] === doc.mode),
        bitsPerChannel: Object.keys(constants.BitsPerChannelType).find((key) => constants.BitsPerChannelType[key] === doc.bitsPerChannel),
    });
}

/**
 * Change resolution, color mode and bit depth of the active document.
 *
 * @param {number} resolution Resolution in dpi, pixels are not resampled.
 * @param {string} mode Key of constants.ChangeMode, e.g. "RGB".
 * @param {number|string} bits Bit depth: 8, 16 or 32.
 * @returns {Promise<string>} JSON {success: true}, or {success: false, errors}
 *     with one message per failed setting.
 */
async function setDocumentSettings(resolution, mode, bits) {
    const doc = app.activeDocument;
    if (typeof bits == "string") {
        bits = parseInt(bits)
    }
    const steps = [
        ["resolution", () => doc.resizeImage(
            undefined, undefined, resolution, constants.ResampleMethod.NONE
        )],
        ["color mode", () => doc.changeMode(
            constants.ChangeMode[String(mode).toUpperCase()]
        )],
        ["bit depth", async () => {await convertBitDepth(doc, bits)}],
    ];

    // validate arguments
    [resolution, mode, bits].forEach((arg, idx) => { 
            steps[idx].push((arg !== null && arg !== undefined));
        }
    )

    const errors = [];
    await execAsModal(async () => {
        for (const [setting, apply, valid] of steps) {
            if (!valid)
                continue;
            
            try {
                await apply();
            } catch (err) {
                errors.push(`Failed to change ${setting}: ${err.message}`);
            }
        }
    }, "Set Document Settings");

    return JSON.stringify(errors.length ? {success: false, errors} : {success: true});
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
            visible: desc.visible,
            blend_mode: desc.mode?._value
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
                visible: bg.visible,
                blend_mode: String(bg.blendMode)
            });
        }
    } catch (e) {
        // no background layer
    }

    return JSON.stringify(layers);
}

/**
 * Blend mode of a layer.
 *
 * @param {number} layer_id Id of the layer.
 * @returns {Promise<string>} Mode id such as "normal" or "multiply".
 */
async function getLayerBlendMode(layer_id) {
    const [descriptor] = await batchPlay(
        [{
            _obj: "get",
            _target: [{ _ref: "layer", _id: layer_id }]
        }],
        { synchronousExecution: true }
    );
    return descriptor.mode?._value;
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
    return (layer.kind == constants.LayerKind.GROUP);
}

async function getSelectedLayers() {
    if (app.documents.length === 0) return "[]";
    try{
    const selected = app.activeDocument.activeLayers;
    const result = selected.map(layer => ({
        id: layer.id,
        name: layer.name,
        group: layer.kind == constants.LayerKind.GROUP,
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
    while (current && current.kind === constants.LayerKind.GROUP) {
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

    const existing = JSON.parse(await getLayers());
    const existingIds = new Set(existing.map(l => l.id));

    const refs = selectedLayers
        .filter(id => existingIds.has(Number(id)))       // ✅ cast to number
        .map(id => ({ _ref: "layer", _id: Number(id) })); // ✅ cast to number

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


async function createGroup(name) {
    let group;
    await execAsModal(async () => {
        group = await app.activeDocument.createLayerGroup({ name });
        // make sure that active layer is new group, replicating CEP behavior
        app.activeDocument.activeLayers = [group];
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
        // mimick CEP behavior
        await batchPlay(
            [{
                _obj: "select",
                _target: [{ _ref: "layer", _id: group.id }],
                makeVisible: false,
                _options: { dialogOptions: "dontDisplay" }
            }],
            { synchronousExecution: true }
        );
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

        // Preserve parent
        const children = layerSet.layers.slice();

        // Move each child out to the document root
        for (const child of children) {
            await child.move(app.activeDocument, constants.ElementPlacement.PLACEBEFORE);
        }

        // Delete empty group
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

    let old_selected;
    try {
        old_selected = JSON.parse(await getSelectedLayers()); // should be a list of ints
    } catch {
        old_selected = [layer_id];
    }

    await selectLayers([layer_id]);

    const result = await execAsModal(async () => {
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

    await selectLayers(old_selected);
    return result;
}

/**
 * Smart Object layers of the active document whose link is broken, with their
 * full paths.
 *
 * @returns {Promise<{layer: object, path: string}[]>} Broken layers in
 *     document order, path like "GROUP/SUBGROUP/LAYER".
 */
async function getBrokenSmartObjectLinks() {
    const smartObjects = [];
    const walk = (layers, parents) => {
        for (const layer of layers) {
            if (layer.kind === constants.LayerKind.GROUP) {
                walk(layer.layers, [...parents, layer.name]);
            } else if (layer.kind === constants.LayerKind.SMARTOBJECT) {
                smartObjects.push({
                    layer, path: [...parents, layer.name].join("/")
                });
            }
        }
    };
    walk(app.activeDocument.layers, []);

    const descriptors = await batchPlay(
        smartObjects.map(({layer}) => ({
            _obj: "get",
            _target: [{ _ref: "layer", _id: layer.id }]
        })),
        { synchronousExecution: true }
    );
    return smartObjects.filter(
        (_, index) => descriptors[index]?.smartObject?.linkMissing
    );
}

/**
 * Rasterize every given Smart Object layer, then convert it back into an
 * embedded Smart Object, which drops the stale link.
 *
 * @param {{layer: object, path: string}[]} smartObjects Layers to repair.
 * @returns {Promise<string>} JSON array of the paths of the repaired layers.
 */
async function rasterizeSmartObject(smartObjects) {
    const fixed = [];
    await execAsModal(async () => {
        for (const {layer, path} of smartObjects) {
            await batchPlay([{
                _obj: "select",
                _target: [{ _ref: "layer", _id: layer.id }],
                makeVisible: false,
                _options: { dialogOptions: "dontDisplay" }
            }], { synchronousExecution: true });

            await layer.rasterize(constants.RasterizeType.ENTIRELAYER);

            await batchPlay([{
                _obj: "newPlacedLayer",
                _options: { dialogOptions: "dontDisplay" }
            }], { synchronousExecution: true });

            fixed.push(path);
        }
    }, "Rasterize Smart Objects");
    return JSON.stringify(fixed);
}

/**
 * Convert the specified document to a bit depth without changing its color mode.
 *
 * This is an Action Manager operation because the UXP DOM does not provide a
 * consistently available writable `bitsPerChannel` property.
 */
async function convertBitDepth(document, depth) {
    await batchPlay(
        [{
            _obj: "convertMode",
            _target: [
                { _ref: "document", _id: document.id }
            ],
            depth,
            flatten: false,
            _isCommand: true
        }],
        {
            synchronousExecution: true,
            modalBehavior: "execute"
        }
    );
}

/**
 * Save a document as OpenEXR.
 *   As: EXRf
 *     BtDp: 32
 *     Cmpr: 1
 *     AChn: 1
 * Must be called inside executeAsModal().
 *
 * @param {Photoshop.Document} doc
 * @param {string} outputPath Native absolute output path.
 * @param {boolean} [asCopy=false]
 * @returns {Promise<string>}
 */
async function saveEXR(doc, outputPath, asCopy = false) {
    const outputFile = await getOutputFileEntry(outputPath);
    const sessionToken = localFileSystem.createSessionToken(outputFile);

    await batchPlay([{
        _obj: "save",
        _target: [
            { _ref: "document", _id: doc.id }
        ],
        as: {
            _obj: "EXRf",
            "$BtDp": 32,
            "$Cmpr": 1,
            "$AChn": 1
        },
        in: {
            _path: sessionToken,
            _kind: "local"
        },
        copy: !!asCopy,
        lowerCase: true,
        _options: {
            dialogOptions: "dontDisplay"
        }
    }], {
        synchronousExecution: true,
        modalBehavior: "execute"
    });

    return outputPath;
}

/**
 * Save a document as PSB.
 * Must be called inside executeAsModal().
 *
 * @param {Photoshop.Document} doc
 * @param {string} outputPath Native absolute output path.
 * @param {boolean} [asCopy=false]
 * @returns {Promise<string>}
 */
async function savePSB(doc, outputPath, asCopy = false) {
    const outputFile = await getOutputFileEntry(outputPath);

    await doc.saveAs.psb(outputFile, {
        embedColorProfile: true,
        alphaChannels: true,
        layers: true,
        annotations: true,
        spotColors: true,
        maximizeCompatibility: true
    }, !!asCopy);

    return outputPath;
}

/**
 * Save as PSD, with PSB fallback for documents too large for PSD.
 *
 * Must run inside executeAsModal().
 *
 * @returns {Promise<string>} The actual output path: PSD or PSB.
 */
async function saveSmart(outputPath, doc, asCopy = false) {
    if (!/\.psd$/i.test(outputPath)) {
        throw new Error(
            `saveSmart requires a .psd output path, got: ${outputPath}`
        );
    }

    const psbPath = outputPath.replace(/\.psd$/i, ".psb");

    // UXP document dimensions are numbers in pixels.
    if (
        doc.width > PSD_MAX_DIMENSION ||
        doc.height > PSD_MAX_DIMENSION
    ) {
        return savePSB(doc, psbPath, asCopy);
    }

    const {
        entry: psdEntry,
        existedBefore
    } = await getOutputFileEntry(outputPath);

    const metadataBefore = await getFileMetadata(psdEntry);

    try {
        await doc.saveAs.psd(psdEntry, {
            embedColorProfile: true,
            alphaChannels: true,
            layers: true,
            annotations: true,
            spotColors: true,
            maximizeCompatibility: true
        }, !!asCopy);
    } catch (psdError) {
        // Do not turn an explicit user cancellation into a PSB save.
        if (isSaveCancelled(psdError)) {
            throw psdError;
        }

        await removePartialSave(psdEntry, existedBefore);

        try {
            return await savePSB(doc, psbPath, asCopy);
        } catch (psbError) {
            console.error("PSD and PSB save both failed:", {
                psdError,
                psbError
            });

            // Preserve the original PSD error
            throw psdError;
        }
    }

    /*
     * Preserve "success but nothing changed" fallback behavior.
     */
    const metadataAfter = await getFileMetadata(psdEntry);

    if (!fileWasWritten(metadataBefore, metadataAfter, existedBefore)) {
        return savePSB(doc, psbPath, asCopy);
    }

    return outputPath;
}

/**
 * Save/export the active document.
 *
 * Supported formats:
 *   jpg, jpeg, png, tga, exr, psd, psb, tif, tiff
 *
 * @param {string} outputPath Absolute native output path.
 * @param {string} ext Output extension, with or without leading dot.
 * @param {boolean} asCopy Photoshop "save as copy" option.
 * @returns {Promise<string>} Actual path written. PSD may return a .psb path.
 */
async function saveAs(outputPath, ext, asCopy = false) {
    if (app.documents.length === 0) {
        throw new Error("saveAs: no document is open");
    }

    const format = String(ext || "")
        .trim()
        .replace(/^\./, "")
        .toLowerCase();

    return execAsModal(async () => {
        let doc = app.activeDocument;
        let isTemporaryDocument = false;

        try {
            const is8Bit = doc.bitsPerChannel === constants.BitsPerChannelType.EIGHT;

            const is16Bit = doc.bitsPerChannel === constants.BitsPerChannelType.SIXTEEN;

            const is32Bit = doc.bitsPerChannel === constants.BitsPerChannelType.THIRTYTWO;
            /*
             * Preserve 16-bit PNG: only 32-bit source documents are converted
             * for PNG. JPG and TGA are likewise made 8-bit from 32-bit input.
             */
            if (
                is32Bit &&
                ["jpg", "jpeg", "png", "tga"].includes(format)
            ) {
                doc = await doc.duplicate();
                isTemporaryDocument = true;

                await convertBitDepth(doc, 8);
            }
            // EXR requires a 32-bit source document. 
            if (
                format === "exr" &&
                (is8Bit || is16Bit)
            ) {
                doc = await doc.duplicate();
                isTemporaryDocument = true;

                await convertBitDepth(doc, 32);
            }

            switch (format) {
                case "jpg":
                case "jpeg": {
                    const { entry } = await getOutputFileEntry(outputPath);

                    await doc.saveAs.jpg(entry, {
                        quality: 12,
                        embedColorProfile: true,
                        formatOptions: "progressive",
                        scans: 5,
                        matte: "noMatte"
                    }, !!asCopy);

                    return outputPath;
                }

                case "png": {
                    const { entry } = await getOutputFileEntry(outputPath);

                    await doc.saveAs.png(entry, {
                        compression: 6,
                        interlaced: true
                    }, !!asCopy);

                    return outputPath;
                }

                case "tif":
                case "tiff": {
                    const { entry } = await getOutputFileEntry(outputPath);

                    await doc.saveAs.tiff(entry, {
                        alphaChannels: true,
                        transparency: true,
                        imageCompression: "TIFFLZW",
                        layers: false
                    }, !!asCopy);

                    return outputPath;
                }

                case "tga": {
                    const { entry } = await getOutputFileEntry(outputPath);
                    const sessionToken =
                        localFileSystem.createSessionToken(entry);

                    await batchPlay([{
                        _obj: "save",
                        _target: [
                            { _ref: "document", _id: doc.id }
                        ],
                        as: {
                            _obj: "targaFormat",
                            depth: 32,
                            alphaChannels: true,
                            rleCompression: true
                        },
                        in: {
                            _path: sessionToken,
                            _kind: "local"
                        },
                        copy: !!asCopy,
                        lowerCase: true,
                        _options: {
                            dialogOptions: "dontDisplay"
                        }
                    }], {
                        synchronousExecution: true,
                        modalBehavior: "execute"
                    });

                    return outputPath;
                }

                case "exr":
                    return saveEXR(doc, outputPath, asCopy);

                case "psd":
                    // preserve saveSmart from CEP
                    return saveSmart(outputPath, doc, asCopy);

                case "psb":
                    return savePSB(doc, outputPath, asCopy);

                default:
                    throw new Error(
                        `saveAs: unsupported extension '${ext}'`
                    );
            }
        } finally {
            if (isTemporaryDocument) {
                await doc.closeWithoutSaving();
            }
        }
    }, `Save As ${format.toUpperCase()}`);
}

/**
 * Create a new blank RGB, 8 bit, white document and make it active.
 *
 * @param {string} name Document name.
 * @param {number} width Width in pixels.
 * @param {number} height Height in pixels.
 * @param {number} resolution Resolution in dpi.
 * @returns {Promise<number>} Id of the new document.
 */
async function createDocument(name, width, height, resolution) {
    let doc;
    await execAsModal(async () => {
        doc = await app.createDocument({
            name,
            width,
            height,
            resolution,
            mode: constants.NewDocumentMode.RGB,
            fill: constants.DocumentFill.WHITE,
            depth: 8,
        });
    }, "Create Document");
    return doc.id;
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
 * Save a JPEG review image.
 *
 * @param {string} imagePath Absolute native output path.
 * @param {number} maxDimension Maximum width or height in pixels.
 *                              Use 0 or a negative value to disable resizing.
 * @returns {Promise<string>} The saved image path.
 */
async function saveReviewJpg(imagePath, maxDimension) {
    if (app.documents.length === 0) {
        throw new Error("saveReviewJpg: no document is open");
    }

    const maxSize = Number(maxDimension);
    const url = "file:" + imagePath.replace(/\\/g, "/");

    await execAsModal(async () => {
        const outputFile =
            await uxp_storage.localFileSystem.createEntryWithUrl(url, {
                overwrite: true
            });

        let duplicate = null;

        try {
            duplicate = await app.activeDocument.duplicate();

            // JPEG requires 8 bits/channel. Convert only the duplicate, so
            // the original 16-bit or 32-bit source remains untouched.
            if (
                duplicate.bitsPerChannel !==
                constants.BitsPerChannelType.EIGHT
            ) {
                await convertBitDepth(duplicate, 8);
            }

            // In UXP, Document.width and Document.height are pixels.
            const width = duplicate.width;
            const height = duplicate.height;
            const longestSide = Math.max(width, height);

            if (
                Number.isFinite(maxSize) &&
                maxSize > 0 &&
                longestSide > maxSize
            ) {
                const scale = maxSize / longestSide;

                // Preserve aspect ratio. Both values are provided explicitly,
                // unlike CEP's UnitValue-based resizeImage call.
                const newWidth = Math.max(1, Math.round(width * scale));
                const newHeight = Math.max(1, Math.round(height * scale));

                await duplicate.resizeImage(
                    newWidth,
                    newHeight,
                    undefined, // Keep current resolution.
                    constants.ResampleMethod.BICUBIC
                );
            }

            await duplicate.saveAs.jpg(outputFile, {
                quality: 12,
                embedColorProfile: true,
                formatOptions: "progressive",
                scans: 5,
                matte: "noMatte"
            }, true); // Always save as a copy, as in the CEP version.
        } finally {
            // Ensure that the temporary document is removed even if conversion,
            // resize, or saving fails.
            if (duplicate) {
                await duplicate.closeWithoutSaving();
            }
        }
    }, "Save Review JPEG");

    return imagePath;
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
    getDocumentSize,
    getDocumentSettings,
    setDocumentSettings,
    getLayerTypeWithName,
    getLayers,
    getLayerBlendMode,
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
    getBrokenSmartObjectLinks,
    rasterizeSmartObject,
    saveAs,
    saveReviewJpg,
    createDocument,
    duplicateDocument,
    closeDocument,
    getExtensionVersion,
    closeApp,
};
