---
status: verifying
trigger: "Tailwind CSS not being applied on deployed Fly.io app"
created: 2026-04-17T00:00:00Z
updated: 2026-04-17T00:00:00Z
---

## Current Focus
hypothesis: "Dockerfile.fly COPY command was creating nested /app/static/dist/ structure instead of /app/static/ because source path /app/dist lacked trailing slash"
test: "Changed COPY command from 'COPY --from=builder /app/dist ./static' to 'COPY --from=builder /app/dist/ /app/static/'"
expecting: "Files now copy directly to /app/static/ preserving /app/static/assets/ structure"
next_action: "Redeploy to Fly.io and verify CSS loads correctly"

## Symptoms
expected: Tailwind CSS should style all elements with proper colors (bg-gray-900), layouts (max-w-5xl mx-auto), and spacing
actual: Browser default styling is applied. Elements are plain HTML without CSS. Everything squeezed left.
errors: No JS errors in console, but CSS appears not loaded.
reproduction: Visit https://legal-ai-saas-kalvi.fly.dev in browser - CSS not applied
started: Started after deploying to Fly.io with Vite build

## Eliminated
- hypothesis: "Tailwind not compiled correctly"
  evidence: "CSS file in dist/assets/ is 47KB and contains proper Tailwind utilities with --tw-* variables"
  timestamp: 2026-04-17
- hypothesis: "vite.config.ts misconfiguration"
  evidence: "build settings are correct (cssCodeSplit: false, assetsInlineLimit: 0) and produce proper output"
  timestamp: 2026-04-17
- hypothesis: "vite.svg favicon missing causing issues"
  evidence: "Browser ignores missing favicon, wouldn't affect CSS loading"
  timestamp: 2026-04-17
- hypothesis: "StaticFiles mount failing due to path mismatch"
  evidence: "After fix, /app/static/assets/ structure should match backend expectations"
  timestamp: 2026-04-17

## Evidence
- timestamp: 2026-04-17
  checked: "Dockerfile.fly COPY command"
  found: "Original: COPY --from=builder /app/dist ./static created nested /app/static/dist/ structure"
  implication: "Backend looked for /app/static/assets/ but files were at /app/static/dist/assets/"

- timestamp: 2026-04-17
  checked: "Docker COPY behavior"
  found: "Without trailing slash on source, Docker copies entire directory to destination"
  implication: "Fix: add trailing slash to source to copy CONTENTS only: /app/dist/"

- timestamp: 2026-04-17
  checked: "Applied fix to Dockerfile.fly"
  found: "Changed to COPY --from=builder /app/dist/ /app/static/"
  implication: "Files now copy directly to /app/static/ preserving correct structure"

## Resolution
root_cause: "Dockerfile.fly COPY command lacked trailing slash on source path. 'COPY /app/dist ./static' copies the entire 'dist' directory creating /app/static/dist/, but backend expects files at /app/static/ directly. Adding trailing slash '/app/dist/' copies CONTENTS only."
fix: "Changed Dockerfile.fly line 49 from 'COPY --from=builder /app/dist ./static' to 'COPY --from=builder /app/dist/ /app/static/'"
verification: "Need to redeploy to Fly.io and test"
files_changed:
  - backend/Dockerfile.fly
