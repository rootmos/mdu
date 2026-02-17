(function() {
    console.debug("hello");

    const stockholm = "740000001";
    const eskilstuna = "740000170";
    const base_url = "https://biljett.malartag.se/search";

    const qs = new URLSearchParams(window.location.search);
    const dry_run = qs.has("dry_run");

    let dir = window.location.hash.substr(1);
    var f, t;
    switch (qs.get("q") || "se") {
        case "e":
        case "es":
            f = eskilstuna; t = stockholm;
            break;
        case "s":
        case "se":
            f = stockholm; t = eskilstuna;
            break;
    }

    let now = Date.now();
    let ts = new Intl.DateTimeFormat("se-SE", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
    }).format(now).replace(/[- :]/g, "");

    let url = `${base_url}/${f}/${t}/${ts}/0/0`;
    console.debug(url);

    let a = document.createElement("a");
    a.href = url;
    a.innerText = url;
    document.body.appendChild(a);

    if (!dry_run) {
        window.location.assign(url);
    }
})();
