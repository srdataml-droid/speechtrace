export function send(res, status, payload) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  return res.status(status).json(payload);
}
export function checkAccess(req, res) {
  const gate = process.env.SPEECHTRACE_ACCESS_CODE;
  if (gate && req.headers['x-speechtrace-code'] !== gate) {
    send(res, 401, {error:'Access code required. Enter the tester code in Settings and retry.', code:'ACCESS_REQUIRED'});
    return false;
  }
  return true;
}
export async function readRaw(req, max=3_800_000) {
  let chunks=[], bytes=0;
  for await (const c of req) {
    const b=Buffer.isBuffer(c)?c:Buffer.from(c);bytes+=b.length;
    if(bytes>max){const e=new Error('Recording too large. Try a shorter speech or a lower recording bitrate.');e.status=413;throw e;}
    chunks.push(b);
  }
  return Buffer.concat(chunks);
}
export const FILLER_SET = new Set(['um','uh','erm','er','ah','hmm']);