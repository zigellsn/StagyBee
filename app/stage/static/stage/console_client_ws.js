/*
 * Copyright 2019-2020 Simon Zigelli
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

function console_client_ws(congregation_ws) {

    let scrimTrigger = false;
    let activity = null;
    let loc = window.location;

    let line = new ProgressBar.Line('#container', {
        strokeWidth: 1,
        trailColor: '#41545e',
        trailWidth: 0.1,
        svgStyle: {
            display: 'block',
            width: '100%',
        },
        from: {color: '#60a917'},
        to: {color: '#CE352C'},
        step: function (state, line, attachment) {
            line.path.setAttribute('stroke', state.color);
        },
    });

    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console_client/${congregation_ws}/`,
    let mySocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/console_client/' + congregation_ws + '/',
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    function showAlert(alert) {
        if (alert['alert'] === 'scrim') {
            if (scrimTrigger) {
                if (activity != null)
                    Metro.activity.close(activity)
            } else {
                activity = Metro.activity.open({
                    type: 'none',
                    overlayColor: '#000',
                    overlayAlpha: 1
                });
            }
            scrimTrigger = !scrimTrigger;
        } else if (alert['alert'] === 'message')
            // Metro.infobox.create(`<h3>${gettext('Nachricht')}</h3><p style="font-size:20px">${alert['value'].replace(/(?:\r\n|\r|\n)/g, '<br />')}</p>`, 'default', {
            Metro.infobox.create('<h3>' + gettext('Nachricht') + '</h3><p style="font-size:20px">' + alert['value'].replace(/(?:\r\n|\r|\n)/g, '<br />') + '</p>', 'default', {
                width: 'auto'
            });
    }

    function showTimer(timer) {
        if (timer['timer'] === 'start' && line !== null) {
            let value = timer['value'];
            let start = moment(timer['start']);
            let span = (parseInt(value['h']) * 3600000 + parseInt(value['m']) * 60000 + parseInt(value['s']) * 1000);
            let diff = (new Date).getTime() - start;
            line.set(diff / span);
            line.animate(1.0, {
                duration: span - diff
            });
        } else if (timer['timer'] === 'stop' && line !== null) {
            line.set(0.0);
            line.stop();
        }
    }

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);

        if ('alert' in data)
            showAlert(data['alert']);
        if ('timer' in data)
            showTimer(data['timer']);
    };

    mySocket.onopen = function (_) {
        console.log('Console Client WebSocket CONNECT successful');
    };

    mySocket.onclose = function (_) {
        console.error('Console Client Socket closed unexpectedly');
    };
}