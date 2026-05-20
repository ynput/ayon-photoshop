const api = require("./client_api");
const WSRPC = require("./lib/wsrpc");

let RPC = null;

async function get_RPC() {
    return RPC;
}

async function setup_rpc(websocket_url) {
    if (websocket_url)
        console.log("websocket_url", websocket_url);
    
    const default_url = 'ws://localhost:8101/ws/';
    
    if  (websocket_url == ''){
         websocket_url = default_url;
    }
    
    RPC = new WSRPC(websocket_url); // spin connection
    console.log("connecting to:", websocket_url, RPC);
    try{
    RPC.connect();
    } catch (err) {
      console.log(err)
    }
    // await RPC.onEvent("onconnect");
    console.log("Connected!");

    RPC.addRoute('Photoshop.open', async (data) => {
            console.log('Server called client route "open":', data.path);
            const result = await api.fileOpen(data.path);
            console.log("open:", result);
            return result
        }
    )

    RPC.addRoute('Photoshop.read', async (data) => {
            console.log('Server called client route "read":', data);
            const result = await api.getHeadline();
            console.log("read:", result.replace("\n",""));
            return result
        }
    );

    RPC.addRoute('Photoshop.get_layers', async (data) => {
            console.log('Server called client route "get_layers":', data);
            const result = await api.getLayers();
            console.log("getLayers:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.set_visible', async (data) => {
            console.log('Server called client route "set_visible":', data);
            const result = await api.setVisible(data.layer_id, data.visibility);
            console.log("setVisible:", result);
            return result;
        }
    );


    RPC.addRoute('Photoshop.get_active_document_name', async (data) => {
            console.log('Server called client route "get_active_document_name":', data);
            const result = await api.getActiveDocumentName();
            console.log("getActiveDocumentName:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.get_active_document_full_name', async (data) => {
            console.log('Server called client route "get_active_document_full_name":', data);
            const result = await api.getActiveDocumentFullName();
            console.log("getActiveDocumentFullName:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.save', async (data) => {
            console.log('Server called client route "save":', data);
            const result = await api.save();
            console.log("save:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.get_selected_layers', async (data) => {
            console.log('Server called client route "get_selected_layers":', data);
            const result = await api.getSelectedLayers();
            console.log("getSelectedLayers:", result);
            return result; // client expects JSON string.
        }
    );

    RPC.addRoute('Photoshop.create_group', async (data) => {
            console.log('Server called client route "create_group":', data);
            const result = await api.createGroup(data.name);
            console.log("createGroup:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.group_selected_layers', async (data) => {
            console.log('Server called client route "group_selected_layers":', data);
            const result = await api.groupSelectedLayers(null, data.name);
            console.log("groupSelectedLayers:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.merge_all_layersets', async (data) => {
            console.log('Server called client route "merge_all_layersets":', data);
            const result = await api.mergeAllLayerSets(data.parent_set);
            console.log("mergeAllLayerSets:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.dissolve_layerset', async (data) => {
            console.log('Server called client route "dissolve_layerset":', data);
            const result = await api.dissolveLayerSet(data.layerset_id);
            console.log("dissolveLayerSet:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.import_smart_object', async (data) => {
            console.log('Server called client route "import_smart_object":', data);
            const result = await api.importSmartObject(data.path, data.name, data.as_reference);
            console.log("importSmartObject:", result);
            return result
        }
    );

    RPC.addRoute('Photoshop.replace_smart_object', async (data) => {
            console.log('Server called client route "replace_smart_object":', data);
            const result = await api.replaceSmartObjects(data.layer_id, data.path, data.name);
            console.log("replaceSmartObjects:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.delete_layer', async (data) => {
            console.log('Server called client route "delete_layer":', data);
            const result = await api.deleteLayer(data.layer_id);
            console.log("deleteLayer:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.rename_layer', async (data) => {
            console.log('Server called client route "rename_layer":', data);
            const result = await api.renameLayer(data.layer_id, data.name);
            console.log("renameLayer:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.select_layers', async (data) => {
            console.log('Server called client route "select_layers":', data);
            const result = await api.selectLayers(data.layers);
            console.log("selectLayers:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.is_saved', async (data) => {
            console.log('Server called client route "is_saved":', data);
            const result = await api.isSaved();
            console.log("isSaved:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.saveAs', async (data) => {
            console.log('Server called client route "saveAs":', data);
            const result = await api.saveAs(data.image_path, data.ext, data.as_copy);
            console.log("saveAs:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.duplicate_document', async (data) => {
            console.log('Server called client route "duplicate_document":', data);
            const result = await api.duplicateDocument(data.newName);
            console.log("duplicateDocument:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.close_document', async (data) => {
            console.log('Server called client route "close_document":', data);
            const result = await api.closeDocument(data.id);
            console.log("closed:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.revert_to_previous', async (data) => {
            console.log('Server called client route "revert_to_previous":', data);
            const result = await api.revertToPrevious();
            console.log("revertToPrevious:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.imprint', async (data) => {
            console.log('Server called client route "imprint":', data);
            // preserve newlines
            const result = await api.imprint(data.payload);
            console.log("imprint:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.get_extension_version', async (data) => {
            console.log('Server called client route "get_extension_version":', data);
            const result = await api.getExtensionVersion();
            console.log("getExtensionVersion:", result);
            return result;
        }
    );

    RPC.addRoute('Photoshop.close', async (data) => {
            console.log('Server called client route "close":', data);
            const result = await api.closeApp();
            // probably dead before this
            return result;
        }
    );

    // this route appears to not exist anymore.
    RPC.call('Photoshop.ping').then(function (data) {
          console.log('Result for calling server route "ping": ', data);
          return "pong";
      }, function (error) {
          console.log(error);
      });

}

module.exports = {
    get_RPC,
    setup_rpc
};