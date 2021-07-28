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

const path = require('path');
const FileManagerPlugin = require("filemanager-webpack-plugin");
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

let runMode = process.env.RUN_MODE;
let devTool = undefined;
if (runMode === undefined || runMode === '') {
    runMode = 'development';
    devTool = 'source-map';
}

const mainConfig = {
    mode: runMode,
    entry: {
        main: ['./style/style.scss', './index.ts'],
    },
    output: {
        filename: 'js/[name].bundle.js',
        chunkFilename: 'js/[name].bundle.js',
        libraryTarget: 'var',
        library: ['StagyBee', '[name]'],
        path: path.resolve(__dirname, 'StagyBee/static')
    },
    optimization: {
        splitChunks: {
            cacheGroups: {
                external: {
                    test: /node_modules/,
                    chunks: 'initial',
                    name: 'external',
                    enforce: true
                },
            }
        },
        minimize: true,
        minimizer: [
            new CssMinimizerPlugin(),
        ],
    },
    externals: {
        'django': 'window.django'
    },
    devtool: devTool,
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: [{
                    loader: 'ts-loader',
                }],
                exclude: /node_modules/,
            },
            {
                test: /\.s?css$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: 'css/bundle.css',
                        },
                    },
                    {
                        loader: 'extract-loader'
                    },
                    {
                        loader: 'css-loader',
                        options: {
                            sourceMap: false,
                            esModule: false
                        }
                    },
                    {
                        loader: 'postcss-loader',
                        options: {
                            postcssOptions: {
                                plugins: [
                                    [
                                        'autoprefixer'
                                    ],
                                ],
                            },
                        }
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            // Prefer Dart Sass
                            implementation: require('sass'),
                            sassOptions: {
                                includePaths: [path.resolve(__dirname, "node_modules")],
                            },
                        },
                    }
                ],
            },
            {
                test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: '[name].[ext]',
                            outputPath: 'fonts',
                            publicPath: '../fonts',
                        }
                    }
                ]
            }
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
    },
};

const schemes = {
    mode: runMode,
    entry: {
        dark: './style/dark.less',
        light: './style/light.less',
    },
    output: {
        path: path.resolve(__dirname, 'StagyBee/static'),
        filename: '[name].scheme.js',
    },
    optimization: {
        minimize: true,
        minimizer: [
            new CssMinimizerPlugin(),
        ],
    },
    devtool: devTool,
    module: {
        rules: [
            {
                test: /\.less$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: 'css/[name].css',
                        },
                    },
                    {
                        loader: 'extract-loader'
                    },
                    {
                        loader: "css-loader",
                        options: {
                            sourceMap: false
                        }
                    },
                    {
                        loader: "less-loader",
                        options: {
                            lessOptions: {
                                strictMath: true,
                                paths: [path.resolve(__dirname, "node_modules")],
                            },
                        },
                    },
                ],
            },
        ],
    },
    plugins: [
        new FileManagerPlugin({
            events: {
                onEnd: {
                    delete: [path.resolve(__dirname, 'StagyBee/static/dark.scheme.js'), path.resolve(__dirname, 'StagyBee/static/light.scheme.js')]
                }
            }
        }),
    ],
}

module.exports = [mainConfig, schemes];