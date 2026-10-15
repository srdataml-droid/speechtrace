const $=id=>document.getElementById(id);
const FILLER=new Set(['um','uh','erm','er','ah','hmm','umm','uhh']);
let stream=null,recorder=null,chunks=[],audioBlob=null,objectUrl=null,clock=0,tick=null,busy=false,lastTranscript='',wordTimes=[],acoustic=null,report=null;
function secs(v){return `${String(Math.floor(v/60)).padStart(2,'0')}:${String(Math.floor(v%60)).padStart(2,'0')}`;}
function status(s,kind=''){const e=$('status');e.textContent=s;e.style.color=kind==='error'?'#ffb7bd':'#bdd8dc';}
function message(s,err=false){const n=$('notice');n.classList.remove('hidden');n.classList.toggle('error',err);n.textContent=s;}
function phase(s,detail='Please keep this page open'){const el=$('process');el.classList.remove('hidden');$('phase').textContent=s;$('phaseDetail').textContent=detail;}
function endPhase(){$('process').classList.add('hidden');}
function html(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function fetchWithTimeout(path,options,ms=50000){const ac=new AbortController(),t=setTimeout(()=>ac.abort(),ms);return fetch(path,{...options,signal:ac.signal}).finally(()=>clearTimeout(t));}
function contentType(){return(audioBlob?.type||'audio/webm').split(';')[0];}
async function startRecording(){
 if(busy)return;
 if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){status('This browser cannot record. Open the site in current Chrome with HTTPS.','error');return;}
 try{
  stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,channelCount:1}});
  const options=['audio/webm;codecs=opus','audio/mp4','audio/webm','audio/ogg;codecs=opus'].find(t=>MediaRecorder.isTypeSupported(t));
  recorder=new MediaRecorder(stream,options?{mimeType:options,audioBitsPerSecond:48000}:{});chunks=[];wordTimes=[];report=null;audioBlob=null;$('report').classList.add('hidden');$('transcript').value='';$('provider').textContent='Not transcribed yet';$('notice').classList.add('hidden');$('playback').classList.add('hidden');$('review').disabled=true;$('retry').disabled=true;$('coachAgain').disabled=true;
  recorder.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data)};
  recorder.onerror=()=>status('Recording error. Please retry; microphone access is required.','error');
  recorder.onstop=()=>{
   stream?.getTracks().forEach(t=>t.stop());clearInterval(tick);$('record').disabled=false;$('stop').disabled=true;
   audioBlob=new Blob(chunks,{type:recorder.mimeType||'audio/webm'});
   if(audioBlob.size<900){status('Recording saved but empty. Try again and speak near the microphone.','error');return;}
   if(objectUrl)URL.revokeObjectURL(objectUrl);objectUrl=URL.createObjectURL(audioBlob);
   $('player').src=objectUrl;$('player').load();$('playback').classList.remove('hidden');$('saveAudio').href=objectUrl;$('saveAudio').download='speechtrace-rehearsal.'+(audioBlob.type.includes('mp4')?'m4a':audioBlob.type.includes('ogg')?'ogg':'webm');
   $('run').disabled=false;$('recordstate').textContent='Voice captured';status('Recording ready. Play it back, then tap Analyze.');
  };
  recorder.start(300);clock=Date.now();$('timer').textContent='00:00';tick=setInterval(()=>{$('timer').textContent=secs((Date.now()-clock)/1000);if(Date.now()-clock>=300000)finishRecording();},230);
  $('recordpad').classList.add('recording');$('recordstate').textContent='Recording your pitch';$('record').disabled=true;$('stop').disabled=false;$('run').disabled=true;status('Microphone permission granted. Speak normally, then tap Finish.');
 }catch(e){stream?.getTracks().forEach(t=>t.stop());status('Could not access your microphone. Allow microphone permission in Chrome and retry: '+e.message,'error');}
}
function finishRecording(){if(recorder?.state==='recording'){try{recorder.requestData();}catch{}recorder.stop();$('recordpad').classList.remove('recording');status('Finishing recording…');}}
$('record').onclick=startRecording;$('stop').onclick=finishRecording;
$('uploadFile').onchange=e=>{
 const file=e.target.files?.[0];if(!file||busy||recorder?.state==='recording')return;
 if(file.size<900){status('That file appears empty. Choose an audio recording.','error');return;}
 if(file.size>3800000){message('Audio file is above the 3.8 MB speech-upload limit. You can still play it, but transcription needs a shorter/compressed file.',true);}
 if(objectUrl)URL.revokeObjectURL(objectUrl);
 audioBlob=file;objectUrl=URL.createObjectURL(file);wordTimes=[];lastTranscript='';acoustic=null;report=null;
 $('transcript').value='';$('provider').textContent='Not transcribed yet';$('report').classList.add('hidden');
 $('player').src=objectUrl;$('player').load();$('playback').classList.remove('hidden');
 $('saveAudio').href=objectUrl;$('saveAudio').download=file.name||'speechtrace-saved-recording';
 $('run').disabled=false;$('retry').disabled=true;$('review').disabled=true;$('coachAgain').disabled=true;
 $('recordstate').textContent='Saved recording loaded';
 status('Saved audio loaded. Replay it first, then tap Analyze. You do not need to record the same pitch again.');
};
$('play').onclick=async()=>{try{$('player').currentTime=0;await $('player').play();}catch{status('Audio did not play. Tap the built-in audio player or Save recording.','error');}};
function playAt(n){try{$('player').currentTime=Math.max(0,n);$('player').play().catch(()=>status('Tap the audio player to start playback.'));}catch{}}
async function captureAcoustics(){
 const ctx=new (window.AudioContext||window.webkitAudioContext)();let decoded;
 try{decoded=await ctx.decodeAudioData(await audioBlob.arrayBuffer());}finally{ctx.close();}
 const sr=decoded.sampleRate,len=decoded.length,hop=Math.max(1,Math.round(sr*0.04)),win=Math.max(1,Math.round(sr*0.06)),frame=[];
 const ch=Array.from({length:decoded.numberOfChannels},(_,i)=>decoded.getChannelData(i));
 for(let i=0;i+win<len;i+=hop){let sum=0,count=0;for(let j=i;j<i+win;j+=4){let x=0;for(const c of ch)x+=c[j]/ch.length;sum+=x*x;count++;}frame.push(Math.sqrt(sum/Math.max(1,count)));}
 const dur=decoded.duration,arr=[...frame].sort((a,b)=>a-b),max=arr[Math.floor(arr.length*.95)]||0,threshold=Math.max(0.002,max*.09),pauses=[];let opened=null;
 for(let i=0;i<=frame.length;i++){
  if(i<frame.length&&frame[i]<threshold&&opened===null)opened=i;
  if((i===frame.length||frame[i]>=threshold)&&opened!==null){const start=opened*hop/sr,end=i*hop/sr;if(end-start>=1.0&&start>0.25&&end<dur-.25)pauses.push({start:+start.toFixed(2),end:+end.toFixed(2),length_s:+(end-start).toFixed(2)});opened=null;}
 }
 return {duration_s:dur,frames:frame,pauses,threshold,hop_s:hop/sr,reference_rms:max};
}
function markedToken(word){return word.toLowerCase().replace(/[^a-z]/g,'');}
function fillerCount(s){return(s.match(/\b(um+|uh+|erm+|er+|ah+|hmm+)\b/gi)||[]).length;}
function computeBursts(words){if(words.length<6)return[];let out=[],lastEnd=-10;
 for(let i=0;i<words.length;i++){
  const start=Number(words[i].start);if(start<lastEnd+1)continue;
  let j=i;while(j<words.length&&words[j].end-start<8)j++;
  if(j-i<8)continue;
  const elapsed=(words[j-1].end-start)||1,rate=(j-i)*60/elapsed;
  if(elapsed>=3&&rate>=190){out.push({start:+start.toFixed(2),end:+words[j-1].end.toFixed(2),wpm:Math.round(rate)});lastEnd=words[j-1].end;}
  if(out.length>=5)break;
 }
 return out;
}
function repaint(){if(!acoustic)return;const c=$('wave'),dpr=window.devicePixelRatio||1,w=c.clientWidth||700,h=140;c.width=Math.ceil(w*dpr);c.height=Math.ceil(h*dpr);const g=c.getContext('2d');g.scale(dpr,dpr);g.fillStyle='#091e2a';g.fillRect(0,0,w,h);for(const e of acoustic.pauses){g.fillStyle='#fabc6a40';g.fillRect(e.start/acoustic.duration_s*w,0,(e.end-e.start)/acoustic.duration_s*w,h);}const bins=acoustic.frames,max=Math.max(.0001,...bins),count=Math.min(Math.floor(w*1.2),bins.length);g.fillStyle='#69e5b9';for(let i=0;i<count;i++){const v=bins[Math.floor(i*bins.length/count)],bar=Math.max(2,(v/max)*(h-20));g.fillRect(i*w/count,h-bar,Math.max(1,w/count),bar);}}
function displayEvidence(transcript,words){
 const n=Number(acoustic.duration_s),count=fillerCount(transcript),total=(transcript.match(/\b[\w'-]+\b/g)||[]).length,rate=Math.round(total*60/n),bursts=computeBursts(words),ev=[];
 $('metrics').innerHTML=[['Duration',secs(n)],['Potential fillers',String(count)],['Quiet intervals',String(acoustic.pauses.length)],['Average WPM',total?String(rate):'—']].map(([k,v])=>`<div class="metric"><b>${v}</b><span>${k}</span></div>`).join('');
 let highlighted='';if(words?.length&&transcript===lastTranscript){highlighted=words.map(w=>{const cls=FILLER.has(markedToken(w.word))?'word filler':'word';return `<span class="${cls}" data-time="${Number(w.start)||0}" title="Replay ${Number(w.start).toFixed(1)}s">${html(w.word)} </span>`}).join('');}else{highlighted=html(transcript).replace(/\b(um+|uh+|erm+|er+|ah+|hmm+)\b/gi,s=>`<mark style="background:#7b572d;color:#ffe6a0;border-radius:4px">${s}</mark>`);}
 $('highlighted').innerHTML=highlighted||'<span class="muted">A transcript is needed for text analysis.</span>';
 $('highlighted').querySelectorAll('[data-time]').forEach(el=>el.onclick=()=>playAt(Number(el.dataset.time)));
 for(const p of acoustic.pauses.slice(0,5))ev.push({title:`Quiet interval · ${p.length_s}s`,note:'Candidate low-energy interval; replay before interpreting it. This is not a speaking mistake.',start:p.start});
 for(const b of bursts)ev.push({title:`Possible rushed stretch · ${b.wpm} WPM`,note:'Locally fast word timing. Replay for clarity; not necessarily an error.',start:b.start});
 if(count)ev.unshift({title:`${count} potential hesitation word(s)`,note:'These are based on the transcript, which may omit some fillers.',start:null});
 $('events').innerHTML=ev.length?ev.map(e=>`<div class="event"><h4>${html(e.title)}</h4><p>${html(e.note)}</p>${e.start===null?'':`<button class="seek" data-time="${e.start}">▶ ${secs(e.start)}</button>`}</div>`).join(''):'<p class="muted small">No basic flags found. This does not mean the presentation is perfect.</p>';
 $('events').querySelectorAll('[data-time]').forEach(el=>el.onclick=()=>playAt(Number(el.dataset.time)));
 $('report').classList.remove('hidden');$('review').disabled=false;requestAnimationFrame(repaint);
 return {duration_s:Math.round(n*100)/100,overall_wpm:total?rate:null,fillers:count,pauses:acoustic.pauses,fast_stretches:bursts,relative_energy_summary:{reference_rms:acoustic.reference_rms,method:'RMS amplitude sampled across original recording; not emotion or confidence'}};
}
function lightCleanup(s){return s.replace(/(^|[\s,])(um+|uh+|erm+|er+|ah+|hmm+)\b[\s,]*/gi,' ').replace(/\s+/g,' ').replace(/\s+([,.!?;:])/g,'$1').trim().replace(/^./,m=>m.toUpperCase());}
function headers(){return {};}

async function makeWavFallback(){
 const C=window.AudioContext||window.webkitAudioContext,ctx=new C();let decoded;
 try{decoded=await ctx.decodeAudioData(await audioBlob.arrayBuffer());}finally{await ctx.close();}
 const sr=16000,samples=Math.round(decoded.duration*sr);
 if(samples*2+44>3800000)throw Error('This recording is too long for WAV recovery. Save the audio and retry with a shorter section.');
 const buffer=new ArrayBuffer(44+samples*2),view=new DataView(buffer);
 const put=(offset,text)=>{for(let i=0;i<text.length;i++)view.setUint8(offset+i,text.charCodeAt(i))};
 put(0,'RIFF');view.setUint32(4,36+samples*2,true);put(8,'WAVE');put(12,'fmt ');view.setUint32(16,16,true);
 view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,sr,true);view.setUint32(28,sr*2,true);
 view.setUint16(32,2,true);view.setUint16(34,16,true);put(36,'data');view.setUint32(40,samples*2,true);
 const ch=Array.from({length:decoded.numberOfChannels},(_,i)=>decoded.getChannelData(i));
 for(let i=0;i<samples;i++){const at=Math.min(decoded.length-1,i*decoded.sampleRate/sr),k=Math.floor(at),j=Math.min(k+1,decoded.length-1),t=at-k;
  let value=0;for(const a of ch)value+=((a[k]*(1-t))+(a[j]*t))/ch.length;
  const v=Math.max(-1,Math.min(1,value));view.setInt16(44+i*2,v<0?v*32768:v*32767,true);}
 return new Blob([buffer],{type:'audio/wav'});
}
async function requestTranscript(payload,mime,mode){
 const response=await fetchWithTimeout('/api/transcribe',{method:'POST',headers:{...headers(),'Content-Type':mime,'x-speechtrace-timing':mode},body:payload},55000);
 const data=await response.json().catch(()=>({error:'The server returned unreadable data.',code:'BAD_RESPONSE'}));
 if(!response.ok){const e=new Error(data.error||'Transcription failed.');e.code=data.code;e.http=response.status;throw e;}
 return data;
}
async function checkConnection(){
 const el=$('connectionResult');el.textContent='Checking the Groq API key and model access…';
 try{const r=await fetchWithTimeout('/api/connection',{method:'GET',headers:headers()},16000);
 const d=await r.json();el.textContent=(d.connected?'Connected. ':'Not connected. ')+(d.message||d.error||'No status returned.');
 el.style.color=d.connected&&d.asr_available?'#94ebbe':'#ffbac0';
 }catch(e){el.textContent='Connection test failed. '+(e.name==='AbortError'?'Timed out.':e.message);el.style.color='#ffbac0';}
}
$('checkConnection').onclick=checkConnection;

async function run(){
 if(busy||!audioBlob)return;
 busy=true;$('run').disabled=true;$('retry').disabled=true;$('review').disabled=true;let transcriptionFailed=false;let transcript=$('transcript').value.trim(),words=[];const voiceConsent=$('voiceConsent').checked,coachConsent=$('coachConsent').checked;report={};
 try{
  phase('Analyzing your vocal delivery','Measuring silence and relative energy from the original audio on this device.');
  const acousticTask=captureAcoustics();
  if(audioBlob.size>3800000)message('Long recording: the free API has a 3.8 MB upload limit; local audio analysis still works.',true);
  if(!voiceConsent&&!transcript)message('Only audio evidence is available. Tick recording consent for a transcript, or add the words manually.');
  if(voiceConsent&&!transcript){
   if(audioBlob.size>3800000){message('Audio is too large for the free-tier upload. Local energy and pause analysis will still run.',true);}
   else{
    phase('Transcribing with open-weight Whisper','Free-tier inference in progress; your recording remains saved.');
    try{
     let d;
     try{d=await requestTranscript(audioBlob,contentType(),$('timingMode').value);}
     catch(firstError){
      if(['AUDIO_REJECTED','BAD_AUDIO_REQUEST','AUDIO_FORMAT'].includes(firstError.code)){
       phase('Trying a compatible WAV conversion','Converting locally to 16 kHz WAV and preserving your original audio.');
       const wav=await makeWavFallback();
       d=await requestTranscript(wav,'audio/wav','fast');
       message('Your original recording format was rejected; the compatible WAV retry worked. Verify the transcript.');
      }else throw firstError;
     }
     transcript=String(d.transcript||'').trim();
     if(!transcript)throw Error('No speech recognized; try clearer audio.');
     wordTimes=Array.isArray(d.words)?d.words:[];lastTranscript=transcript;$('transcript').value=transcript;
     $('provider').textContent='Whisper turbo · '+(Number(d.transcription_ms||0)/1000).toFixed(1)+'s';
     message('Transcript ready. Check proper names and missing fillers before reviewing.');
    }catch(e){
     transcriptionFailed=true;message('Transcription failed'+(e.code?' ['+e.code+']':'')+': '+(e.name==='AbortError'?'Timed out.':e.message)+' Your original recording remains saved in this tab. Check AI connection, then Retry transcription; you do not need to record again.',true);
     transcript=$('transcript').value.trim();wordTimes=[];$('provider').textContent='Transcript unavailable';
    }
   }
  }else{if(transcript!==lastTranscript)wordTimes=[];lastTranscript=transcript;$('provider').textContent=transcript?'Verified/edited transcript':'Audio evidence only';}
  acoustic=await acousticTask;
  if(acoustic.duration_s<2||acoustic.duration_s>305)throw Error('Please record between 2 seconds and 5 minutes.');
  phase('Mapping delivery evidence','Aligning words, potential hesitation terms, quiet intervals and local fast stretches.');
  const evidence=displayEvidence(transcript,wordTimes);
  report={version:'0.9',transcript,words:wordTimes,evidence,goal:$('goal').value,observed_at:new Date().toISOString()};
  $('v1').textContent=lightCleanup(transcript)||'Transcript required.';
  $('v2').textContent='AI coaching needs the Groq open-weight model and your separate consent.';
  $('coachCards').innerHTML='';
  if(coachConsent&&transcript){
   phase('Preparing your AI coaching','The text model reviews speech structure, measured events and the meaning of your words.');
   const resp=await fetchWithTimeout('/api/coach',{method:'POST',headers:{...headers(),'Content-Type':'application/json'},body:JSON.stringify({goal:$('goal').value,transcript,words:wordTimes.slice(0,1300),duration_s:evidence.duration_s,acoustics:evidence})},55000);
   const out=await resp.json().catch(()=>({error:'The coaching API response was unreadable.'}));
   if(!resp.ok){$('coachStatus').textContent=out.error||'AI coach unavailable. You can still review the transcript and acoustic evidence.';$('coachStatus').classList.add('error');report.coaching_error=out.error;}
   else{$('coachStatus').classList.remove('error');$('coachStatus').textContent=out.summary||'AI feedback ready';$('v1').textContent=out.version1||lightCleanup(transcript);$('v2').textContent=out.version2||'';report.coaching=out;
    $('coachCards').innerHTML=(out.moments||[]).slice(0,6).map(m=>`<div class="coach-card"><b>${html(m.quote||'Moment to review')}</b><p>${html(m.observation||'')}</p><p><strong>Try:</strong> ${html(m.suggestion||'')}</p>${typeof m.start_s==='number'?`<button class="seek" data-time="${m.start_s}">▶ ${secs(m.start_s)}</button>`:''}</div>`).join('');
    $('coachCards').querySelectorAll('[data-time]').forEach(el=>el.onclick=()=>playAt(Number(el.dataset.time)));
   }
  }else{$('coachStatus').classList.remove('error');$('coachStatus').textContent=coachConsent?'Provide a transcript to request AI feedback.':'AI coaching not requested. Tick the second consent box to receive model-generated coaching.';}
  status(transcriptionFailed?'Audio-only review ready. Transcription failed; you can retry the same recording.':'Review ready. Tap highlighted words or pause markers to replay them.',transcriptionFailed?'error':'');$('report').scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){message((e.name==='AbortError'?'Processing timed out. Please retry.':e.message||'An error occurred.'),true);status('Your recording is still available to replay and save.','error');if(acoustic&&transcript){const evidence=displayEvidence(transcript,wordTimes);report={version:'0.9',transcript,words:wordTimes,evidence};$('v1').textContent=lightCleanup(transcript);$('coachStatus').textContent='Partial report: API processing did not complete.';}}finally{busy=false;endPhase();$('run').disabled=!audioBlob;$('retry').disabled=!audioBlob;$('review').disabled=!acoustic;$('coachAgain').disabled=!acoustic;}
}
$('run').onclick=run;$('retry').onclick=()=>{$('transcript').value='';wordTimes=[];run();};$('coachAgain').onclick=run;
$('transcript').addEventListener('input',()=>{if(!report?.evidence)return;delete report.coaching;$('coachCards').innerHTML='';$('v2').textContent='Transcript changed. Refresh the evidence and request new coaching for this text.';$('coachStatus').textContent='Earlier AI advice was cleared because you edited the transcript.';});
$('review').onclick=()=>{if(!acoustic)return;const changed=$('transcript').value.trim()!==lastTranscript;const s=$('transcript').value.trim();const e=displayEvidence(s,changed?[]:wordTimes);if(changed){message('You edited the transcript. Word timings are now hidden because they may no longer align with your recording.');}report={...report,transcript:s,words:changed?[]:wordTimes,evidence:e};delete report.coaching;$('coachCards').innerHTML='';$('v1').textContent=lightCleanup(s);};
$('download').onclick=()=>{if(!report)return;const u=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='speechtrace-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),900);};
$('copy').onclick=()=>{navigator.clipboard?.writeText($('v2').textContent||$('v1').textContent).then(()=>status('Pitch text copied.')).catch(()=>status('Select the revised pitch to copy it.'));};
window.addEventListener('resize',()=>{if(acoustic)requestAnimationFrame(repaint);});
fetch('/api/status').then(r=>r.json()).then(d=>{if(!d.fast_asr_configured)message('Open-weight transcription requires the free Groq grok_api in Vercel. You can still record and replay audio.');else if(!d.ai_coach_configured)message('Fast transcription is configured, but AI coaching uses the same Groq key.');}).catch(()=>message('Service status could not be checked. The recording feature still works.'));