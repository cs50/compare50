// https://stackoverflow.com/questions/61971615/how-can-i-create-one-bundle-file-from-react-create-app
const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlWebpackInlineSourcePlugin = require('html-webpack-inline-source-plugin');

module.exports = function override(config, env) {
  if (env === 'production') {
    config.plugins
      .find(plugin => Object.getPrototypeOf(plugin).constructor.name === 'HtmlWebpackPlugin')
      .options.inlineSource = '.(js|css)$'
    config.plugins.push(new HtmlWebpackInlineSourcePlugin(HtmlWebpackPlugin))
  }
  return config
}
