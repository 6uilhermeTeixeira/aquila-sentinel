'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const http = require('node:http');
const { after, test } = require('node:test');

const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const jwk = publicKey.export({ format: 'jwk' });
jwk.kid = 'test-key';
jwk.use = 'sig';

let opaAvailable = true;
const upstream = http.createServer(async (request, response) => {
  response.setHeader('Content-Type', 'application/json');
  if (request.url === '/certs') {
    response.end(JSON.stringify({ keys: [jwk] }));
    return;
  }
  if (!opaAvailable) {
    response.writeHead(503);
    response.end('{}');
    return;
  }
  let body = '';
  for await (const chunk of request) body += chunk;
  const input = JSON.parse(body).input;
  response.end(JSON.stringify({ result: input.subject.id === 'sentinel-service' &&
    input.resource === 'health' && input.action === 'read' }));
});

function token(claimOverrides = {}, signingKey = privateKey) {
  const header = Buffer.from(JSON.stringify({ alg: 'RS256', kid: 'test-key' })).toString('base64url');
  const claims = Buffer.from(JSON.stringify({
    iss: 'http://issuer/realms/sentinel',
    aud: 'sentinel-gateway',
    azp: 'sentinel-service',
    exp: Math.floor(Date.now() / 1000) + 300,
    ...claimOverrides,
  })).toString('base64url');
  const message = `${header}.${claims}`;
  const signature = crypto.sign('RSA-SHA256', Buffer.from(message), signingKey).toString('base64url');
  return `${message}.${signature}`;
}

async function authorize(bearer, resource = 'health', action = 'read') {
  const response = await fetch(`http://127.0.0.1:${gateway.address().port}/authorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}) },
    body: JSON.stringify({ resource, action }),
  });
  return response.status;
}

let gateway;
async function main() {
await new Promise(resolve => upstream.listen(0, '127.0.0.1', resolve));
process.env.EXPECTED_ISSUER = 'http://issuer/realms/sentinel';
process.env.EXPECTED_AUDIENCE = 'sentinel-gateway';
process.env.JWKS_URL = `http://127.0.0.1:${upstream.address().port}/certs`;
process.env.OPA_URL = `http://127.0.0.1:${upstream.address().port}/opa`;
process.env.PORT = '0';
gateway = require('../gateway/server');
await new Promise(resolve => gateway.once('listening', resolve));
after(() => {
  gateway.close();
  upstream.close();
});

test('valid service token receives only explicit permission', async () => {
  assert.equal(await authorize(token()), 200);
  assert.equal(await authorize(token(), 'secrets', 'read'), 403);
});

test('missing, expired and wrong-audience tokens are rejected', async () => {
  assert.equal(await authorize(null), 401);
  assert.equal(await authorize(token({ exp: 1 })), 401);
  assert.equal(await authorize(token({ aud: 'other-service' })), 401);
});

test('invalid signature is rejected', async () => {
  const other = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
  assert.equal(await authorize(token({}, other.privateKey)), 401);
});

test('OPA outage fails closed', async () => {
  opaAvailable = false;
  assert.equal(await authorize(token()), 503);
});

}
main().catch(error => { throw error; });
