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
function console_ws(language, congregation_ws) {
    let submitTime = document.getElementById('submit_time');
    let submitStop = document.getElementById('submit_stop');
    let submitText = document.getElementById('submit_text');
    let submitScrim = document.getElementById('submit_scrim');
    let submitRefresh = document.getElementById('submit_refresh');
    let customTalkName = document.getElementById('custom_talk');
    let messageAcknowledgement = document.getElementById('messageAcknowledgement');
    let talkNameInput = document.getElementById('talk_name');
    let loc = window.location;
    let running = -1;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    // let consoleSocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/${language}/console/${congregation_ws}/`,
    let consoleSocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/' + language + '/console/' + congregation_ws + '/',
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    let centralTimerSocket = new ReconnectingWebSocket(protocol + loc.host + '/ws/central_timer/' + congregation_ws + '/',
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    centralTimerSocket.onopen = function (_) {
        console.log('Timer WebSocket CONNECT successful');
    };

    centralTimerSocket.onclose = function (_) {
        console.error('Timer WebSocket closed unexpectedly');
    };

    centralTimerSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        if ('type' in data && data['type'] === 'timer') {
            running = data['timer']['index'];
        }
        if ('type' in data && data['type'] === 'timer' && 'mode' in data['timer'] && data['timer']['mode'] === 'running') {
            setRunningTalk(data['timer']['index']);
            $('#submit_stop').removeClass("light").addClass("primary");
        }
    };

    consoleSocket.onopen = function (_) {
        console.log('Console WebSocket CONNECT successful');
        customTalkName.style.display = 'none';
        messageAcknowledgement.style.display = 'none';
        removeAllListItems();
        consoleSocket.send(JSON.stringify({
            'alert': 'status'
        }));
    };

    consoleSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        if (data === undefined) {
            return;
        }
        if ('type' in data && data['type'] === 'times' && 'times' in data) {
            let times = data['times'];
            if (times !== undefined) {
                let lv = $('#talk_list');
                let pTimes = JSON.parse(times);
                lv.data('listview').addGroup({
                    caption: gettext('Leben-und-Dienst-Zusammenkunft')
                });
                for (let k in pTimes) {
                    if (pTimes.hasOwnProperty(k)) {
                        let values = pTimes[k];
                        for (let time in values) {
                            if (values.hasOwnProperty(time)) {
                                lv.data('listview').add(null, {
                                    caption: values[time][1],
                                    content: values[time][0]
                                }).addClass('bg-darkBlue-hover');
                            }
                        }
                    }
                }
                lv.data('listview').addGroup({
                    caption: gettext('Zusammenkunft für die Öffentlichkeit')
                });
                lv.data('listview').add(null, {
                    caption: gettext('Öffentlicher Vortrag (30 Min.)'),
                    content: 30
                }).addClass('bg-darkBlue-hover');
                lv.data('listview').add(null, {
                    caption: gettext('Wachtturm-Studium (60 Min.)'),
                    content: 60
                }).addClass('bg-darkBlue-hover');
                lv.data('listview').addGroup({
                    caption: gettext('Benutzerdefiniert')
                });
                lv.data('listview').add(null, {
                    caption: gettext('Benutzerdefiniert'),
                    content: 10
                }).addClass('bg-darkBlue-hover');
                lv.children('.node').first().click();
                lv.on("node-click", function (e) {
                    let talkName = e.detail.node[0];
                    if (talkName.innerText === gettext('Benutzerdefiniert')) {
                        customTalkName.style.display = 'block';
                    } else {
                        customTalkName.style.display = 'none';
                    }
                    let t = talkName.querySelector('div.content').innerText;
                    $('#time').data('timepicker').time('0:' + t + ':0');

                });
            }
            setRunningTalk(running);
        }
        if ('type' in data && data['type'] === 'message' && 'message' in data) {
            if (data['message']['message'] === 'ACK') {
                messageAcknowledgement.style.display = 'block';
                let line = gettext('Nachricht vom %s bestätigt.');
                messageAcknowledgement.innerText = interpolate(line, [data['message']['time']]);
            } else if (data['message']['message'] === 'status') {
                if (data['message']['scrim']) {
                    submitScrim.innerText = gettext('Verdunkelung aufheben')
                } else {
                    submitScrim.innerText = gettext('Bildschirm verdunkeln')
                }
            }
        }
    };

    consoleSocket.onclose = function (_) {
        console.error('Console WebSocket closed unexpectedly');
    };

    function setRunningTalk(talk) {
        let lv = $('#talk_list');
        if (talk !== -1 && talk < lv[0].childNodes.length) {
            $('#submit_stop').removeClass("light").addClass("primary");
            lv[0].childNodes[talk].click();
        } else
            lv.children('.node').first().click();
    }

    function removeAllListItems() {
        let list = $('#talk_list');
        list.children('.node').each(function () {
            list.data('listview').del(this);
        });
        list.children('.node-group').each(function () {
            list.data('listview').del(this);
        });
    }

    if (submitTime !== null)
        submitTime.onclick = function (_) {
            let time = $('#time').data('timepicker').time();
            if (time['h'] === 0 && time['m'] === 0 && time['s'] === 0) {
                Metro.dialog.create({
                    title: 'Timer',
                    // content: `<div>${gettext('Bitte eine Zeit > 0 angeben.')}</div>`,
                    content: '<div>' + gettext('Bitte eine Zeit > 0 angeben.') + '</div>',
                    closeButton: true
                });
                return;
            }
            let talk = $('#talk_list').find('.current')[0];
            let parent = talk.parentNode;
            let index = Array.prototype.indexOf.call(parent.children, talk) + 1;
            let talkName = talk.innerText;
            if (talkName === gettext('Benutzerdefiniert')) {
                talkName = talkNameInput.value
            }
            centralTimerSocket.send(JSON.stringify({'timer': 'stop'}));
            centralTimerSocket.send(JSON.stringify({
                'timer': 'start',
                'duration': time,
                'name': talkName,
                'index': index
            }));
            running = index;
            $('#submit_stop').removeClass("light").addClass("primary");
        };

    if (submitStop !== null)
        submitStop.onclick = function (_) {
            if (running !== -1) {
                centralTimerSocket.send(JSON.stringify({'timer': 'stop'}));
                $('#talk_list').find('.current').next().click();
                $('#submit_stop').removeClass("primary").addClass("light");
                running = -1;
            }
        };

    if (submitScrim !== null)
        submitScrim.onclick = function (_) {
            consoleSocket.send(JSON.stringify({
                'alert': 'scrim'
            }));
            consoleSocket.send(JSON.stringify({
                'alert': 'status'
            }));
        };

    if (submitRefresh !== null)
        submitRefresh.onclick = function (_) {
            consoleSocket.send(JSON.stringify({
                'alert': 'status'
            }));
        };

    if (submitText !== null)
        submitText.onclick = function (_) {
            let message = document.getElementById('text_message').value;
            if (message !== undefined && message !== '') {
                consoleSocket.send(JSON.stringify({
                    'alert': 'message',
                    'value': message
                }));
                messageAcknowledgement.style.display = 'none';
            }
        };
}
