'use strict';

const path = require('path');
const dns = require('dns');
const util = require('util');

const appConfig = require(path.join(process.env.ENV_HOME, 'config.json'));

const Luminati = {
    resolve: async server => {
        let resolvePromise = util.promisify(dns.resolve);
        return resolvePromise(server)
            .then(addrs => addrs[0])
            .catch(err => console.error(err));
    },
};

const getProxyConfig = async (config) => {
    config = Object.assign({}, config);
    let proxyModule = eval(config.module);
    if (config.session) {
        if (!config.ip) {
            config.ip = await proxyModule.resolve(config.server);
        }
        if (config.session === true) {
            config.session = 'rand' + Math.floor(Math.random()*10000+1);
        }
        config.username += '-session-' + config.session;
    }
    return config;
}

(async () => {
    let proxyName = process.argv[2];
    if (!proxyName) {
        return;
    }

    let config = appConfig.proxy[proxyName];
    if (!config) {
        console.error('Invalid proxyName in appConfig', proxyName);
        return;
    }
    let proxyConfig = await getProxyConfig(config);
    console.log(proxyConfig);
})();

module.exports = {
    getProxyConfig,
};
