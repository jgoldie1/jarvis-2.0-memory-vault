'use strict';

const { Router } = require('express');
const router = Router();

// GET /apps – list registered apps
router.get('/', (req, res) => {
  res.json({
    apps: [
      { id: 'memory', description: 'Memory vault module' },
      { id: 'marketplace', description: 'Golden Era Marketplace module' },
    ],
  });
});

module.exports = router;
