import {checkAccess,readRaw,send,getGroqKey} from '../lib/shared.js';
export const config={api:{bodyParser:false}};
const extensions={'audio/webm':'webm','audio/ogg':'ogg','audio/mp4':'m4a','audio/mpeg':'mp3','audio/wav':'wav','audio/x-wav':'wav','audio/aac':'aac'};
function classify(status,provider){
 const message=String(provider?.error?.message||provider?.message||'').toLowerCase();
 if(status===401)return {status:502,code:'GROQ_AUTH',error:'Groq rejected the API key. Check that grok_api contains a valid Groq key and redeploy.'};
 if(status===403)return {status:502,code:'GROQ_ACCESS',error:'Groq denied API access. Check the Groq account, project permissions and model access.'};
 if(status===429)return {status:429,code:'GROQ_RATE_LIMIT',error:'Groq has reached its rate or free-tier quota. Wait and retry this same recording.'};
 if(status===404||message.includes('model not found')||message.includes('model does not exist'))return {status:502,code:'MODEL_NOT_FOUND',error:'The transcription model is unavailable in this Groq account. Check GROQ_ASR_MODEL.'};
 if(status===413)return {status:413,code:'FILE_TOO_LARGE',error:'Groq rejected the recording because it is too large. Shorten it or compress it.'};
 if(status===400||status===415||status===422){
  if(/timestamp|granularit|response.format/i.test(message))return {status:422,code:'TIMING_UNSUPPORTED',error:'Groq rejected detailed timestamps. Try Fast transcription for the same recording.'};
  if(/audio|file|format|codec|webm|ffmpeg|decode|invalid/i.test(message))return {status:422,code:'AUDIO_REJECTED',error:'Groq could not read this audio format. SpeechTrace can retry with a standard WAV conversion.'};
  return {status:422,code:'BAD_AUDIO_REQUEST',error:'Groq rejected the transcription request. Retry in Fast mode or use a standard WAV recording.'};
 }
 if(status>=500)return {status:502,code:'GROQ_DOWN',error:'The Groq speech service is temporarily unavailable. Your saved recording is safe; retry later.'};
 return {status:502,code:'GROQ_ERROR',error:`Groq rejected this transcription request (HTTP ${status}). Check your Groq account and retry.`};
}
function normalize(data,model,ms,mode){
 const transcript=String(data?.text||'').trim();
 const words=(Array.isArray(data?.words)?data.words:[]).filter(w=>typeof w.word==='string'&&Number.isFinite(Number(w.start))&&Number.isFinite(Number(w.end))).map(w=>({word:w.word,start:Math.max(0,Number(w.start)),end:Math.max(0,Number(w.end)),confidence:null}));
 const utterances=(Array.isArray(data?.segments)?data.segments:[]).map(s=>({start:Number(s.start)||0,end:Number(s.end)||0,transcript:s.text||''}));
 return {transcript,words,utterances,provider:'groq',model,duration_s:Number(data?.duration)||null,transcription_ms:ms,timing_mode:mode,warning:'Whisper can miss fillers or mishear words, including Nigerian accents. Please check the transcript before coaching.'};
}
export default async function handler(req,res){
 if(req.method!=='POST')return send(res,405,{error:'Method not allowed'});
 if(!checkAccess(req,res))return;
 const key=getGroqKey();
 if(!key)return send(res,503,{code:'KEY_MISSING',error:'Groq is not configured. Add grok_api in the Vercel Production environment and redeploy.'});
 const type=String(req.headers['content-type']||'').split(';')[0].trim().toLowerCase();
 if(!extensions[type])return send(res,415,{code:'AUDIO_FORMAT',error:'The recorded file has an unsupported audio type. Try the standard WAV recovery option.'});
 let audio;try{audio=await readRaw(req);}catch(e){return send(res,e.status||400,{code:'UPLOAD_LIMIT',error:e.message});}
 if(audio.length<800)return send(res,422,{code:'EMPTY_AUDIO',error:'The recorded audio is empty. Check microphone permission and replay before retrying.'});
 const model=process.env.GROQ_ASR_MODEL||'whisper-large-v3-turbo';
 const detailed=req.headers['x-speechtrace-timing']==='detailed';
 const started=Date.now();
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
 try{
  for(let attempt=0;attempt<(detailed?2:1);attempt++){
   const timing=detailed&&attempt===0?'detailed':'fast';
   const form=new FormData();form.append('file',new Blob([audio],{type}),`speech.${extensions[type]}`);
   form.append('model',model);form.append('response_format','verbose_json');form.append('language','en');form.append('temperature','0');
   if(timing==='detailed')form.append('timestamp_granularities[]','word');
   form.append('timestamp_granularities[]','segment');
   let result;
   try{result=await fetch('https://api.groq.com/openai/v1/audio/transcriptions',{method:'POST',headers:{Authorization:'Bearer '+key},body:form,signal:controller.signal})}
   catch(e){if(e.name==='AbortError')return send(res,504,{code:'GROQ_TIMEOUT',error:'Transcription timed out. Your recording is saved in this tab; retry it.'});return send(res,502,{code:'GROQ_NETWORK',error:'Cannot reach Groq from the server right now. Replay your saved recording and retry.'});}
   const data=await result.json().catch(()=>null);
   if(result.ok){
    const parsed=normalize(data,model,Date.now()-started,timing);
    if(!parsed.transcript)return send(res,422,{code:'NO_SPEECH',error:'Groq returned no transcript. Check your recording playback or try converting it to WAV.'});
    return send(res,200,parsed);
   }
   const reason=classify(result.status,data);
   console.warn('speechtrace.asr.provider_error',{status:result.status,code:reason.code,mode:timing,mime:type});
   if(attempt===0&&detailed&&(reason.code==='TIMING_UNSUPPORTED'||reason.code==='BAD_AUDIO_REQUEST'))continue;
   return send(res,reason.status,{code:reason.code,error:reason.error,provider_status:result.status,retryable:['GROQ_RATE_LIMIT','GROQ_TIMEOUT','GROQ_NETWORK','GROQ_DOWN','AUDIO_REJECTED','TIMING_UNSUPPORTED','BAD_AUDIO_REQUEST'].includes(reason.code)});
  }
 }finally{clearTimeout(timer);}
}