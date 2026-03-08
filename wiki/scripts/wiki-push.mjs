#!/usr/bin/env node

/**
 * wiki-push.mjs – Generisches Wiki.js Push-Script
 *
 * Usage:
 *   node wiki-push.mjs create --path <wiki-path> --title <title> --file <md-file> [--tags <tags>] [--description <desc>]
 *   node wiki-push.mjs update --id <page-id> --title <title> --file <md-file> [--tags <tags>]
 *   node wiki-push.mjs update --path <wiki-path> --title <title> --file <md-file> [--tags <tags>]
 *
 * Token Resolution (in order):
 *   1. WIKI_API_KEY environment variable
 *   2. ~/.claude/.wiki-token file
 *
 * Output:
 *   JSON to stdout on success: { "ok": true, "action": "create|update", "id": 47, "path": "...", "url": "..." }
 *   JSON to stdout on failure: { "ok": false, "error": "..." }
 *   Human-readable logs to stderr.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { homedir } from 'node:os';

// --- Token Resolution ---

function resolveToken() {
  // 1. Environment variable
  if (process.env.WIKI_API_KEY) {
    return process.env.WIKI_API_KEY;
  }

  // 2. Token file
  try {
    const tokenPath = resolve(homedir(), '.claude', '.wiki-token');
    const token = readFileSync(tokenPath, 'utf-8').trim();
    if (token) {
      console.error('Token loaded from ~/.claude/.wiki-token');
      return token;
    }
  } catch {
    // File doesn't exist or isn't readable
  }

  return null;
}

// --- Configuration ---

const WIKI_URL = process.env.WIKI_URL || 'http://192.168.178.67:3100/graphql';
const WIKI_BASE_URL = WIKI_URL.replace('/graphql', '');
const API_KEY = resolveToken();

if (!API_KEY) {
  const result = { ok: false, error: 'No Wiki token found. Set WIKI_API_KEY env var or create ~/.claude/.wiki-token' };
  console.log(JSON.stringify(result));
  process.exit(1);
}

// --- Argument Parsing ---

const args = process.argv.slice(2);
const action = args[0]; // 'create' or 'update'

function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : null;
}

if (!action || !['create', 'update'].includes(action)) {
  const result = { ok: false, error: 'Usage: wiki-push.mjs <create|update> --path <path> --title <title> --file <file> [--tags <tags>] [--description <desc>] [--id <id>]' };
  console.log(JSON.stringify(result));
  process.exit(1);
}

const filePath = getArg('file');
const title = getArg('title');
const wikiPath = getArg('path');
const tagsRaw = getArg('tags');
const description = getArg('description') || '';
const pageId = getArg('id');

if (!filePath || !title) {
  const result = { ok: false, error: 'Required arguments: --file and --title' };
  console.log(JSON.stringify(result));
  process.exit(1);
}

const tags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()) : [];
const content = readFileSync(resolve(filePath), 'utf-8');

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

// --- Lookup Page ID by Path ---

async function lookupPageId(path) {
  const result = await gql(
    `query ($path: String!, $locale: String!) {
      pages {
        singleByPath(path: $path, locale: $locale) {
          id
        }
      }
    }`,
    { path, locale: 'en' }
  );

  return result?.data?.pages?.singleByPath?.id || null;
}

// --- Create Page ---

async function createPage() {
  if (!wikiPath) {
    return { ok: false, error: 'create requires --path argument' };
  }

  const result = await gql(
    `mutation ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
      pages {
        create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
          responseResult { succeeded message }
          page { id path title }
        }
      }
    }`,
    {
      content,
      description,
      editor: 'markdown',
      isPublished: true,
      isPrivate: false,
      locale: 'en',
      path: wikiPath,
      tags,
      title,
    }
  );

  const createResult = result?.data?.pages?.create;
  if (createResult?.responseResult?.succeeded) {
    return {
      ok: true,
      action: 'create',
      id: createResult.page.id,
      path: createResult.page.path,
      url: `${WIKI_BASE_URL}/${createResult.page.path}`,
    };
  } else {
    return {
      ok: false,
      error: createResult?.responseResult?.message || JSON.stringify(result.errors || result),
    };
  }
}

// --- Update Page ---

async function updatePage() {
  let id = pageId ? parseInt(pageId, 10) : null;

  if (!id && wikiPath) {
    id = await lookupPageId(wikiPath);
    if (!id) {
      return { ok: false, error: `Page not found at path: ${wikiPath}` };
    }
  }

  if (!id) {
    return { ok: false, error: 'update requires --id or --path argument' };
  }

  const result = await gql(
    `mutation ($id: Int!, $content: String!, $title: String!, $tags: [String]!, $isPublished: Boolean!) {
      pages {
        update(id: $id, content: $content, title: $title, tags: $tags, isPublished: $isPublished) {
          responseResult { succeeded message }
        }
      }
    }`,
    {
      id,
      content,
      title,
      tags,
      isPublished: true,
    }
  );

  const updateResult = result?.data?.pages?.update;
  if (updateResult?.responseResult?.succeeded) {
    return {
      ok: true,
      action: 'update',
      id,
      path: wikiPath || null,
      url: wikiPath ? `${WIKI_BASE_URL}/${wikiPath}` : null,
    };
  } else {
    return {
      ok: false,
      error: updateResult?.responseResult?.message || JSON.stringify(result.errors || result),
    };
  }
}

// --- Execute ---

try {
  const result = action === 'create' ? await createPage() : await updatePage();

  if (result.ok) {
    console.error(`${result.action.toUpperCase()} OK: ${result.path || `ID ${result.id}`}${result.url ? ` → ${result.url}` : ''}`);
  } else {
    console.error(`${action.toUpperCase()} FAIL: ${result.error}`);
  }

  console.log(JSON.stringify(result));
  process.exit(result.ok ? 0 : 1);
} catch (err) {
  const result = { ok: false, error: err.message };
  console.error(`ERROR: ${err.message}`);
  console.log(JSON.stringify(result));
  process.exit(1);
}
