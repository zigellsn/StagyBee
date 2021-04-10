/*
 * Copyright 2019-2021 Simon Zigelli
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

import ReconnectingWebSocket from "reconnecting-websocket";
import { DateTime } from 'luxon';
import ProgressBar from "progressbar.js"

export function timer_ws(congregation_ws: string, reload: boolean, resetOnStop: boolean = false) {

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
        null, {debug: true, maxReconnectionDelay: 3000, connectionTimeout: 5000, maxRetries: 100});

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
            showTimer(message);
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
                remaining.removeClass('fg-red');
                remaining.removeClass('timesUp');
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
                } else {
                    remaining.text('-' + millisecondsToTime(rem));
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
                step: function (state, line, _) {
                    line.path.setAttribute('stroke', state.color);
                },
            });
    } catch (_) {

    }

    function showTimer(timer: any) {
        if (line === undefined || timer === undefined)
            return;
        if ('mode' in timer && (timer['mode'] === 'started') || timer['mode'] === 'running') {
            let value = timer['duration'];
            let start = DateTime.fromISO(timer['start']);
            let diff = Math.abs(start.diffNow().milliseconds);
            let span = (parseInt(value['h']) * 3600000 + parseInt(value['m']) * 60000 + parseInt(value['s']) * 1000);
            line.set(diff / span);
            line.animate(1.0, {
                duration: span - diff
            });
        } else if ('mode' in timer && timer['mode'] === 'stopped') {
            line.set(0.0);
            line.stop();
        }
    }

    function millisecondsToTime(ms: number): string {
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

    function pad(i: number): string {
        let padded: string = i.toString();
        if (i < 10) {
            // i = `0${i}`
            padded = '0' + i;
        }
        return padded;
    }
}

export function bar(id: string) {
    $('#' + id).each(function () {
        let percentage = $(this).data('percentage');
        let thisBar = $(this).get(0);
        if (thisBar === undefined || percentage === undefined)
            return;
        percentage = parseFloat(percentage);
        let color;
        if (percentage < 0.0) {
            percentage = percentage * -1.0;
            color = '#CE352C';
        } else {
            percentage = 1.0 - percentage;
            color = '#00AFF0';
        }

        let bar = new ProgressBar.Line(thisBar, {
            strokeWidth: 3,
            easing: 'easeInOut',
            duration: 1400,
            color: color,
            trailColor: '#ffffff',
            trailWidth: 0.5,
            svgStyle: {width: '100%', height: '100%'},
            text: {
                style: {
                    color: color,
                    position: 'relative',
                    left: '0',
                    top: '0',
                    padding: 0,
                    margin: 0,
                    transform: null
                },
            },
            step: (state, bar) => {
                bar.setText(Math.round(bar.value() * 100) + ' %');
            }
        });
        bar.animate(percentage);
    });
}