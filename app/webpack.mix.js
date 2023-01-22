/*
 * Copyright 2019-2023 Simon Zigelli
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

let mix = require('laravel-mix');

mix.disableNotifications();

let src = ['./node_modules/luxon/build/global/luxon.min.js',
    './node_modules/sweetalert2/dist/sweetalert2.min.js',
    './node_modules/htmx.org/dist/htmx.js',
    './node_modules/htmx.org/dist/ext/ws.js',
    './node_modules/hyperscript.org/dist/_hyperscript.min.js']

if (process.env.NODE_ENV === 'development')
    src.push('./node_modules/hyperscript.org/src/hdb.js');

mix.combine(src,
    './StagyBee/static/js/bundle.js');

mix.minify('./node_modules/hyperscript.org/src/socket.js', './StagyBee/static/js/hs_socket.js');
mix.minify('./node_modules/hyperscript.org/src/eventsource.js', './StagyBee/static/js/hs_eventsource.js');

mix.combine(['./node_modules/sweetalert2/dist/sweetalert2.css', './style/main.css'],
    './style/all_main.css');
