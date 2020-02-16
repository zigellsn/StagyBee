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
function stage_ws(congregation_ws, showOnlyRequestToSpeak = false) {
    let listeners = document.getElementById('listeners');
    let sumListenersContainer = document.getElementById('sumListeners');
    let sumListenersNumber = document.getElementById('sumListenersNumber');
    let activity = document.getElementById('activity');
    let errorMessage = document.getElementById('errorMessage');

    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/extractor/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    function setElements(activityVisibility, errorMessageVisibility, sumListenersContainerVisibility) {
        if (activity !== null)
            activity.style.display = activityVisibility;
        if (errorMessage !== null)
            errorMessage.style.display = errorMessageVisibility;
        if (sumListenersContainer !== null)
            sumListenersContainer.style.display = sumListenersContainerVisibility;
    }

    mySocket.onopen = function (_) {
        console.log("Stage WebSocket CONNECT successful");
        setElements('', 'none', 'none');
    };

    function parseNames(names, namesHtml, sumListeners) {
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
            if (element['givenName'] === '' && element['familyName'] === '')
                continue;
            else if (element['givenName'] === '') {
                fullName = element['familyName'];
            } else if (element['familyName'] === '') {
                fullName = element['givenName'];
            } else {
                fullName = `${element['givenName']} ${element['familyName']}`
            }
            if (element['requestToSpeak'] === true && element['speaking'] === false) {
                speak = 'bg-blue requestToSpeak';
            } else if (element['speaking'] === true) {
                speak = 'bg-green';
            } else {
                speak = 'bg-gray';
            }
            if ((showOnlyRequestToSpeak && element['requestToSpeak'] === true) || !showOnlyRequestToSpeak)
                namesHtml = `${namesHtml}<div class="button primary large ${speak} fg-black m-1" data-size="wide"><span class="ml-1">${fullName}&nbsp;</span><span class="badge inline">${element['listenerCount']}</span></div>`;
            if (typeof element['listenerCount'] === 'string')
                sumListeners += parseInt(element['listenerCount']);
            else
                sumListeners += parseInt(element['listenerCount']);
        }
        let new_element = document.createElement('div');
        new_element.innerHTML = namesHtml;
        listeners.innerHTML = '';
        listeners.appendChild(new_element);
        sumListenersNumber.textContent = sumListeners.toString();
    }

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        let namesHtml = '';
        if (data === 'extractor_not_available') {
            setElements('none', '', 'none');
            return;
        }

        setElements('none', 'none', '');

        let sumListeners = 0;
        let names = data['names'];
        if (names !== undefined)
            parseNames(names, namesHtml, sumListeners);
    };

    mySocket.onclose = function (_) {
        console.error('Stage Socket closed unexpectedly');
    };
}

function console_client_ws(congregation_ws) {

    let scrimTrigger = false;
    let activity = null;
    let loc = window.location;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console_client/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    function showAlert(alert) {
        if (alert['alert'] === 'time')
            $('#body').addClass('timeAlert');
        else if (alert['alert'] === 'clock')
            $('#clock').addClass('clockAlert');
        else if (alert['alert'] === 'stop') {
            $('#body').removeClass('timeAlert');
            $('#clock').removeClass('clockAlert');
        } else if (alert['alert'] === 'scrim') {
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
            Metro.infobox.create(`<p>${alert['value']}</p>`, 'default');
    }

    mySocket.onmessage = function (e) {
        let data = JSON.parse(e.data);

        let alert = data['alert'];
        if (alert !== undefined) {
            showAlert(alert);
        }
    };

    mySocket.onopen = function (_) {
        console.log("Console Client WebSocket CONNECT successful");
    };

    mySocket.onclose = function (_) {
        console.error('Console Client Socket closed unexpectedly');
    };
}