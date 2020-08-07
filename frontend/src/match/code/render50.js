function render50(str_a, str_b, name_a="a.txt", name_b="b.txt") {
    // form data
    let formData = new FormData();
    formData.set("size", "letter landscape")
    formData.append("file", new File([str_a], name_a, {type: "text/plain"}), name_a);
    formData.append("file", new File([str_b], name_b, {type: "text/plain"}), name_b);
    formData.set("y", "");

    // POST request
    fetch("https://render.cs50.io/", {
        method: "POST",
        body: formData,
        mode: "cors"
    }).then((response) => {
        if (response.ok) {
            return response.blob();
        }
    }).then((response) => {
        // create data URL to download from
        let anchor = document.createElement("a");
        anchor.href = URL.createObjectURL(response);
        anchor.setAttribute("download", "output");
        anchor.style.display = "none";
        document.body.appendChild(anchor);

        // wait, then click to download
        setTimeout(function() {
            anchor.click();
            document.body.removeChild(anchor);
        }, 66);
    });
}

export default render50;
