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
    let line = undefined;
    if (talk !== null)
        talk.style.display = 'none';
    let remaining = $('#remaining');

    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let centralTimerSocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/central_timer/${congregation_ws}/`,
    let centralTimerSocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/central_timer/' + congregation_ws + '/',
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    centralTimerSocket.onopen = function (_) {
        console.log('Timer WebSocket CONNECT successful');
    };

    centralTimerSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let message = data['timer'];
        if (message === undefined)
            return;

        if (message['mode'] === 'started') {
            if (talk !== null)
                talk.style.display = 'block';
            if (talkNumber !== null)
                talkNumber.innerText = message['name'];
            showTimer(message['timer']);
        } else if (message['mode'] === 'stopped') {
            if (talk !== null)
                talk.style.display = 'none';
            if (reload) {
                location.reload();
            } else {
                centralTimerSocket.send(JSON.stringify({
                    'alert': 'stop',
                }));
            }
            if (resetOnStop) {
                remaining.text(millisecondsToTime(0));
                stopwatch.innerText = millisecondsToTime(0);
            }
            showTimer(message)
        } else if (message['mode'] === 'sync') {
            if (talk !== null)
                talk.style.display = 'block';
            if (talkNumber !== null)
                talkNumber.innerText = message['name'];
            let value = message['remaining'];
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
        } else if (message['mode'] === 'running') {
            showTimer(message);
        }
    };

    centralTimerSocket.onclose = function (_) {
        console.error('Timer Socket closed unexpectedly');
    };

    try {
        if ($('#container') !== undefined)
            line = new ProgressBar.Line('#container', {
                strokeWidth: 1,
                trailColor: '#41545e',
                trailWidth: 0.1,
                svgStyle: {
                    display: 'block',
                    width: '100%',
                },
                from: {color: '#00AFF0'},
                to: {color: '#CE352C'},
                step: function (state, line, attachment) {
                    line.path.setAttribute('stroke', state.color);
                },
            });
    } catch (_) {

    }

    function showTimer(timer) {
        if (line === undefined)
            return;
        if ('mode' in timer && (timer['mode'] === 'started') || timer['mode'] === 'running') {
            let value = timer['duration'];
            let start = moment(timer['start']);
            let span = (parseInt(value['h']) * 3600000 + parseInt(value['m']) * 60000 + parseInt(value['s']) * 1000);
            let diff = (new Date).getTime() - start;
            line.set(diff / span);
            line.animate(1.0, {
                duration: span - diff
            });
        } else if ('mode' in timer && timer['mode'] === 'stopped') {
            line.set(0.0);
            line.stop();
        }
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
            // i = `0${i}`
            i = '0' + i
        }
        return i;
    }
}