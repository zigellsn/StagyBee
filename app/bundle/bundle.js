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
import htmx from 'htmx.org'
import _hyperscript from 'hyperscript.org'
import * as ws from 'htmx-ext-ws'
import sweetalert from 'sweetalert2'
import * as hs_socket from './node_modules/hyperscript.org/src/socket.js'
import * as hs_eventsource from './node_modules/hyperscript.org/src/eventsource.js'
import './main.css'
import 'sweetalert2/dist/sweetalert2.css';

window.htmx = htmx
_hyperscript.browserInit();

export {DateTime, sweetalert, htmx, _hyperscript, ws, hs_eventsource, hs_socket}
