const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
    transpileDependencies: true,
    devServer: {
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    configureWebpack: {
        // This produces high-quality source maps that the VS Code debugger can read
        devtool: 'source-map',
        output: {
            devtoolModuleFilenameTemplate: info => {
                return `webpack:///${info.resourcePath}`
            }
        }
    }
})