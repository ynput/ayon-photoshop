var csInterface = new CSInterface();

function initPanel() {
    document.getElementById('publishBtn').addEventListener('click', function() {
        csInterface.evalScript('publishWorkfile()', function(result) {
            document.getElementById('status').innerText = result;
        });
    });
}

document.addEventListener('DOMContentLoaded', initPanel);