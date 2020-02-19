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
function console_ws(congregation_ws) {
    let submitTime = document.getElementById('submit_time');
    let submitStop = document.getElementById('submit_stop');
    let submitText = document.getElementById('submit_text');
    let submitScrim = document.getElementById('submit_scrim');
    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    mySocket.onopen = function (_) {
        console.log('Console WebSocket CONNECT successful');
    };

    mySocket.onmessage = function (e) {
    };

    mySocket.onclose = function (_) {
        console.error('Console WebSocket closed unexpectedly');
    };

    if (submitTime !== null)
        submitTime.onclick = function (_) {
            let time = $('#time').data('timepicker').time();
            let select = $('#talk').data('select');
            let talk = select.val();
            if (talk === undefined)
                talk = 1;
            mySocket.send(JSON.stringify({
                'timer': 'start',
                'talk': talk,
                'start': moment().format(),
                'value': time
            }));
        };

    if (submitStop !== null)
        submitStop.onclick = function (_) {
            mySocket.send(JSON.stringify({
                'timer': 'stop'
            }));
        };

    if (submitScrim !== null)
        submitScrim.onclick = function (_) {
            mySocket.send(JSON.stringify({
                'alert': 'scrim'
            }));
        };

    if (submitText !== null)
        submitText.onclick = function (_) {
            let message = document.getElementById('text_message').value;
            if (message !== undefined && message !== '')
                mySocket.send(JSON.stringify({
                    'alert': 'message',
                    'value': message
                }));
        };
}
