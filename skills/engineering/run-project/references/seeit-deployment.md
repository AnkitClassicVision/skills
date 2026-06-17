# SEEIT Deployment

SEEIT produces interactive HTML diagrams. Users often want to view them live rather than opening local files.

## Quick Vercel Deploy

```bash
mkdir -p /tmp/seeit-deploy
cp SEEIT.html /tmp/seeit-deploy/index.html
cd /tmp/seeit-deploy
vercel --yes --prod
```

This gives a public URL in ~10 seconds. No build step needed — SEEIT HTML is self-contained.

## When to deploy

- After SEEIT phase completes
- After major refactor (re-run SEEIT, re-deploy)
- When sharing with stakeholders who can't access local files

## Persistence

Capture the deployed URL in the repo:
```bash
echo "https://<deploy-url>.vercel.app" > .run-project/seeit-url.txt
```

This lets future agents and humans find the latest live diagram without redeploying.

## Alternative: Static file server

If Vercel is not available:
```bash
python -m http.server 8080 --directory .run-project/
# Open http://localhost:8080/seeit.html
```
