function startTime() {
  let now = new Date();
  document.getElementById('currentTime').innerHTML =
      `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  setTimeout(startTime, 500);
}

function pad(i) {
    if (i < 10) {
        i = `0${i}`
    }
    return i;
}