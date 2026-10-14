"""Reproduce limited, controlled-unit evaluation. Not a public speaking benchmark."""
import json
from pathlib import Path
from src.analysis import load_audio,analyze_pair,evaluate_intervals
ROOT=Path(__file__).resolve().parent
labels=json.loads((ROOT/'data/labels.json').read_text())
ref=load_audio(str(ROOT/labels['reference']))
results=[]
for entry in labels['examples']:
    attempt=load_audio(str(ROOT/entry['path']))
    result=analyze_pair(ref,attempt)
    for detected in result['events']:
        detected.pop('suggestion',None)
    row={'clip_id':entry['id'],'predictions':result['events'],'metrics':result['metrics']}
    if entry['id']=='extra_pause':
        row['temporal_evaluation']=evaluate_intervals(result['events'],entry['events'])
    results.append(row)
out=ROOT/'data'/'evaluation_results.json'
out.write_text(json.dumps(results,indent=2)+'\n')
for item in results:
    print(item['clip_id'],[e['type'] for e in item['predictions']],item.get('temporal_evaluation',''))
print('Wrote',out)
