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

import {console_client_ws} from './stage/static/stage/js/console_client_ws';
import {console_ws} from './console/static/console/js/console_ws';
import {
    loadColorScheme,
    RedirectPage,
    reloadOnNavigateBack,
    shutdownDialogActions,
    startTime,
    toggleColorScheme
} from './StagyBee/static/stagybee/js/global';
import {stage_ws} from './stage/static/stage/js/stage_ws';
import {bar, timer_ws} from './stopwatch/static/stopwatch/js/timer_ws';

export {
    console_client_ws,
    console_ws,
    reloadOnNavigateBack,
    loadColorScheme,
    toggleColorScheme,
    startTime,
    RedirectPage,
    shutdownDialogActions,
    stage_ws,
    timer_ws,
    bar
}
