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

'use strict';

export function startTime() {
    let now = new Date();
    let element = document.getElementById('currentTime');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
    element = document.getElementById('currentHour');
    if (element != null)
        // element.innerHTML = `${pad(now.getHours())}`;
        element.innerHTML = pad(now.getHours());
    element = document.getElementById('currentMinute');
    if (element != null)
        // element.innerHTML = `${pad(now.getMinutes())}`;
        element.innerHTML = pad(now.getMinutes());
    element = document.getElementById('currentSecond');
    if (element != null)
        // element.innerHTML = `${pad(now.getSeconds())}`;
        element.innerHTML = pad(now.getSeconds());
    setTimeout(startTime, 500);
}

function pad(i: number): string {
    let padded: string = i.toString();
    if (i < 10) {
        // i = `0${i}`
        padded = '0' + i;
    }
    return padded;
}
