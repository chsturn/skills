#!/usr/bin/env node

/**
 * wiki-fetch.mjs – Fetch Wiki.js page content via GraphQL API
 *
 * Usage:
 *   node wiki-fetch.mjs --path <wiki-path> [--locale <locale>]
 *
 * Environment:
 *   WIKI_API_KEY  – Required. Wiki.js API token.
 *   WIKI_URL      – Optional. Wiki.js GraphQL endpoint (default: http://192.168.178.67:3100/graphql)
 *
 * Output:
 *   JSON to stdout on success: { "ok": true, "page": { "id": 47, "path": "...", "title": "...", "content": "...", "tags": [...], "updatedAt": "..." } }
 *   JSON to stdout on failure: { "ok": false, "error": "..." }
 *   Human-readable logs to stderr.
 */

// --- Configuration ---

const WIKI_URL = process.env.WIKI_URL || 'http://192.168.178.67:3100/graphql';
const API_KEY = process.env.WIKI_API_KEY;

if (!API_KEY) {
  const result = { ok: false, error: 'WIKI_API_KEY environment variable is required' };
  console.log(JSON.stringify(result));
  process.exit(1);
}

// --- Argument Parsing ---

const args = process.argv.slice(2);

function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : null;
}

const wikiPath = getArg('path');
const locale = getArg('locale') || 'en';

if (!wikiPath) {
  const result = { ok: false, error: 'Usage: wiki-fetch.mjs --path <wiki-path> [--locale <locale>]' };
  console.log(JSON.stringify(result));
  process.exit(1);
}

// --- GraphQL Helper ---

async function gql(query, variables) {
  const maxRetries = 2;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(WIKI_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({ query, variables }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      if (attempt < maxRetries) {
        console.error(`Retry ${attempt + 1}/${maxRetries} after error: ${err.message}`);
        await new Promise(r => setTimeout(r, 2000));
      } else {
        throw err;
      }
    }
  }
}

// --- Fetch Page ---

async function fetchPage() {
  console.error(`Fetching page: ${wikiPath} (locale: ${locale})`);

  const result = await gql(
    `query ($path: String!, $locale: String!) {
      pages {
        singleByPath(path: $path, locale: $locale) {
          id
          path
          title
          description
          content
          tags {
            tag
          }
          updatedAt
        }
      }
    }`,
    { path: wikiPath, locale }
  );

  const page = result?.data?.pages?.singleByPath;

  if (!page) {
    return { ok: false, error: `Page not found at path: ${wikiPath}` };
  }

  return {
    ok: true,
    page: {
      id: page.id,
      path: page.path,
      title: page.title,
      description: page.description,
      content: page.content,
      tags: (page.tags || []).map(t => t.tag),
      updatedAt: page.updatedAt,
    },
  };
}

// --- Execute ---

try {
  const result = await fetchPage();

  if (result.ok) {
    console.error(`FETCH OK: ${result.page.path} (ID ${result.page.id}, ${result.page.content.length} chars)`);
  } else {
    console.error(`FETCH FAIL: ${result.error}`);
  }

  console.log(JSON.stringify(result));
  process.exit(result.ok ? 0 : 1);
} catch (err) {
  const result = { ok: false, error: err.message };
  console.error(`ERROR: ${err.message}`);
  console.log(JSON.stringify(result));
  process.exit(1);
}
