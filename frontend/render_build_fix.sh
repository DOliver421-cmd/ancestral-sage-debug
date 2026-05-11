#!/usr/bin/env bash

echo "=== Render Frontend Auto‑Doctor: Starting ==="

echo "=== Step 1: Cleaning old installs ==="
rm -rf node_modules package-lock.json yarn.lock pnpm-lock.yaml

echo "=== Step 2: Installing dependencies with conflict bypass ==="
npm install --legacy-peer-deps || npm install --force

echo "=== Step 3: Fixing date-fns conflict ==="
npm install date-fns@3.6.0 --save

echo "=== Step 4: Ensuring CRACO/Tailwind/PostCSS are aligned ==="
npm install @craco/craco tailwindcss postcss autoprefixer --save-dev

echo "=== Step 5: Rebuilding frontend ==="
npm run build

echo "=== Render Frontend Auto‑Doctor: COMPLETE ==="
