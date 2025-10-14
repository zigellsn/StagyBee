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

import {defineConfig} from 'vite';
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({command, mode, isSsrBuild, isPreview}) => {
    let entry = '';
    if (mode === 'development')
        entry = 'bundle_dev.js';
    else
        entry = 'bundle.js';
    return {
        build: {
            lib: {
                entry: entry,
                name: 'StagyBee',
                formats: ['umd'],
                cssFileName: 'bundle',
            },
            outDir: '../StagyBee/static',
            emptyOutDir: false,
            rollupOptions: {
                output: {
                    inlineDynamicImports: false,
                    entryFileNames: `js/bundle.js`,
                    chunkFileNames: `js/bundle.js`,
                    assetFileNames: `css/[name].[ext]`
                }
            }
        },
        plugins: [
            tailwindcss()
        ]
    }
});