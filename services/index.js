'use strict';

const { Router } = require('express');
const router = Router();

// GET /services – list available services
router.get('/', (req, res) => {
  res.json({
    services: [
      { id: 'ai', description: 'AI integration service' },
      { id: 'vault', description: 'Memory vault persistence service' },
    ],
  });
});

module.exports = router;
