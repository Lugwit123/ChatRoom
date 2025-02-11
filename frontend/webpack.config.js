// webpack.config.js
const path = require('path');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    entry: './frontend/App.js',
    devtool: 'eval-source-map', // 生成完整的 Source Maps

    output: {
      path: path.resolve(__dirname, 'frontend', 'dist'),
      filename: isProduction ? '[name].[contenthash].js' : 'bundle.js',
      assetModuleFilename: 'assets/[hash][ext][query]', // 统一处理静态资源
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: 'babel-loader',
        },
        {
          test: /\.css$/,
          use: [
            'style-loader',
            {
              loader: 'css-loader',
              options: {
                sourceMap: !isProduction,
              },
            },
          ],
        },
        {
          test: /\.tsx?$/,
          exclude: /node_modules/,
          use: 'ts-loader',
        },
        {
          test: /\.(png|jpg|gif|svg)$/,
          type: 'asset/resource',
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js', '.jsx'],
    },
    plugins: [
      new CleanWebpackPlugin(), // 自动清理 dist 文件夹
      new HtmlWebpackPlugin({
        template: './frontend/index.html', // 自动注入到HTML模板中
        minify: isProduction ? {
          removeComments: true,
          collapseWhitespace: true,
        } : false,
      }),
    ],
    optimization: {
      splitChunks: {
        chunks: 'all', // 拆分 vendor 和 app 代码
      },
      runtimeChunk: 'single', // 分离 runtime 代码
      minimize: false,  // 禁用代码压缩
    },
    mode: 'development',
    devServer: {
      static: path.join(__dirname, 'frontend', 'dist'),
      compress: true,
      port: 8080,
      hot: true,
    },
  };
};
