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

async function download(format) {
    document.getElementById("loading-dialog").showModal();
    try {
        const response = await fetch(
            `http://raspberrypi.local/api/v1/race_data/all/latest/${format}`,
            {
                method: "GET"
            }
        );
            
        if (response.redirected) {
            window.open(response.url, '_blank');
            document.getElementById("loading-dialog").close();
        } else {
            document.getElementById("loading-dialog-label").innerText = `HTTP Error${response.status ? ` ${response.status}` : ""}. Check console`;
            console.log(response);
        }
    } catch (err) {
        document.getElementById("loading-dialog-label").innerText = "Fetch Error! Check console";
        console.log(err);
    }
}

setSessionHash();