module.exports = {
  apps: [
    {
      name: 'Tracking',
      script: './server.js',
      instances: 0,
      exec_mode: 'cluster',
      watch: false,
      env: {
        PORT: 5000
      }
    }
  ]
};
