const get_RPC = require("./client_RPC").get_RPC
const setup_rpc = require("./client_RPC").setup_rpc

const WS_URL = "ws://localhost:8101/ws/";

let RPC = null;

document.addEventListener("DOMContentLoaded", async () => {
  // Ensure that RPC is ready.
  await setup_rpc(WS_URL);
  RPC = await get_RPC();
  console.log("Got RPC!")
  async function bind(id, route) {
    const el = document.getElementById(id);
    if (!el) return;

    el.addEventListener("click", async () => {
      try {
        const result = await RPC.call(route);
        console.log(`Success: ${route}`, result);
      } catch (err) {
        console.error(`Failed: ${route}`, err);
      }
    });
  }

  // Bind buttons.
  await bind("workfiles-button", "Photoshop.workfiles_route");
  await bind("loader-button", "Photoshop.loader_route");
  await bind("publish-button", "Photoshop.publish_route");
  await bind("sceneinventory-button", "Photoshop.sceneinventory_route");
  await bind("experimental-button", "Photoshop.experimental_tools_route");
});