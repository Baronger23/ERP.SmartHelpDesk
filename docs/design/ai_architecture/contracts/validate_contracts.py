"""Offline specification conformance checker; no ERP/LLM/network calls.

The reference protocol model validates contract vectors, not a deployed adapter.
Real transaction, race, identity and durable-worker tests remain integration gates.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import sys
import jsonschema
import rfc8785

ROOT=Path(__file__).resolve().parent
FORMAT=jsonschema.FormatChecker()


def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def hashed(binding): return sha256(rfc8785.dumps(binding)).hexdigest()


def validator(path):
    filename,_,fragment=path.partition('#')
    schema=read(filename)
    if fragment:
        schema={'$schema':schema['$schema'],'$defs':schema['$defs'],'$ref':'#'+fragment}
    return jsonschema.Draft202012Validator(schema,format_checker=FORMAT)


def valid(path,value): return not list(validator(path).iter_errors(value))


def valid_plan(plan):
    if not valid('schemas/plan.schema.json',plan): return False
    steps={s['step_id']:s for s in plan['steps']}
    if len(steps)!=len(plan['steps']): return False
    if any(d not in steps for s in steps.values() for d in s['depends_on']): return False
    active,done=set(),set()
    def visit(key):
        if key in active: return False
        if key in done: return True
        active.add(key)
        if not all(visit(d) for d in steps[key]['depends_on']): return False
        active.remove(key);done.add(key);return True
    return all(visit(k) for k in steps)


class ProtocolModel:
    """Single-threaded contract example, deliberately not an ERP implementation."""
    def __init__(self,examples,tools):
        self.examples=deepcopy(examples);self.tools=tools
        self.binding=deepcopy(examples['binding']);self.approval=deepcopy(examples['approval'])
        self.scope=deepcopy(self.approval['scope']);self.versions=deepcopy(self.binding['expected_versions'])
        self.policy=self.binding['policy_version'];self.now=datetime.fromisoformat('2026-10-08T11:00:00+07:00')
        self.key='run-demo-001:step-commit-draft:proposal-1'
        self.receipts={};self.cancelled=False;self.consumed=False;self.effects=0
        self.events=set();self.resume_count=0;self.stock_observations=[];self.trace=[];self.outcome=None

    def commit(self):
        if not valid('schemas/command_binding.schema.json',self.binding): return 'SCHEMA_INVALID'
        if any(self.scope[k]!=self.binding[k] for k in self.scope): return 'SCOPE_DENIED'
        h=hashed(self.binding)
        if self.key in self.receipts:
            return 'APPLIED' if self.receipts[self.key]['binding_hash']==h else 'IDEMPOTENCY_CONFLICT'
        if self.cancelled: return 'CANCELLED'
        if self.approval['scope']!=self.scope or self.approval['proposal_id']!=self.binding['proposal_id'] or self.approval['run_id']!=self.binding['run_id']: return 'APPROVAL_SCOPE_MISMATCH'
        if self.approval['binding_hash']!=h: return 'HASH_MISMATCH'
        if self.approval['decision']!='APPROVED': return self.approval['decision']
        if datetime.fromisoformat(self.approval['expires_at'])<=self.now: return 'EXPIRED'
        if self.policy!=self.binding['policy_version'] or self.versions!=self.binding['expected_versions']: return 'STALE_APPROVAL'
        if self.consumed: return 'APPROVAL_CONSUMED'
        if Decimal(self.binding['payload']['quantity'])<=0: return 'INVALID_QUANTITY'
        # One modeled atomic unit; actual ERP atomicity/concurrency is not tested here.
        self.effects+=1;self.consumed=True
        self.receipts[self.key]={'command_state':'APPLIED','command_id':'command-demo-1','idempotency_key':self.key,'binding_hash':h,'effect_count':1,'document_id':'draft-demo-1','docstatus':0}
        return 'APPLIED'

    def action(self,a):
        op=a['op']
        if op in {'commit','commit_timeout'}:
            result=self.commit()
            self.outcome='OUTCOME_UNKNOWN' if op=='commit_timeout' and result=='APPLIED' else result
        elif op=='lookup':
            receipt=self.receipts.get(self.key)
            if any(self.scope[k]!=self.binding[k] for k in self.scope): self.outcome='SCOPE_DENIED'
            else: self.outcome='APPLIED' if receipt and receipt['binding_hash']==hashed(self.binding) else 'NOT_FOUND'
        elif op=='lose_receipt': self.outcome='OUTCOME_UNKNOWN'
        elif op=='change_payload': self.binding['payload'][a['key']]=a['value']
        elif op=='change_version': self.versions[a['key']]=a['value']
        elif op=='change_scope': self.scope[a['key']]=a['value']
        elif op=='change_approval_scope': self.approval['scope'][a['key']]=a['value']
        elif op=='change_policy': self.policy=a['value']
        elif op=='advance_time': self.now=datetime.fromisoformat(a['value'])
        elif op=='approval_decision': self.approval['decision']=a['value']
        elif op=='cancel': self.cancelled=True
        elif op=='resume':
            event=deepcopy(self.examples['resume_event']);event['source_verified']=a.get('source_verified',True)
            event['checkpoint_version']=a.get('checkpoint_version',event['checkpoint_version'])
            event['approval_id']=a.get('approval_id',event['approval_id'])
            if not valid('schemas/resume_event.schema.json',event) or not event['source_verified']: self.outcome='UNVERIFIED_EVENT'
            elif event['checkpoint_version']!=self.examples['checkpoint']['state_version'] or event['approval_id']!=self.approval['approval_id']: self.outcome='STALE_RESUME'
            else:
                if event['event_id'] not in self.events:
                    self.events.add(event['event_id']);self.resume_count+=1
                self.outcome='RESUMED_ONCE' if self.resume_count==1 else 'DUPLICATE_TRANSITION'
        elif op=='stock_timeout':
            observation=deepcopy(self.examples['stock_timeout'])
            if not valid(self.tools['get_available_stock']['output_schema'],observation): raise AssertionError('Invalid stock error envelope')
            self.stock_observations.append(observation)
        elif op=='classify_stock_observations':
            self.outcome='PARTIAL_NO_SHORTAGE' if self.stock_observations and all(o['status']=='error' and 'data' not in o for o in self.stock_observations) else 'INVALID_OBSERVATION'
        elif op=='validate_input': self.outcome='VALID_INPUT' if valid(self.tools[a['tool']]['input_schema'],a['arguments']) else 'SCHEMA_INVALID'
        elif op=='validate_plan':
            plan=deepcopy(self.examples['plan'])
            if a.get('create_cycle'): plan['steps'][0]['depends_on']=['stock']
            self.outcome='VALID_PLAN' if valid_plan(plan) else 'INVALID_PLAN'
        elif op=='validate_resume_budget':
            run=deepcopy(self.examples['run']);run['counters']['tool_attempts']=a['tool_attempts']
            original=deepcopy(run['counters']);run['counters']['resumes']+=1
            assert run['counters']['tool_attempts']==original['tool_attempts']
            self.outcome='BUDGET_EXHAUSTED' if any(run['counters'][k]>=run['limits'][k] for k in run['limits']) else 'WITHIN_BUDGET'
        elif op=='verify_evidence': self.outcome='EVIDENCE_ELIGIBLE' if a['eligible'] else 'EVIDENCE_INELIGIBLE'
        elif op=='verify_compatibility': self.outcome='VERIFIED_COMPATIBILITY' if a['value']=='VERIFIED' else 'COMPATIBILITY_CONFLICT'
        else: raise AssertionError(f'Unknown fixture operation {op}')
        self.trace.append({'operation':op,'outcome':self.outcome,'effect_count':self.effects})


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    registry=read('tool_registry.json');examples=read('examples.json');fixtures=read('fixtures.json')
    schemas=list((ROOT/'schemas').glob('*.json'))
    for p in schemas: jsonschema.Draft202012Validator.check_schema(json.loads(p.read_text(encoding='utf-8')))
    tools={t['name']:t for t in registry['tools']}
    assert len(tools)==len(registry['tools'])
    for t in tools.values():
        validator(t['input_schema']);validator(t['output_schema'])
        assert t['identity_source']=='TRUSTED_GATEWAY_CONTEXT'
        assert t['effect'] not in registry['baseline_forbidden_effects']
        if t['effect']=='WRITE_DRAFT':
            assert t['idempotency_required'] and t['max_attempts']==1 and 'get_command_outcome' in tools
    pairs=[('schemas/command_binding.schema.json','binding'),('schemas/approval.schema.json','approval'),('schemas/agent_run.schema.json','run'),('schemas/plan.schema.json','plan'),('schemas/resume_event.schema.json','resume_event'),(tools['get_available_stock']['output_schema'],'stock_ok'),(tools['get_available_stock']['output_schema'],'stock_timeout')]
    pairs.extend([('schemas/agent_definition.schema.json','definition'),('schemas/agent_step.schema.json','step'),('schemas/checkpoint.schema.json','checkpoint'),('schemas/evidence.schema.json','evidence')])
    for path,key in pairs: assert valid(path,examples[key]), f'Invalid positive example: {key}'
    assert valid_plan(examples['plan'])
    assert examples['approval']['binding_hash']==hashed(examples['binding'])
    negatives=[]
    malformed=deepcopy(examples['stock_timeout']);malformed['data']={'available_qty':'0.000'}
    negatives.append((tools['get_available_stock']['output_schema'],malformed))
    malformed=deepcopy(examples['approval']);malformed['binding_hash']='invalid'
    negatives.append(('schemas/approval.schema.json',malformed))
    malformed=deepcopy(examples['run']);malformed['counters']['tokens']=-1
    negatives.append(('schemas/agent_run.schema.json',malformed))
    malformed=deepcopy(examples['binding']);malformed['payload']['ignore_permissions']=True
    negatives.append(('schemas/command_binding.schema.json',malformed))
    malformed=deepcopy(examples['step']);malformed['command_key']=None
    negatives.append(('schemas/agent_step.schema.json',malformed))
    malformed=deepcopy(examples['checkpoint']);malformed['resume_condition']={'kind':'INPUT','input_request_id':'input-demo'}
    negatives.append(('schemas/checkpoint.schema.json',malformed))
    for path,value in negatives: assert not valid(path,value), f'Negative accepted: {path}'
    results=[]
    for f in fixtures['protocol_vectors']:
        model=ProtocolModel(examples,tools)
        for a in f['actions']: model.action(a)
        actual={'outcome':model.outcome,'business_effect_count':model.effects}
        if model.receipts:
            receipt=next(iter(model.receipts.values()))
            ok={'tool_version':'1.0.0','status':'ok','observed_at':'2026-10-08T11:00:00+07:00','source_version':'draft-v1','data':receipt,'evidence_refs':['receipt-demo-1']}
            assert valid(tools['commit_approved_proposal']['output_schema'],ok)
        passed=actual==f['expected']
        results.append({'case_id':f['case_id'],'covers':f['covers'],'passed':passed,'expected':f['expected'],'actual':actual,'trace':model.trace})
    report={'scope':'offline_contract_conformance','synthetic':True,'schema_count':len(schemas),'registry_tools':len(tools),'positive_examples':len(pairs),'negative_examples':len(negatives),'protocol_vectors':len(results),'passed_vectors':sum(r['passed'] for r in results),'runtime_integration_tested':False,'llm_or_erp_called':False,'results':results}
    covered={test for result in results for test in result['covers']}
    report['covered_oracle_references']=sorted(covered)
    report['not_exercised_oracle_references']=sorted({f'HT-{i:02}' for i in range(1,25)}-covered)
    report['not_tested']=['ERP database transaction/locks/concurrency','Real authentication/permissions/files','Durable worker CAS/lease/webhook delivery','LLM task success and prompt injection','Real retrieval quality/freshness','KPI late-event consumer']
    (ROOT/'conformance_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert all(r['passed'] for r in results),[r for r in results if not r['passed']]
    print(f'PASS: {len(schemas)} schemas, {len(tools)} tools, {len(pairs)} positive + {len(negatives)} negative examples, {len(results)} protocol vectors.')
    print('Scope: offline specification conformance only; ERP/LLM/runtime integration not tested.')


if __name__=='__main__': main()
