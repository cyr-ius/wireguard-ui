// TOTP
function totp_countdown() {
  setInterval(function () {
    var bar = document.getElementById("totp_bar");
    var d = new Date(),
      s = d.getSeconds();
    if (s <= 30) {
      pr = Math.floor((s / 30) * 100);
    } else {
      pr = Math.floor(((s - 30) / 30) * 100);
    }
    if (pr > 80) {
      bar.style.backgroundColor = "red";
    } else {
      bar.style.backgroundColor = "#979797";
    }
    bar.style.width = pr + "%";
  }, 1000);
}
