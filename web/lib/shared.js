// Server-side Groq secret. Neither secret is sent to browsers or logs.
export function getGroqKey(){return (process.env.grok_api || process.env.GROQ_API_KEY || '').trim()}
export function send(res,status,payload){res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('Cache-Control','no-store');return res.status(status).json(payload)}

// Judge-ready public demo: no password. This per-instance limiter is best-effort
// only, not a distributed/global quota; production needs durable edge rate limits.
const clients=new Map();
const WINDOW_MS=15*60*1000;
export function checkAccess(req,res){
 if(req.method!=='POST')return true;
 const origin=req.headers?.origin;
 const allowed=new Set(['https://speechtrace-mobile-lab.vercel.app','https://speechtrace-mobile-lab-srdataml-droids-projects.vercel.app']);
 if(origin&&!allowed.has(origin)){send(res,403,{code:'ORIGIN_DENIED',error:'Open SpeechTrace from its official website.'});return false;}
 const ip=String(req.headers?.['x-vercel-forwarded-for']||req.headers?.['x-forwarded-for']||req.socket?.remoteAddress||'unknown').split(',')[0].slice(0,128);
 const now=Date.now();
 if(clients.size>1500){for(const [k,v] of clients){if(v.until<=now)clients.delete(k)}if(clients.size>1500)clients.clear()}
 let slot=clients.get(ip);if(!slot||slot.until<=now){slot={count:0,until:now+WINDOW_MS};clients.set(ip,slot)}
 if(slot.count>=12){res.setHeader('Retry-After',String(Math.max(1,Math.ceil((slot.until-now)/1000))));send(res,429,{code:'DEMO_RATE_LIMIT',error:'This demo has temporarily reached its per-visitor processing limit. Please retry later.'});return false;}
 slot.count++;return true;
}
export async function readRaw(req,max=3800000){let buffers=[],bytes=0;for await(const chunk of req){const b=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);bytes+=b.length;if(bytes>max){const e=new Error('This recording exceeds the 3.8 MB upload limit. Use shorter audio or compress it.');e.status=413;throw e;}buffers.push(b)}return Buffer.concat(buffers)}
