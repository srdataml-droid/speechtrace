import {send,getGroqKey} from '../lib/shared.js';
export default function handler(req,res){
 if(req.method!=='GET')return send(res,405,{error:'Method not allowed'});
 const configured=!!getGroqKey(),hasGate=!!process.env.SPEECHTRACE_ACCESS_CODE;
 return send(res,200,{version:'0.9',fast_asr_configured:configured,ai_coach_configured:configured,access_code_required:hasGate,access_setup_required:configured&&!hasGate,asr_model:process.env.GROQ_ASR_MODEL||'whisper-large-v3-turbo',coach_model:process.env.GROQ_COACH_MODEL||'qwen/qwen3.8-27b',service:'Groq free-tier inference; quotas apply'});
}