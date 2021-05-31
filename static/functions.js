// funtion that opens the side menu bar once a button is clicked in mobile devices
function menuOpen() {
    if(document.getElementById("menu-bar").style.width != "0px"){
        menuClose();
    } else {
        document.getElementById("menu-bar").style.width = "200px";
        // change the color slightly
        document.body.style.backgroundColor = "#0e304cf9";
    }
}

// funtion that closes the side menu bar once a button is clicked again in mobile devices
function menuClose() {
    document.getElementById("menu-bar").style.width = "0px";
    document.body.style.backgroundColor = "#0e304cf7";
}