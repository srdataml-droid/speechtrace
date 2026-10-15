// The user created the actual Vercel secret as grok_api. Keep GROQ_API_KEY as a conventional alias.
export function getGroqKey(){return (process.env.grok_api || process.env.GROQ_API_KEY || '').trim()}
export function send(res,status,payload){res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('Cache-Control','no-store');return res.status(status).json(payload)}
export function checkAccess(req,res){
 const gate=process.env.SPEECHTRACE_ACCESS_CODE,enabled=!!getGroqKey();
 if(enabled&&!gate){send(res,503,{code:'ACCESS_SETUP_REQUIRED',error:'Configure SPEECHTRACE_ACCESS_CODE in Vercel to protect your inference quota.'});return false;}
 if(gate&&req.headers['x-speechtrace-code']!==gate){send(res,401,{code:'ACCESS_REQUIRED',error:'Tester access code missing or incorrect.'});return false;}
 return true;
}
export async function readRaw(req,max=3800000){let buffers=[],bytes=0;for await(const chunk of req){const b=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);bytes+=b.length;if(bytes>max){const e=new Error('This recording exceeds the 3.8 MB upload limit. Use shorter audio or compress it.');e.status=413;throw e;}buffers.push(b);}return Buffer.concat(buffers)}