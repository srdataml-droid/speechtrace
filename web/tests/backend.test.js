import test from 'node:test';
import assert from 'node:assert/strict';
import transcribe from '../api/transcribe.js';
import coach from '../api/coach.js';
import status from '../api/status.js';
function res(){return {statusCode:200,payload:null,headers:{},setHeader(k,v){this.headers[k]=v;return this;},status(n){this.statusCode=n;return this;},json(v){this.payload=v;return this;}}}
function req(method,body,headers={}){const x={method,headers,body};if(Buffer.isBuffer(body))x[Symbol.asyncIterator]=async function*(){yield body};return x;}
function setting(key,value){const old=process.env[key];if(value===undefined)delete process.env[key];else process.env[key]=value;return()=>old===undefined?delete process.env[key]:process.env[key]=old;}
test('missing free model key is correctly reported',async()=>{const restore=setting('GROQ_API_KEY',undefined),r=res();status(req('GET'),r);assert.equal(r.payload.fast_asr_configured,false);assert.equal(r.payload.ai_coach_configured,false);await transcribe(req('POST',Buffer.alloc(900),{'content-type':'audio/webm'}),r);assert.equal(r.payload.code,'KEY_MISSING');restore();});
test('public judge access does not demand an access code',async()=>{const a=setting('GROQ_API_KEY','dummy'),b=setting('SPEECHTRACE_ACCESS_CODE',undefined),old=globalThis.fetch,r=res();try{globalThis.fetch=async()=>({ok:true,json:async()=>({text:'Hello judges.',duration:2,segments:[]})});await transcribe(req('POST',Buffer.alloc(900),{'content-type':'audio/webm'}),r);assert.equal(r.statusCode,200);}finally{a();b();globalThis.fetch=old;}});
test('cross-origin browser API request is rejected',async()=>{const a=setting('GROQ_API_KEY','dummy'),r=res();await transcribe(req('POST',Buffer.alloc(900),{'content-type':'audio/webm','origin':'https://untrusted.example'}),r);assert.equal(r.statusCode,403);assert.equal(r.payload.code,'ORIGIN_DENIED');a();});
test('multipart Whisper request normalizes word and segment timing',async()=>{const a=setting('GROQ_API_KEY','dummy'),b=setting('SPEECHTRACE_ACCESS_CODE','secret'),old=globalThis.fetch;
try{globalThis.fetch=async(url,opts)=>{assert.match(url,/api.groq.com\/openai\/v1\/audio\/transcriptions/);assert.equal(opts.headers.Authorization,'Bearer dummy');assert.equal(opts.body.get('model'),'whisper-large-v3-turbo');assert.deepEqual(opts.body.getAll('timestamp_granularities[]'),['word','segment']);return {ok:true,json:async()=>({text:'Um, this helps students.',duration:2,words:[{word:'Um,',start:.1,end:.4}],segments:[{start:0,end:2,text:'Um, this helps students.'}]})};};
const r=res();await transcribe(req('POST',Buffer.alloc(1000),{'content-type':'audio/webm','x-speechtrace-code':'secret','x-speechtrace-timing':'detailed'}),r);assert.equal(r.statusCode,200);assert.equal(r.payload.words[0].start,.1);assert.equal(r.payload.provider,'groq');}finally{globalThis.fetch=old;a();b();}});
test('free Whisper quota failure returns 429',async()=>{const a=setting('GROQ_API_KEY','dummy'),b=setting('SPEECHTRACE_ACCESS_CODE','secret'),old=globalThis.fetch;
try{globalThis.fetch=async()=>({ok:false,status:429,json:async()=>({})});const r=res();await transcribe(req('POST',Buffer.alloc(1000),{'content-type':'audio/webm','x-speechtrace-code':'secret'}),r);assert.equal(r.statusCode,429);assert.equal(r.payload.code,'FREE_TIER_LIMIT');}finally{globalThis.fetch=old;a();b();}});
test('Qwen JSON coaching validates quote and uses actual word timing instead of invented time',async()=>{const a=setting('GROQ_API_KEY','dummy'),b=setting('SPEECHTRACE_ACCESS_CODE','secret'),old=globalThis.fetch;
try{globalThis.fetch=async(url,opts)=>{assert.match(url,/api.groq.com\/openai\/v1\/chat\/completions/);const body=JSON.parse(opts.body);assert.equal(body.model,'qwen/qwen3.8-27b');assert.equal(body.response_format.type,'json_object');return {ok:true,json:async()=>({choices:[{message:{content:JSON.stringify({summary:'Good opening',moments:[{quote:'our pitch',observation:'Clear',suggestion:'Add an example',start_s:99,end_s:100,evidence:'transcript'}],version1:'Our pitch works.',version2:'Our pitch solves this problem.',practice_steps:[],strengths:['Direct']})}}]})};};const r=res();await coach(req('POST',{transcript:'Our pitch works.',duration_s:3,words:[{word:'Our',start:.2,end:.4},{word:'pitch',start:.41,end:.61},{word:'works',start:.62,end:1}]},{'x-speechtrace-code':'secret'}),r);assert.equal(r.statusCode,200);assert.equal(r.payload.moments[0].start_s,.2);assert.equal(r.payload.version2,'Our pitch solves this problem.');}finally{globalThis.fetch=old;a();b();}});
test('no Groq key cannot generate coach response',async()=>{const a=setting('GROQ_API_KEY',undefined),r=res();await coach(req('POST',{transcript:'our demo'}),r);assert.equal(r.payload.code,'KEY_MISSING');a();});
test('status never exposes a secret key',()=>{const a=setting('GROQ_API_KEY','secret-xyz'),r=res();status(req('GET'),r);assert.equal(JSON.stringify(r.payload).includes('secret-xyz'),false);a();});

test('fast transcription avoids extra word alignment request',async()=>{
 const a=setting('GROQ_API_KEY','dummy'),b=setting('SPEECHTRACE_ACCESS_CODE','secret'),oldFetch=globalThis.fetch;
 try {
  globalThis.fetch=async(url,opts)=>{
   assert.deepEqual(opts.body.getAll('timestamp_granularities[]'),['segment']);
   return {ok:true,json:async()=>({text:'Hello judges, here is the problem.',duration:3,segments:[{start:0,end:3,text:'Hello judges, here is the problem.'}]})};
  };
  const r=res();await transcribe(req('POST',Buffer.alloc(1000),{'content-type':'audio/webm','x-speechtrace-code':'secret'}),r);
  assert.equal(r.statusCode,200);assert.equal(r.payload.timing_mode,'fast');
  assert.deepEqual(r.payload.words,[]);
 } finally{globalThis.fetch=oldFetch;a();b();}
});
