import {checkAccess,readRaw,send} from '../lib/shared.js';
export const config={api:{bodyParser:false}};
const AUDIO_TYPES=['audio/webm','audio/ogg','audio/mp4','audio/mpeg','audio/wav','audio/x-wav','audio/aac'];
export default async function handler(req,res){
  if(req.method!=='POST')return send(res,405,{error:'Method not allowed'});
  if(!checkAccess(req,res))return;
  const key=process.env.DEEPGRAM_API_KEY;
  if(!key)return send(res,503,{error:'Fast transcription is not configured yet. Add DEEPGRAM_API_KEY to Vercel project environment variables, then redeploy.',code:'KEY_MISSING'});
  const type=(req.headers['content-type']||'').split(';')[0].trim().toLowerCase();
  if(!AUDIO_TYPES.includes(type))return send(res,415,{error:'Unsupported audio type. Record in Chrome and retry.'});
  let input;try{input=await readRaw(req);}catch(e){return send(res,e.status||400,{error:e.message});}
  if(input.byteLength<800)return send(res,422,{error:'The recording is empty. Check microphone permission and speak again.'});
  const started=Date.now();
  const query=new URLSearchParams({model:'nova-3',language:'en',punctuate:'true',smart_format:'true',filler_words:'true',utterances:'true'});
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),45000);
  try{
    const dg=await fetch(`https://api.deepgram.com/v1/listen?${query}`,{
      method:'POST',headers:{Authorization:`Token ${key}`,'Content-Type':type},body:input,signal:controller.signal
    });
    const data=await dg.json().catch(()=>null);
    if(!dg.ok){
      return send(res,502,{error:dg.status===429?'Transcription provider is rate-limited. Try again shortly.':'Speech provider could not process this recording.',code:'PROVIDER_ERROR',provider_status:dg.status});
    }
    const alt=data?.results?.channels?.[0]?.alternatives?.[0];
    const words=(alt?.words||[]).map(w=>({word:w.punctuated_word||w.word||'',start:Math.max(0,Number(w.start)||0),end:Math.max(0,Number(w.end)||0),confidence:typeof w.confidence==='number'?w.confidence:null}));
    const transcript=(alt?.transcript||'').trim();
    if(!transcript)return send(res,422,{error:'No clear speech detected. Please record closer to your microphone.'});
    const utterances=(data?.results?.utterances||[]).map(u=>({start:Number(u.start)||0,end:Number(u.end)||0,transcript:u.transcript||''}));
    return send(res,200,{transcript,words,utterances,provider:'deepgram',model:'nova-3',duration_s:data?.metadata?.duration||null,transcription_ms:Date.now()-started,warning:'Automatic transcripts can omit hesitations or mishear names and accents. Verify against playback.'});
  }catch(e){return send(res,504,{error:e.name==='AbortError'?'Speech provider timed out. Your recording is safe on this page; retry.':'Network error reaching transcription provider. Try again.',code:'UPSTREAM_UNAVAILABLE'});}
  finally{clearTimeout(timeout);}
}