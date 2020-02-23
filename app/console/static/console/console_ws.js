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
    let customTalkName = document.getElementById('custom_talk_name');
    let talkNameInput = document.getElementById('talk_name');
    let loc = window.location;
    let running = false;
    let protocol = 'ws://';
    if (loc.protocol === 'https:') {
        protocol = 'wss://'
    }

    let mySocket = new ReconnectingWebSocket(`${protocol}${loc.host}/ws/console/${congregation_ws}/`,
        null, {debug: true, reconnectInterval: 3000, timeoutInterval: 5000, maxReconnectAttempts: 100});

    mySocket.onopen = function (_) {
        console.log('Console WebSocket CONNECT successful');
        customTalkName.style.display = 'none';
        let list = $('#talk_list');
        list.children('.node').each(function () {
            list.data('listview').del(this);
        });
        list.children('.node-group').each(function () {
            list.data('listview').del(this);
        });
    };

    mySocket.onmessage = function (e) {
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
                    caption: 'Freitag'
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
                    caption: 'Sonntag'
                });
                lv.data('listview').add(null, {
                    caption: 'Öffentlicher Vortrag (30 Min.)',
                    content: 30
                }).addClass('bg-darkBlue-hover');
                lv.data('listview').add(null, {
                    caption: 'Bibelstudium anhand des Wachtturms (60 Min.)',
                    content: 60
                }).addClass('bg-darkBlue-hover');
                lv.data('listview').addGroup({
                    caption: 'Custom'
                });
                lv.data('listview').add(null, {
                    caption: 'Custom',
                    content: 10
                }).addClass('bg-darkBlue-hover');
                lv.children('.node').first().click();
            }
        }

    };

    $('#talk_list').on("node-click", function (e) {
        let talkName = e.detail.node[0];
        if (talkName.innerText === 'Custom') {
            customTalkName.style.display = 'block';
        } else {
            customTalkName.style.display = 'none';
        }
        let t = talkName.querySelector('div.content').innerText;
        $('#time').data('timepicker').time('0:' + t + ':0');

    });

    mySocket.onclose = function (_) {
        console.error('Console WebSocket closed unexpectedly');
    };

    if (submitTime !== null)
        submitTime.onclick = function (_) {
            let time = $('#time').data('timepicker').time();
            if (time['h'] === 0 && time['m'] === 0 && time['s'] === 0) {
                Metro.dialog.create({
                    title: "Timer",
                    content: "<div>Bitte eine Zeit > 0 angeben.</div>",
                    closeButton: true
                });
                return;
            }
            let talkName = $('#talk_list').find('.current')[0].innerText;
            if (talkName === 'Custom') {
                talkName = talkNameInput.value
            }
            mySocket.send(JSON.stringify({
                'timer': 'start',
                'talk': talkName,
                'start': moment().format(),
                'value': time
            }));
            running = true;
        };

    if (submitStop !== null)
        submitStop.onclick = function (_) {
            if (running) {
                mySocket.send(JSON.stringify({
                    'timer': 'stop'
                }));
                $('#talk_list').find('.current').next().click();
                running = false;
            }
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
