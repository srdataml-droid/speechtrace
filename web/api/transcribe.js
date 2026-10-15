import {checkAccess,readRaw,send} from '../lib/shared.js';
export const config={api:{bodyParser:false}};
const extensions={'audio/webm':'webm','audio/ogg':'ogg','audio/mp4':'m4a','audio/mpeg':'mp3','audio/wav':'wav','audio/x-wav':'wav','audio/aac':'aac'};
export default async function handler(req,res){
 if(req.method!=='POST')return send(res,405,{error:'Method not allowed'});
 if(!checkAccess(req,res))return;
 const key=process.env.GROQ_API_KEY;
 if(!key)return send(res,503,{error:'Connect your free Groq API key (GROQ_API_KEY) in Vercel and redeploy.',code:'KEY_MISSING'});
 const type=String(req.headers['content-type']||'').split(';')[0].trim().toLowerCase();
 if(!extensions[type])return send(res,415,{error:'Audio format unsupported. Please record in Chrome.'});
 let audio;try{audio=await readRaw(req);}catch(e){return send(res,e.status||400,{error:e.message});}
 if(audio.length<800)return send(res,422,{error:'Your recording was empty. Please try again.'});
 const form=new FormData();form.append('file',new Blob([audio],{type}),'rehearsal.'+extensions[type]);
 const model=process.env.GROQ_ASR_MODEL||'whisper-large-v3-turbo';
 for(const [k,v] of [['model',model],['response_format','verbose_json'],['language','en'],['temperature','0'],['timestamp_granularities[]','word'],['timestamp_granularities[]','segment']])form.append(k,v);
 const started=Date.now(),controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
 try{
  const response=await fetch('https://api.groq.com/openai/v1/audio/transcriptions',{method:'POST',headers:{Authorization:'Bearer '+key},body:form,signal:controller.signal});
  const data=await response.json().catch(()=>null);
  if(!response.ok)return send(res,response.status===429?429:502,{code:response.status===429?'FREE_TIER_LIMIT':'PROVIDER_ERROR',error:response.status===429?'The Groq free-tier audio quota was reached. Please wait, then retry.':'The Whisper model could not process this recording.',provider_status:response.status});
  const transcript=String(data?.text||'').trim();
  if(!transcript)return send(res,422,{error:'No clear speech recognized. Check playback and try again.'});
  const words=(Array.isArray(data.words)?data.words:[]).filter(w=>typeof w.word==='string'&&Number.isFinite(Number(w.start))&&Number.isFinite(Number(w.end))).map(w=>({word:w.word,start:Math.max(0,Number(w.start)),end:Math.max(0,Number(w.end)),confidence:null}));
  const utterances=(Array.isArray(data.segments)?data.segments:[]).map(s=>({start:Number(s.start)||0,end:Number(s.end)||0,transcript:s.text||''}));
  return send(res,200,{transcript,words,utterances,provider:'groq',model,duration_s:Number(data.duration)||null,transcription_ms:Date.now()-started,warning:'Whisper may omit hesitations or mishear words. Review and correct the transcript.'});
 }catch(e){return send(res,504,{code:'UPSTREAM_UNAVAILABLE',error:e.name==='AbortError'?'Transcription timed out. Retry without losing your recording.':'The speech provider could not be reached.'});}finally{clearTimeout(timer);}
}