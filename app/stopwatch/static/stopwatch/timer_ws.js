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

function timer_ws(congregation_ws, reload, resetOnStop = false) {

    let stopwatch = document.getElementById('stopwatch');
    let talk = document.getElementById('talk');
    let talkNumber = document.getElementById('talk_number');
    if (talk !== null)
        talk.style.display = 'none';
    let remaining = $('#remaining');

    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/central_timer/${congregation_ws}/`,
    let mySocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/central_timer/' + congregation_ws + '/',
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    mySocket.onopen = function (_) {
        console.log('Timer WebSocket CONNECT successful');
    };

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let message = data['timer'];
        if (message === undefined)
            return;

        if (message['timer'] === 'started') {
            if (talk !== null)
                talk.style.display = 'block';
            if (talkNumber !== null)
                talkNumber.innerText = message['name'];
        } else if (message['timer'] === 'stopped') {
            if (talk !== null)
                talk.style.display = 'none';
            if (reload) {
                location.reload();
            } else {
                mySocket.send(JSON.stringify({
                    'alert': 'stop',
                }));
            }
            if (resetOnStop) {
                remaining.text(millisecondsToTime(0));
                stopwatch.innerText = millisecondsToTime(0);
            }
        } else if ('sync' in message) {
            if (talk !== null)
                talk.style.display = 'block';
            if (talkNumber !== null)
                talkNumber.innerText = message['name'];
            let value = message['sync'];
            let duration = message['duration'];
            let span = (parseInt(value['h']) * 3600000 + parseInt(value['m']) * 60000 + parseInt(value['s']) * 1000);
            let span_duration = (parseInt(duration['h']) * 3600000 + parseInt(duration['m']) * 60000 + parseInt(duration['s']) * 1000);
            let rem = span_duration - span;
            if (stopwatch !== null)
                stopwatch.innerText = millisecondsToTime(span);
            if (remaining !== undefined)
                if (rem >= 0) {
                    remaining.text(millisecondsToTime(rem));
                    remaining.removeClass('fg-red');
                    remaining.removeClass('timesUp');
                    remaining.addClass('fg-white');
                } else {
                    remaining.text('-' + millisecondsToTime(rem));
                    remaining.removeClass('fg-white');
                    remaining.addClass('timesUp');
                    remaining.addClass('fg-red');
                }
        } else {
            console.log(message);
        }
    };

    mySocket.onclose = function (_) {
        console.error('Timer Socket closed unexpectedly');
    };

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
            // i = `0${i}`
            i = '0' + i
        }
        return i;
    }
}