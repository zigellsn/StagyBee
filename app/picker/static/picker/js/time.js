function startTime() {
    let now = new Date();
    let element = document.getElementById('currentTime');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
    element = document.getElementById('currentHour');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}`;
        element.innerHTML = pad(now.getHours());
    element = document.getElementById('currentMinute');
    if (element != null)
        // element.innerHTML = `${pad(now.getMinutes())}`;
        element.innerHTML = pad(now.getMinutes());
    element = document.getElementById('currentSecond');
    if (element != null)
        // element.innerHTML = `${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.getSeconds());
    setTimeout(startTime, 500);
}

function pad(i) {
    if (i < 10) {
        // i = `0${i}`
        i = '0' + i
    }
    return i;
}