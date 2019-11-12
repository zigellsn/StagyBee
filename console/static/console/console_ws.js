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
    let submitButton = document.getElementById('submit');
    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    mySocket.onopen = function (_) {
        console.log("WebSocket CONNECT successful");
    };

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let message = data['message'];
        console.log(message);
    };

    mySocket.onclose = function (_) {
        console.error('Socket closed unexpectedly');
    };

    submitButton.onclick = function (_) {
        let time = $('#time').data('timepicker').time();
        mySocket.send(JSON.stringify({
            'alert': time
        }));
    };
}
