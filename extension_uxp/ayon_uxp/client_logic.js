/**
 * Helpers of the AYON UXP plugin that don't need Photoshop.
 */

/**
 * Shape an error so that the server receives its message.
 *
 * The server reads the error payload as a dictionary: a thrown Error
 * serialises to "{}" and a plain string makes the server's own error
 * handling fail. Both are sent as a {type, message} object instead.
 *
 * @param {*} error Whatever was thrown.
 * @returns {{type: string, message: string}}
 */
function toRpcError(error) {
    if (error && typeof error === "object" && "message" in error) {
        return {type: String(error.name || "Error"), message: String(error.message)};
    }
    return {type: "Error", message: String(error)};
}

module.exports = {
    toRpcError,
};
