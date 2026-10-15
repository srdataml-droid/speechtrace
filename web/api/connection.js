import {checkAccess,send,getGroqKey} from '../lib/shared.js';
export default async function handler(req,res){
 if(req.method!=='GET')return send(res,405,{error:'Method not allowed'});
 if(!checkAccess(req,res))return;
 const key=getGroqKey();
 if(!key)return send(res,503,{connected:false,code:'KEY_MISSING',message:'Groq API key is missing on the Vercel server.'});
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
 try{
  const response=await fetch('https://api.groq.com/openai/v1/models',{headers:{Authorization:`Bearer ${key}`},signal:controller.signal});
  const data=await response.json().catch(()=>null);
  if(!response.ok){const code=response.status===401?'GROQ_AUTH':response.status===403?'GROQ_ACCESS':response.status===429?'GROQ_RATE_LIMIT':'GROQ_UNAVAILABLE';return send(res,200,{connected:false,code,message:response.status===401?'Groq rejected this API key. Verify grok_api in Vercel.':`Groq model access check failed (HTTP ${response.status}).`});}
  const ids=new Set((data?.data||[]).map(x=>x.id));
  const asr=process.env.GROQ_ASR_MODEL||'whisper-large-v3-turbo';const coach=process.env.GROQ_COACH_MODEL||'qwen/qwen3.8-27b';
  return send(res,200,{connected:true,asr_available:ids.has(asr),coach_available:ids.has(coach),message:ids.has(asr)&&ids.has(coach)?'Groq credentials and both configured models are available. This does not yet prove an audio upload succeeds.':'Groq key works, but one of the configured models was not found.'});
 }catch(e){return send(res,200,{connected:false,code:'GROQ_NETWORK',message:e.name==='AbortError'?'Groq connection test timed out.':'Groq connection check could not finish.'});}finally{clearTimeout(timer);}
}