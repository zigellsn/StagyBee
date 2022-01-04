/*
 * Copyright 2019-2022 Simon Zigelli
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

export function stage_ws(congregation_ws: string, showOnlyRequestToSpeak: boolean = false) {
    let listeners = document.getElementById('listeners');
    let sumListenersContainer = document.getElementById('sumListeners');
    let sumListenersNumber = document.getElementById('sumListenersNumber');
    let sumRequestToSpeakNumber = document.getElementById('sumRequestToSpeakNumber');
    let activity = document.getElementById('activity');
    let errorMessage = document.getElementById('errorMessage');

    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/extractor/${congregation_ws}/`,
    let mySocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/extractor/' + congregation_ws + '/',
        null, {debug: true, maxReconnectionDelay: 3000, connectionTimeout: 5000, maxRetries: 100});

    function setElements(activityVisibility: string, errorMessageVisibility: string, sumListenersContainerVisibility: string) {
        if (activity !== null)
            activity.style.display = activityVisibility;
        if (errorMessage !== null)
            errorMessage.style.display = errorMessageVisibility;
        if (sumListenersContainer !== null)
            sumListenersContainer.style.display = sumListenersContainerVisibility;
    }

    mySocket.onopen = function (_) {
        console.log('Stage WebSocket CONNECT successful');
        setElements('', 'none', 'none');
    };

    function parseNames(names: any, namesHtml: string) {
        let sumListeners: number = 0;
        let sumRequestToSpeak: number = 0;
        names.sort(function (a, b) {
            if (a['familyName'] < b['familyName'])
                return -1;
            if (a['familyName'] > b['familyName'])
                return 1;
            if (a['givenName'] < b['givenName'])
                return -1;
            if (a['givenName'] > b['givenName'])
                return 1;
            return 0;
        });
        for (const element of names) {
            let speak = '';
            let fullName = '';
            let listenerType = '';
            if (element['givenName'] === '' && element['familyName'] === '')
                continue;
            else if (element['givenName'] === '') {
                fullName = element['familyName'];
            } else if (element['familyName'] === '') {
                fullName = element['givenName'];
            } else {
                // fullName = `${element['givenName']} ${element['familyName']}`
                fullName = element['givenName'] + ' ' + element['familyName']
            }
            if (element['requestToSpeak'] === true && element['speaking'] === false) {
                speak = 'bg-blue requestToSpeak';
                sumRequestToSpeak += 1;
            } else if (element['speaking'] === true) {
                speak = 'bg-green';
            } else {
                speak = 'bg-gray';
            }
            if (element['listenerType'] <= 3) {
                listenerType = 'mif-phone';
            } else {
                listenerType = 'mif-tablet';
            }
            if ((showOnlyRequestToSpeak && element['requestToSpeak'] === true) || !showOnlyRequestToSpeak)
                namesHtml = namesHtml + '<div class="button primary large ' + speak + ' fg-black m-1" data-size="wide"><span class="ml-1"><span class="' + listenerType + '"></span>&nbsp;' + fullName + '&nbsp;</span><span class="badge inline">' + element['listenerCount'] + '</span></div>';
            // namesHtml = `${namesHtml}<div class="button primary large ${speak} fg-black m-1" data-size="wide"><span class="ml-1">${fullName}&nbsp;</span><span class="badge inline">${element['listenerCount']}</span></div>`;
            sumListeners += parseInt(element['listenerCount']);
        }
        let new_element = document.createElement('div');
        new_element.innerHTML = namesHtml;
        if (listeners !== null) {
            listeners.innerHTML = '';
            listeners.appendChild(new_element);
        }
        if (sumListenersNumber !== null)
            sumListenersNumber.textContent = sumListeners.toString();
        if (sumRequestToSpeakNumber !== null)
            sumRequestToSpeakNumber.textContent = sumRequestToSpeak.toString();
    }

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let namesHtml = '';
        if (data === 'extractor_not_available') {
            setElements('none', '', 'none');
            if (listeners !== null)
                listeners.innerHTML = '';
            return;
        }
        if (data === 'subscribed_to_extractor') {
            setElements('none', 'none', '');
            return;
        }
        if ('running' in data) {
            if (data['running'] === true)
                setElements('none', 'none', '');
            else {
                setElements('none', '', 'none');
                if (listeners !== null)
                    listeners.innerHTML = '';
            }
            return;
        }
        if ('names' in data) {
            setElements('none', 'none', '');

            let names = data['names'];
            if (names !== undefined)
                parseNames(names, namesHtml);
        }
    };

    mySocket.onclose = function (_) {
        console.error('Stage Socket closed unexpectedly');
    };
}
