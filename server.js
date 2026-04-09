'use strict';

require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'jarvis-2.0-memory-vault' });
});

// Mount app routes
const appRoutes = require('./apps/index');
app.use('/apps', appRoutes);

// Mount service routes
const serviceRoutes = require('./services/index');
app.use('/services', serviceRoutes);

// Root
app.get('/', (req, res) => {
  res.json({
    name: 'Jarvis 2.0 Memory Vault',
    version: '1.0.0',
    type: 'backend',
    status: 'running',
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Global error handler
app.use((err, req, res, _next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`Jarvis 2.0 Memory Vault server running on port ${PORT}`);
});

module.exports = app;
