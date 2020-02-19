/*
 * Copyright 2019 Simon Zigelli
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

function timer_ws(congregation_ws, reload, showWarning) {

    let stopwatch = document.getElementById('stopwatch');
    let talk = document.getElementById('talk');
    let talkNumber = document.getElementById('talk_number');
    if (talk !== null)
        talk.style.display = 'none';
    let remaining = $('#remaining');
    let start = null;
    let value = null;
    let timeout = null;
    let sent = false;

    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/timer/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    mySocket.onopen = function (_) {
        console.log('Timer WebSocket CONNECT successful');
    };

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let message = data['timer'];
        if (message === undefined)
            return;
        let timer = message['timer'];
        if (timer === undefined)
            return;

        if (timer === 'start') {
            if (talk !== null)
                talk.style.display = 'block';
            if (talkNumber !== null)
                talkNumber.innerText = message['talk'];
            start = moment(message['start']);
            value = message['value'];
            sent = false;
            timeout = setTimeout(runTimer, 500);
        } else if (timer === 'stop') {
            start = null;
            value = null;
            if (talk !== null)
                talk.style.display = 'none';
            if (reload) {
                location.reload();
            } else {
                mySocket.send(JSON.stringify({
                    'alert': 'stop',
                }));
            }
            sent = false;
            clearTimeout(timeout);
        } else {
            console.log(message);
        }
    };

    mySocket.onclose = function (_) {
        console.error('Timer Socket closed unexpectedly');
    };

    function runTimer() {
        if (stopwatch === null || remaining == null || value === null || start === null)
            return;
        let diff = (new Date).getTime() - start;
        stopwatch.innerText = millisecondsToTime(diff);
        let span = (value['h'] * 60000000 + value['m'] * 60000 + value['s'] * 1000) - diff;
        if (span >= 0) {
            remaining.text(millisecondsToTime(span));
            remaining.removeClass('fg-red');
            remaining.removeClass('timesUp');
            remaining.addClass('fg-white');
            sent = false;
        } else {
            if (mySocket !== null && !sent && !reload && showWarning) {
                mySocket.send(JSON.stringify({
                    'alert': 'time',
                }));
                sent = true;
            }
            remaining.text('-' + millisecondsToTime(span));
            remaining.removeClass('fg-white');
            remaining.addClass('timesUp');
            remaining.addClass('fg-red');
        }
        timeout = setTimeout(runTimer, 500)
    }

    function millisecondsToTime(ms) {
        if (ms < 0)
            ms *= -1;
        const seconds = Math.floor((ms / 1000) % 60);
        const minutes = Math.floor((ms / 1000 / 60) % 60);
        const hours = Math.floor(ms / 1000 / 60 / 60);

        return [
            pad(hours),
            pad(minutes),
            pad(seconds),
        ].join(':');
    }

    function pad(i) {
        if (i < 10) {
            i = `0${i}`
        }
        return i;
    }
}