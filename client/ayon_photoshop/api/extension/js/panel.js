/*global $, window, RPC*/

/**
 * Bind every button carrying a data-route to its RPC route.
 *
 * A route call blocks with no timeout and retries three times on a
 * dropped socket, so a click can take ~18s. The button is disabled
 * and relabelled meanwhile, otherwise artists click again and fire
 * the route twice. Only the label span is rewritten, never the
 * button itself, or the icon would be wiped out with it.
 */
$(function () {
    var $status = $("#status");
    var $connection = $("#connection");
    var $connectionText = $("#connection-text");
    var $reconnect = $("#reconnect-button");
    var DISCONNECTED = "Not connected to Photoshop.";

    function setStatus(message, isError) {
        $status.text(message || "").toggleClass("is-error", !!isError);
    }

    // A route that raises in Python rejects with {type, message},
    // while wsrpc.js rejects with a plain string.
    function errorText(error) {
        if (error && typeof error === "object") {
            return error.message || error.type || "Unknown error";
        }
        return String(error);
    }

    /**
     * wsrpc reconnects on its own every 5s, the interval client.js
     * passes to the WSRPC constructor. None of this replaces that; it
     * only makes the state visible and lets the artist skip the wait.
     */
    function rpcState() {
        return window.RPC && RPC.state ? RPC.state() : "CLOSED";
    }

    function showConnection(text, canRetry) {
        $connectionText.text(text);
        $reconnect.prop("disabled", !canRetry);
        $connection.prop("hidden", false);
    }

    $reconnect.on("click", function () {
        if (rpcState() !== "CLOSED") {
            return;
        }
        showConnection("Reconnecting...", false);
        try {
            RPC.connect();
        } catch (error) {
            showConnection("Reconnect failed: " + error, true);
            return;
        }
        // connect() replaces the socket outright and wsrpc may have
        // its own retry already pending, so stay disabled past one
        // reconnect cycle rather than stacking a second socket
        window.setTimeout(function () {
            if (rpcState() !== "OPEN") {
                showConnection(DISCONNECTED, true);
            }
        }, 6000);
    });

    // client.js builds RPC asynchronously, so wait for it to exist
    var wiring = window.setInterval(function () {
        if (!window.RPC || !RPC.addEventListener) {
            return;
        }
        window.clearInterval(wiring);

        RPC.addEventListener("onconnect", function () {
            $connection.prop("hidden", true);
        });
        RPC.addEventListener("onclose", function () {
            showConnection(DISCONNECTED, true);
        });
        RPC.addEventListener("onerror", function () {
            showConnection(DISCONNECTED, true);
        });

        // CONNECTING is the normal state on open, do not alarm
        if (rpcState() === "CLOSED") {
            showConnection(DISCONNECTED, true);
        }
    }, 250);

    $("#content button[data-route]").each(function () {
        var $button = $(this);
        var $label = $button.find(".btn-label");
        var label = $label.text();

        // labels elide in a narrow panel, so keep the full text
        $button.attr("title", label);

        $button.on("click", function () {
            if ($button.prop("disabled")) {
                return;
            }
            // without this the call burns ~18s of retries first
            if (rpcState() !== "OPEN") {
                setStatus(DISCONNECTED, true);
                return;
            }
            setStatus("");
            $button.prop("disabled", true);
            $label.text($button.data("busy") || "Working...");

            function done() {
                $button.prop("disabled", false);
                $label.text(label);
            }

            RPC.call("Photoshop." + $button.data("route")).then(
                done,
                function (error) {
                    done();
                    setStatus(errorText(error), true);
                }
            );
        });
    });
});

/**
 * Make the button groups collapsible and remember each one's state.
 *
 * Groups are <details data-group="..."> elements, so folding itself is
 * native. This only restores the artist's last choice per group from
 * localStorage. Storage can be unavailable or full; the panel then
 * still folds, it just forgets on reload.
 */
$(function () {
    var STORAGE_PREFIX = "ayon.panel.group.";

    $("#content details.group[data-group]").each(function () {
        var details = this;
        var storageKey = STORAGE_PREFIX + $(details).data("group");

        try {
            if (window.localStorage.getItem(storageKey) === "closed") {
                details.open = false;
            }
        } catch (error) {
            // unreadable storage, keep the default open state
        }

        details.addEventListener("toggle", function () {
            try {
                window.localStorage.setItem(
                    storageKey, details.open ? "open" : "closed"
                );
            } catch (error) {
                // not saved, the fold still works for this session
            }
        });
    });

    // no :focus-visible in Chrome 61, so keep mouse clicks from
    // leaving the keyboard focus ring on the header
    $("#content details.group > summary").on("mousedown", function (event) {
        event.preventDefault();
    });
});
