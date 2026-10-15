// Accept the owner's Vercel variable name as well as the conventional Groq name.
export function getGroqKey(){return (process.env.grok_api || process.env.GROQ_API_KEY || '').trim();}
export function send(res,status,payload){
 res.setHeader('Content-Type','application/json; charset=utf-8');res.setHeader('Cache-Control','no-store');
 return res.status(status).json(payload);
}
export function checkAccess(req,res){
 const gate=process.env.SPEECHTRACE_ACCESS_CODE,apiConnected=!!getGroqKey();
 if(apiConnected&&!gate){send(res,503,{error:'Protect your Groq free-tier quota: set SPEECHTRACE_ACCESS_CODE in Vercel.',code:'ACCESS_SETUP_REQUIRED'});return false;}
 if(gate&&req.headers['x-speechtrace-code']!==gate){send(res,401,{error:'The tester access code is missing or incorrect.',code:'ACCESS_REQUIRED'});return false;}
 return true;
}
export async function readRaw(req,max=3800000){
 let buffers=[],bytes=0;
 for await(const chunk of req){const b=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);bytes+=b.length;
  if(bytes>max){const e=new Error('Recording exceeds the upload limit. Use shorter audio or compress it.');e.status=413;throw e;}
  buffers.push(b);
 }
 return Buffer.concat(buffers);
}
