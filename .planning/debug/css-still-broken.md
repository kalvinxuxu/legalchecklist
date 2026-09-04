---
status: awaiting_human_verify
trigger: "CSS still not loading correctly on Fly.io deployment despite correct response"
created: 2026-04-17T12:00:00Z
updated: 2026-04-17T12:00:00Z
---

## Current Focus
hypothesis: "postcss.config.js was NOT being copied to Docker build container, so PostCSS didn't know to use Tailwind"
test: "Added COPY commands for postcss.config.js and tailwind.config.js in Dockerfile.fly"
expecting: "PostCSS will now properly process @tailwind directives and generate compiled Tailwind utility classes"
next_action: "Rebuild Docker image and deploy to Fly.io to verify CSS is now properly compiled"

## Symptoms
expected: Tailwind CSS should style all elements properly
actual: Browser default styling (unstyled content) despite CSS returning 200 with valid content
errors: No JS errors in console
reproduction: Visit https://legal-ai-saas-kalvi.fly.dev in browser - CSS not applied
started: After deploying to Fly.io with Vite build

## Eliminated
- hypothesis: "Dockerfile.fly COPY command nested structure issue"
  evidence: "Line 49 has correct trailing slash: COPY --from=builder /app/dist/ /app/static/"
  timestamp: 2026-04-17
- hypothesis: "CSS file not being served (404)"
  evidence: "CSS returns HTTP 200 with content-type: text/css; charset=utf-8"
  timestamp: 2026-04-17
- hypothesis: "Incorrect MIME type"
  evidence: "content-type header is text/css; charset=utf-8"
  timestamp: 2026-04-17
- hypothesis: "CSS content invalid or empty"
  evidence: "CSS contains valid Tailwind utilities and custom CSS"
  timestamp: 2026-04-17

## Evidence
- timestamp: 2026-04-17
  checked: "CSS response headers via curl"
  found: "HTTP/1.1 200 OK, content-type: text/css; charset=utf-8, content-length: 4608"
  implication: "Server is serving CSS correctly"

- timestamp: 2026-04-17
  checked: "HTML served from Fly.io"
  found: '<link rel="stylesheet" crossorigin href="/assets/style.css">'
  implication: "HTML references CSS with crossorigin attribute"

- timestamp: 2026-04-17
  checked: "CSS content via curl"
  found: "4608 bytes - ONLY has @tailwind directives and custom CSS, NO compiled Tailwind utilities"
  implication: "Tailwind is NOT being compiled - @tailwind directives remain as text instead of being replaced with utility classes"

- timestamp: 2026-04-17
  checked: "Local dist vs deployed CSS"
  found: "Local CSS is 47KB with compiled utilities, deployed CSS is 4.5KB with unprocessed @tailwind directives"
  implication: "Docker build is NOT properly processing Tailwind CSS"

- timestamp: 2026-04-17
  checked: "Local built index.html"
  found: "References /assets/index-DPy_QmN_.css (47KB)"
  implication: "Local build produces different output than deployed version"

- timestamp: 2026-04-17
  checked: "Deployed index.html"
  found: "References /assets/style.css (4.5KB) - NOT the same file as local build"
  implication: "Deployed version was built from different source or with different configuration"

## Resolution
root_cause: "Dockerfile.fly was NOT copying postcss.config.js and tailwind.config.js to the Docker build container. Without postcss.config.js, PostCSS/Tailwind wasn't being invoked during the Vite build, so @tailwind directives were not processed - they remained as plain text in the output CSS"
fix: "Added COPY commands for frontend/postcss.config.js and frontend/tailwind.config.js in Dockerfile.fly builder stage"
verification: "Rebuild Docker image and deploy to Fly.io. CSS should now be ~47KB with compiled Tailwind utility classes instead of 4.5KB with unprocessed @tailwind directives."
files_changed:
  - backend/Dockerfile.fly
