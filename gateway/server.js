'use strict';

const crypto = require('node:crypto');
const http = require('node:http');

const issuer = process.env.EXPECTED_ISSUER;
const audience = process.env.EXPECTED_AUDIENCE;
const jwksUrl = process.env.JWKS_URL;
const opaUrl = process.env.OPA_URL;
const port = Number(process.env.PORT || 8081);

if (!issuer || !audience || !jwksUrl || !opaUrl) {
  throw new Error('EXPECTED_ISSUER, EXPECTED_AUDIENCE, JWKS_URL and OPA_URL are required');
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(3000) });
  if (!response.ok) throw new Error(`Upstream returned ${response.status}`);
  return response.json();
}

function decodePart(value) {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error('Invalid token encoding');
  return JSON.parse(Buffer.from(value, 'base64url').toString('utf8'));
}

async function verifyToken(token) {
  if (token.length > 8192) throw new Error('Token too large');
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('Invalid token structure');
  const header = decodePart(parts[0]);
  const claims = decodePart(parts[1]);
  if (header.alg !== 'RS256' || typeof header.kid !== 'string') {
    throw new Error('Unsupported token algorithm');
  }
  const now = Math.floor(Date.now() / 1000);
  if (claims.iss !== issuer || !([].concat(claims.aud || [])).includes(audience)) {
    throw new Error('Invalid issuer or audience');
  }
  if (!Number.isInteger(claims.exp) || claims.exp <= now ||
      (claims.nbf !== undefined && (!Number.isInteger(claims.nbf) || claims.nbf > now))) {
    throw new Error('Token expired or not yet valid');
  }
  if (typeof claims.azp !== 'string' || claims.azp.length === 0) {
    throw new Error('Missing client identity');
  }
  const jwks = await fetchJson(jwksUrl);
  const jwk = jwks.keys?.find(key => key.kid === header.kid && key.kty === 'RSA' &&
    (!key.use || key.use === 'sig'));
  if (!jwk) throw new Error('Signing key unavailable');
  const publicKey = crypto.createPublicKey({ key: jwk, format: 'jwk' });
  const signature = Buffer.from(parts[2], 'base64url');
  if (!crypto.verify('RSA-SHA256', Buffer.from(`${parts[0]}.${parts[1]}`), publicKey, signature)) {
    throw new Error('Invalid signature');
  }
  return claims;
}

function send(response, status, body) {
  response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  response.end(JSON.stringify(body));
}

const server = http.createServer(async (request, response) => {
  if (request.method !== 'POST' || request.url !== '/authorize') {
    send(response, 404, { error: 'not_found' });
    return;
  }
  const authorization = request.headers.authorization || '';
  if (!authorization.startsWith('Bearer ')) {
    send(response, 401, { error: 'invalid_token' });
    return;
  }
  let claims;
  try {
    claims = await verifyToken(authorization.slice(7));
  } catch {
    send(response, 401, { error: 'invalid_token' });
    return;
  }
  let body = '';
  for await (const chunk of request) {
    body += chunk;
    if (body.length > 4096) {
      send(response, 413, { error: 'request_too_large' });
      return;
    }
  }
  let input;
  try {
    input = JSON.parse(body);
    if (typeof input.resource !== 'string' || typeof input.action !== 'string') throw new Error();
  } catch {
    send(response, 400, { error: 'invalid_request' });
    return;
  }
  try {
    const decision = await fetchJson(opaUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: {
        subject: { id: claims.azp, verified: true, expires_at: claims.exp },
        resource: input.resource,
        action: input.action,
      } }),
    });
    send(response, decision.result === true ? 200 : 403, { allowed: decision.result === true });
  } catch {
    send(response, 503, { error: 'policy_unavailable' });
  }
});

server.listen(port, '0.0.0.0');

module.exports = server;
