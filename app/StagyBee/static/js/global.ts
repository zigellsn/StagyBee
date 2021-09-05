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

'use strict';

// import Metro from 'metro4'
import { DateTime } from 'luxon';

export function startTime() {

    function pad(i: number): string {
        let padded: string = i.toString();
        if (i < 10) {
            // i = `0${i}`
            padded = '0' + i;
        }
        return padded;
    }

    let now = DateTime.local();
    let element = document.getElementById('currentTime');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.hour) + ':' + pad(now.minute) + ':' + pad(now.second);
    element = document.getElementById('currentHour');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}`;
        element.innerHTML = pad(now.hour);
    element = document.getElementById('currentMinute');
    if (element != null)
        // element.innerHTML = `${pad(now.getMinutes())}`;
        element.innerHTML = pad(now.minute);
    element = document.getElementById('currentSecond');
    if (element != null)
        // element.innerHTML = `${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.second);
    setTimeout(startTime, 500);
}

export function RedirectPage(element, url) {
    window.frames[element].location = url;
}

// export function shutdownDialogActions(dialogTitle, target) {
//     Metro.dialog.create({
//         title: dialogTitle,
//         content: '<div>' + django.gettext('Bist du sicher?') + '</div>',
//         actions: [
//             {
//                 caption: django.gettext('Nein'),
//                 cls: 'js-dialog-close alert'
//             },
//             {
//                 caption: django.gettext('Ja'),
//                 cls: 'js-dialog-close',
//                 onclick: function () {
//                     window.location.href = target;
//                 }
//             }
//         ]
//     });
// }