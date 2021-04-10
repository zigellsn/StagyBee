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

import Metro from "metro4"
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

export function reloadOnNavigateBack() {
    let perfEntries = performance.getEntriesByType("navigation");
    for (let i = 0; i < perfEntries.length; i++) {
        let p = perfEntries[i];
        if ('type' in p && p['type'] === 'back_forward') {
            location.reload();
            break;
        }
    }
}

function setColorScheme(dark: boolean, darkStyle: string, lightStyle: string): string {
    let scheme;
    let icon = $('#scheme-icon');
    let qrCode = $('.qrline');

    if (!dark) {
        scheme = lightStyle;
        if (icon !== null) {
            icon.removeClass('mif-sun4').addClass('mif-sun');
            icon.attr('data-hint-text', django.gettext('Dunkles Design'));
        }
        if (qrCode !== null) {
            qrCode.attr('stroke', '#000');
        }
    } else {
        scheme = darkStyle;
        if (icon !== null) {
            icon.removeClass('mif-sun').addClass('mif-sun4');
            icon.attr('data-hint-text', django.gettext('Helles Design'));
        }
        if (qrCode !== null) {
            qrCode.attr('stroke', '#fff');
        }
    }
    return scheme;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

export function loadColorScheme(darkStyle: string, lightStyle: string) {

    let xhr = new XMLHttpRequest();
    xhr.onerror = function () {
        console.error(xhr.responseText);
    }
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            let id = $('#color-scheme');
            if (id !== null) {
                let mode = xhr.response.toLowerCase() !== 'false';
                let actualStyle = id.attr('href')
                if ((actualStyle === darkStyle && mode === false) || actualStyle === lightStyle && mode === true) {
                    let scheme = setColorScheme(mode, darkStyle, lightStyle);
                    id.attr("href", scheme);
                    Metro.utils.addCssRule(Metro.sheet, ".app-bar-menu li", "list-style: none!important;");
                }
            }
        }
    }
    xhr.open('GET', '/scheme/', true);
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
    xhr.send();
}

export function toggleColorScheme(darkStyle: string, lightStyle: string) {

    let id = $('#color-scheme');
    if (id !== null) {
        let scheme
        if (id.attr('href') === darkStyle) {
            scheme = setColorScheme(false, darkStyle, lightStyle);
        } else {
            scheme = setColorScheme(true, darkStyle, lightStyle);
        }
        id.attr("href", scheme);
        Metro.utils.addCssRule(Metro.sheet, ".app-bar-menu li", "list-style: none!important;");
    }

    let xhr = new XMLHttpRequest();
    xhr.onerror = function () {
        console.error(xhr.responseText);
    }
    xhr.open('POST', '/toggle_scheme/', true);
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"))
    xhr.send();
}

export function RedirectPage(element, url) {
    window.frames[element].location = url;
}

export function shutdownDialogActions(dialogTitle, target) {
    Metro.dialog.create({
        title: dialogTitle,
        content: "<div>{{ confirm }}</div>",
        actions: [
            {
                caption: django.gettext('Nein'),
                cls: "js-dialog-close alert"
            },
            {
                caption: django.gettext('Ja'),
                cls: "js-dialog-close",
                onclick: function () {
                    window.location.href = target;
                }
            }
        ]
    });
}