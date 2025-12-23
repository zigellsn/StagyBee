/*
 * Copyright 2025 Simon Zigelli
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

import {DateTime} from 'luxon';
import htmx from 'htmx.org';
import * as ws from 'htmx-ext-ws';
import _hyperscript from 'hyperscript.org';
import * as hdb from 'hyperscript.org/dist/hdb';
import hs_eventsource from 'hyperscript.org/dist/eventsource';
import hs_socket from 'hyperscript.org/dist/socket';
import sweetalert from 'sweetalert2';
import './dist/bundle.css';

function init() {
    _hyperscript.browserInit();
    _hyperscript.use(hs_eventsource);
    _hyperscript.use(hs_socket);
}

let StagyBee;
if (process.env.NODE_ENV !== "production") {
    StagyBee = {init, DateTime, sweetalert, htmx, ws, _hyperscript, hs_eventsource, hs_socket, hdb};
    console.log('This is a development build. Do not use in production.');
} else
    StagyBee = {init, DateTime, sweetalert, htmx, ws, _hyperscript, hs_eventsource, hs_socket, undefined};
export {StagyBee};
