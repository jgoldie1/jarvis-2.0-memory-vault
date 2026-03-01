console.log('dashboard loaded');

const aiStatsEl = document.createElement('div');
aiStatsEl.id = 'live-ai-stats';
document.body.appendChild(aiStatsEl);

async function fetchLocalStats() {
	try {
		const r = await fetch('/fintech/ai_stats.json');
		if (!r.ok) return null;
		return await r.json();
	} catch (e) { return null; }
}

async function fetchApiStats() {
	try {
		const r = await fetch('http://localhost:5002/api/stats');
		if (!r.ok) return null;
		return await r.json();
	} catch (e) { return null; }
}

function renderStats(stats) {
	if (!stats) return;
	const ai = stats.ai || stats;
	const wallet = stats.wallet || {};
	aiStatsEl.innerText = `AI: ${JSON.stringify(ai)} | Wallet: ${JSON.stringify(wallet)}`;
}

async function poll() {
	const api = await fetchApiStats();
	if (api && api.ai) {
		renderStats(api);
		return;
	}
	const local = await fetchLocalStats();
	renderStats({ ai: local || {}, wallet: {} });
}

setInterval(poll, 5000);
poll();
