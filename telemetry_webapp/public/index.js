async function setSessionHash() {
    const sessionHashSpan = document.getElementById("session_hash_span");
    const sessionHash = await fetch(
        `http://raspberrypi.local/api/v1/session_hash/latest`,
        {
            method: "GET",
            headers: {
                Accept: "application/json"
            }
        }
    ).then((r) => r.json()).then((r) => r.session_hash);
    sessionHashSpan.innerText = `Session hash: ${sessionHash}`;
};

async function downloadCsv() {
    document.getElementById("loading-dialog").showModal();
    try {
        const responseUrl = await fetch(
            `http://raspberrypi.local/api/v1/race_data/all/latest`,
            {
                method: "GET"
            }
        ).then((r) => r.redirected ? r.url : "");
    
        if (responseUrl !== "") {
            window.open(responseUrl, '_blank');
        }
        document.getElementById("loading-dialog").close();
    } catch (err) {
        document.getElementById("loading-dialog-label").innerText = "Error! Check console";
        console.log(err);
    }
}

setSessionHash();