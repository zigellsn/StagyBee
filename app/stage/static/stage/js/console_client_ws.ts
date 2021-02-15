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

import ReconnectingWebSocket from "reconnecting-websocket";
import { DateTime } from 'luxon';
import Metro from "metro4";

export function console_client_ws(congregation_ws: string) {

    let scrimTrigger = false;
    let activity = null;
    let loc = window.location;

    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console_client/${congregation_ws}/`,
    let mySocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/console_client/' + congregation_ws + '/',
        null, {debug: true, maxReconnectionDelay: 3000, connectionTimeout: 5000, maxRetries: 100});

    function showAlert(alert: any) {
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
        } else if (alert['alert'] === 'message') {
            // Metro.infobox.create(`<h3>${gettext('Nachricht')}</h3><p style="font-size:20px">${alert['value'].replace(/(?:\r\n|\r|\n)/g, '<br />')}</p>`, 'default', {
            let date = DateTime.local().toMillis()
            Metro.infobox.create('<h3>' + django.gettext('Nachricht') + '</h3><p style="font-size:20px">' + alert['value'].replace(/(?:\r\n|\r|\n)/g, '<br />') + '</p>',
                'default',
                {
                    removeOnClose: true,
                    width: 'auto',
                    onClose: function () {
                        mySocket.send(JSON.stringify({'message': 'ACK', 'time': date}))
                    }
                });
        }
    }

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        if ('alert' in data)
            if (data['alert']['alert'] === 'status')
                mySocket.send(JSON.stringify({'message': 'status', 'scrim': scrimTrigger}));
            else
                showAlert(data['alert']);
    };

    mySocket.onopen = function (_) {
        console.log('Console Client WebSocket CONNECT successful');
    };

    mySocket.onclose = function (_) {
        console.error('Console Client Socket closed unexpectedly');
    };
}
