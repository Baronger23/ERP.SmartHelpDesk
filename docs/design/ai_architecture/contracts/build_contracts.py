"""Build design schemas, registry, examples and offline protocol vectors.

This generates specification artifacts. It does not deploy an agent or call ERP.
"""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json
import rfc8785

ROOT=Path(__file__).resolve().parent
SCHEMA='https://json-schema.org/draft/2020-12/schema'
ID={'type':'string','minLength':1,'maxLength':128}
VERSION={'type':'string','minLength':1,'maxLength':128}
TIME={'type':'string','format':'date-time'}
HASH={'type':'string','pattern':'^[a-f0-9]{64}$'}
QTY={'type':'string','pattern':'^[0-9]+(\\.[0-9]{1,3})?$'}
STRINGS={'type':'array','items':ID,'uniqueItems':True}


def obj(properties,required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}


def array(item): return {'type':'array','items':item}
def enum(*values): return {'type':'string','enum':list(values)}
def ref(name): return {'$ref':'#/$defs/'+name}
def write(name,value):
    p=ROOT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def hashed(binding): return sha256(rfc8785.dumps(binding)).hexdigest()


def build():
    defs={'id':ID,'quantity':QTY}
    stock=obj({'item_code':ID,'warehouse_id':ID,'actual_qty':QTY,'held_qty':QTY,'available_qty':QTY,'uom':ID})
    evidence=obj({'evidence_id':ID,'document_id':ID,'document_version':VERSION,'page':{'type':'integer','minimum':1},'content_hash':HASH,'support':enum('SUPPORTED','PARTIAL','CONFLICTED'),'eligible':{'type':'boolean'}})
    versions={'type':'object','minProperties':1,'additionalProperties':VERSION}
    receipt=obj({'command_state':{'const':'APPLIED'},'command_id':ID,'idempotency_key':ID,'binding_hash':HASH,'effect_count':{'const':1},'document_id':ID,'docstatus':{'const':0}})
    defs['receipt_data']=receipt
    defs['error_result']=obj({'tool_version':{'const':'1.0.0'},'status':{'const':'error'},'observed_at':TIME,'code':enum('READ_TIMEOUT','RATE_LIMITED','TRANSIENT_FAILURE','RESOURCE_UNAVAILABLE','SCHEMA_INVALID','PERMISSION_DENIED','STALE_APPROVAL','PRECONDITION_FAILED','KNOWLEDGE_CONFLICT','IDEMPOTENCY_CONFLICT','OUTCOME_UNKNOWN'),'category':enum('TRANSIENT','AUTHORIZATION','VALIDATION','PRECONDITION','CONFLICT','UNKNOWN'),'retryable':{'type':'boolean'},'correlation_ref':ID})
    tools=[]

    def tool(name,module,inputs,data,risk='R1',effect='READ',timeout=5000,retries=2,required=None):
        defs[name+'_input']=obj(inputs,required)
        ok=obj({'tool_version':{'const':'1.0.0'},'status':{'const':'ok'},'observed_at':TIME,'source_version':VERSION,'data':data,'evidence_refs':STRINGS})
        defs[name+'_output']={'oneOf':[ok,ref('error_result')]}
        tools.append({'name':name,'version':'1.0.0','module':module,'risk_tier':risk,'effect':effect,'input_schema':'schemas/tool_contracts.schema.json#/$defs/'+name+'_input','output_schema':'schemas/tool_contracts.schema.json#/$defs/'+name+'_output','timeout_ms':timeout,'max_attempts':retries+1,'retry_strategy':'CLASSIFIED_READ' if effect=='READ' else 'RECONCILE_BEFORE_REDISPATCH' if effect=='WRITE_DRAFT' else 'NO_BLIND_RETRY','identity_source':'TRUSTED_GATEWAY_CONTEXT','idempotency_required':effect=='WRITE_DRAFT','baseline_enabled':True})

    tool('resolve_equipment','M04',{'equipment_code':ID},obj({'equipment_id':ID,'equipment_code':ID,'model':ID,'serial':ID,'site_id':ID,'customer_id':ID,'equipment_version':VERSION}))
    tool('get_service_context','M02/M03',{'work_order_id':ID},obj({'work_order_id':ID,'source_id':ID,'origin_kind':enum('INCIDENT','SERVICE_REQUEST','PM_OCCURRENCE'),'equipment_id':ID,'site_id':ID,'versions':versions}))
    tool('get_entitlement_snapshot','M01',{'work_order_id':ID},obj({'snapshot_id':ID,'coverage_version':VERSION,'policy_version':VERSION}))
    visit=obj({'visit_id':ID,'outcome':enum('COMPLETED','INCOMPLETE','CANCELLED'),'occurred_at':TIME,'source_version':VERSION})
    tool('get_work_history','M03',{'equipment_id':ID},obj({'equipment_id':ID,'visits':array(visit)}),timeout=8000)
    tool('search_approved_knowledge','M09',{'query':{'type':'string','minLength':1,'maxLength':2000},'model':ID,'error_code':ID},obj({'catalog_version':VERSION,'index_generation':VERSION,'evidence':array(evidence),'conflict':{'type':'boolean'}}),risk='R0',timeout=8000)
    tool('verify_compatibility','M04/M09',{'equipment_id':ID,'item_code':ID},obj({'equipment_id':ID,'item_code':ID,'compatibility':enum('VERIFIED','UNKNOWN','CONFLICTED'),'compatibility_version':VERSION,'evidence_refs':STRINGS}))
    tool('get_available_stock','M05',{'item_code':ID,'warehouse_id':ID},stock,timeout=3000)
    supply=obj({'order_id':ID,'demand_id':ID,'remaining_qty':QTY,'accepted_qty':QTY,'eta':TIME})
    tool('get_open_supply','M06',{'item_code':ID,'work_order_id':ID},obj({'orders':array(supply)}))
    eligible=obj({'user_id':ID,'skill_refs':STRINGS,'available':{'type':'boolean'},'slot_ref':ID})
    tool('get_eligible_technicians','M03',{'work_order_id':ID},obj({'eligible':array(eligible),'availability_version':VERSION}))
    finding=obj({'finding_id':ID,'occurrence_id':ID,'equipment_id':ID,'owner_id':ID,'severity':enum('LOW','MEDIUM','HIGH','URGENT'),'outcome':enum('OPEN','FOLLOW_UP','INCIDENT','RESOLVED')})
    tool('get_pm_findings','M04',{'pm_occurrence_id':ID},obj({'findings':array(finding)}))
    charge=obj({'charge_id':ID,'amount':{'type':'string','pattern':'^-?[0-9]+(\\.[0-9]{1,3})?$'},'currency':ID,'reconciled':{'type':'boolean'},'source_ref':ID})
    tool('get_charge_reconciliation','M07',{'work_order_id':ID},obj({'coverage_snapshot_id':ID,'charges':array(charge)}))
    risk=obj({'request_id':ID,'reason':ID,'deadline':TIME,'source_event_refs':STRINGS})
    tool('get_operational_risks','M08',{'snapshot_id':ID},obj({'snapshot_id':ID,'formula_version':VERSION,'as_of':TIME,'risks':array(risk)}))
    payload=obj({'work_order_id':ID,'equipment_id':ID,'item_code':ID,'warehouse_id':ID,'quantity':QTY,'uom':ID,'reason_ref':ID})
    kinds=enum('MATERIAL_ALLOCATION_DRAFT','MATERIAL_REQUEST_DRAFT','WORK_ORDER_DRAFT','TRIAGE_RECOMMENDATION','DISPATCH_RECOMMENDATION')
    # Shape of proposal payload depends on target action. Each variant is strict.
    work_payload=obj({'work_source_id':ID,'equipment_id':ID,'package_key':ID,'generation_version':VERSION,'reason_ref':ID})
    triage_payload=obj({'request_id':ID,'recommendation_ref':ID,'reason_ref':ID})
    dispatch_payload=obj({'work_order_id':ID,'eligible_technician_id':ID,'slot_ref':ID,'reason_ref':ID})
    variants=[]
    for kind,domain,p in [('MATERIAL_ALLOCATION_DRAFT','M05',payload),('MATERIAL_REQUEST_DRAFT','M06',payload),('WORK_ORDER_DRAFT','M03',work_payload),('TRIAGE_RECOMMENDATION','M02',triage_payload),('DISPATCH_RECOMMENDATION','M03',dispatch_payload)]:
        variants.append(obj({'command_type':{'const':kind},'target_domain':{'const':domain},'payload':p,'expected_versions':versions,'evidence_refs':STRINGS}))
    defs['prepare_proposal_input']={'oneOf':variants}
    # tool() installs the output; replace its common input with the typed union below.
    tool('prepare_proposal','CONTROL',{},obj({'proposal_id':ID,'binding_hash':HASH,'control_plane_only':{'const':True},'business_effect_count':{'const':0}}),risk='R2',effect='PREPARE',retries=0)
    defs['prepare_proposal_input']={'oneOf':variants}
    tool('commit_approved_proposal','GATEWAY',{'proposal_id':ID,'approval_id':ID,'idempotency_key':ID},ref('receipt_data'),risk='R2',effect='WRITE_DRAFT',timeout=10000,retries=0)
    lookup_data={'oneOf':[obj({'command_state':{'const':'APPLIED'},'receipt':ref('receipt_data')}),obj({'command_state':enum('NOT_FOUND','APPLYING','UNKNOWN'),'command_id':ID})]}
    tool('get_command_outcome','GATEWAY',{'command_id':ID,'idempotency_key':ID,'binding_hash':HASH},lookup_data,timeout=3000)
    write('schemas/tool_contracts.schema.json',{'$schema':SCHEMA,'$defs':defs})
    limits={'steps':12,'tool_attempts':16,'model_turns':6,'tokens':12000,'active_ms':90000,'resumes':3}
    write('tool_registry.json',{'registry_version':'ais-tools-1.0.0','profile':'ais-baseline-v1','limits':limits,'max_in_flight_reads':2,'approval_ttl_seconds':86400,'planning_stock_max_age_seconds':60,'baseline_forbidden_effects':['RESERVE','SUBMIT_STOCK','SUBMIT_PO','SUBMIT_INVOICE','ASSIGN_OVERRIDE','CLOSE_REQUEST'],'tools':tools})
    binding_properties={'proposal_id':ID,'run_id':ID,'command_type':kinds,'target_domain':enum('M02','M03','M05','M06'),'actor_id':ID,'company_id':ID,'customer_id':ID,'site_id':ID,'payload':{},'expected_versions':versions,'policy_version':VERSION,'tool_version':{'const':'1.0.0'},'evidence_refs':STRINGS}
    binding=obj(binding_properties)
    binding['allOf']=[{'if':{'properties':{'command_type':{'const':v['properties']['command_type']['const']}}},'then':{'properties':{'target_domain':v['properties']['target_domain'],'payload':v['properties']['payload']}}} for v in variants]
    write('schemas/command_binding.schema.json',{'$schema':SCHEMA,**binding})
    scope=obj({'actor_id':ID,'company_id':ID,'customer_id':ID,'site_id':ID})
    approval=obj({'approval_id':ID,'proposal_id':ID,'run_id':ID,'binding_hash':HASH,'scope':scope,'approver_id':ID,'policy_version':VERSION,'decision':enum('APPROVED','REJECTED','REVOKED'),'decided_at':TIME,'expires_at':TIME,'expected_versions':versions})
    write('schemas/approval.schema.json',{'$schema':SCHEMA,**approval})
    counts=obj({k:{'type':'integer','minimum':0} for k in limits})
    run=obj({'run_id':ID,'definition_version':VERSION,'instruction_version':VERSION,'registry_version':VERSION,'status':enum('CREATED','RUNNING','WAITING_INPUT','WAITING_APPROVAL','RESUMING','VERIFYING','COMPLETED','PARTIAL','BLOCKED','FAILED','CANCELLED'),'reason_code':{'type':['string','null']},'scope':scope,'state_version':{'type':'integer','minimum':1},'correlation_id':ID,'counters':counts,'limits':counts})
    write('schemas/agent_run.schema.json',{'$schema':SCHEMA,**run})
    step=obj({'step_id':ID,'tool':{'enum':[t['name'] for t in tools]},'depends_on':STRINGS,'success':ID})
    plan=obj({'run_id':ID,'plan_version':{'type':'integer','minimum':1},'goal':{'type':'string','minLength':1},'steps':{'type':'array','minItems':1,'maxItems':12,'items':step}})
    write('schemas/plan.schema.json',{'$schema':SCHEMA,**plan})
    event=obj({'event_id':ID,'run_id':ID,'checkpoint_version':{'type':'integer','minimum':1},'approval_id':ID,'decision_ref':ID,'source_verified':{'type':'boolean'},'received_at':TIME})
    write('schemas/resume_event.schema.json',{'$schema':SCHEMA,**event})
    definition=obj({'definition_id':ID,'definition_version':VERSION,'instruction_version':VERSION,'registry_version':VERSION,'allowed_tools':{'type':'array','minItems':1,'uniqueItems':True,'items':{'enum':[t['name'] for t in tools]}},'model_policy':obj({'policy_version':VERSION,'primary_model':ID,'allowed_models':STRINGS}),'execution_limits':obj({k:{'type':'integer','minimum':1} for k in limits})})
    write('schemas/agent_definition.schema.json',{'$schema':SCHEMA,**definition})
    step_state=obj({'step_id':ID,'run_id':ID,'plan_version':{'type':'integer','minimum':1},'action_type':enum('READ','PREPARE','WRITE_DRAFT','VERIFY'),'tool_name':{'type':['string','null']},'input_ref':ID,'output_ref':{'type':['string','null']},'outcome':enum('PENDING','SUCCESS','ERROR','UNKNOWN'),'attempt_count':{'type':'integer','minimum':0},'evidence_refs':STRINGS,'command_key':{'type':['string','null']}})
    step_state['allOf']=[{'if':{'properties':{'action_type':{'const':'WRITE_DRAFT'}}},'then':{'properties':{'command_key':ID}}},{'if':{'properties':{'action_type':{'const':'VERIFY'}}},'then':{'properties':{'tool_name':{'const':None}}},'else':{'properties':{'tool_name':{'enum':[t['name'] for t in tools]}}}}]
    write('schemas/agent_step.schema.json',{'$schema':SCHEMA,**step_state})
    resume_condition={'oneOf':[obj({'kind':{'const':'APPROVAL_DECISION'},'approval_id':ID}),obj({'kind':{'const':'INPUT'},'input_request_id':ID}),obj({'kind':{'const':'RECOVERY'},'command_ids':STRINGS})]}
    checkpoint=obj({'run_id':ID,'state_version':{'type':'integer','minimum':1},'status':enum('RUNNING','WAITING_INPUT','WAITING_APPROVAL','RESUMING','VERIFYING'),'plan_version':{'type':'integer','minimum':1},'pending_step_ids':STRINGS,'pending_command_keys':STRINGS,'evidence_refs':STRINGS,'counters':counts,'resume_condition':resume_condition})
    checkpoint['allOf']=[{'if':{'properties':{'status':{'const':'WAITING_APPROVAL'}}},'then':{'properties':{'resume_condition':{'properties':{'kind':{'const':'APPROVAL_DECISION'}}}}}}]
    write('schemas/checkpoint.schema.json',{'$schema':SCHEMA,**checkpoint})
    verified_evidence=obj({'evidence_id':ID,'source_type':enum('DOCUMENT','MODULE_OBSERVATION'),'source_id':ID,'source_version':VERSION,'observed_at':TIME,'scope_fingerprint':HASH,'content_hash':HASH,'support':enum('SUPPORTED','PARTIAL','CONFLICTED','UNSUPPORTED'),'eligible':{'type':'boolean'},'permission_epoch':{'type':'integer','minimum':0},'document_page':{'type':['integer','null'],'minimum':1},'catalog_version':{'type':['string','null']}})
    write('schemas/evidence.schema.json',{'$schema':SCHEMA,**verified_evidence})
    binding_example={'proposal_id':'proposal-demo-1','run_id':'run-demo-001','command_type':'MATERIAL_ALLOCATION_DRAFT','target_domain':'M05','actor_id':'user-tech-demo','company_id':'company-ais-demo','customer_id':'customer-demo','site_id':'site-demo','payload':{'work_order_id':'WO-DEMO-1','equipment_id':'AC-102-DEMO','item_code':'PART-DEMO-01','warehouse_id':'WH-DEMO-01','quantity':'1.000','uom':'Nos','reason_ref':'reason-demo-e17'},'expected_versions':{'work_order':'wo-v3','equipment':'eq-v2','compatibility':'compat-v4','stock':'stock-v17'},'policy_version':'policy-v1','tool_version':'1.0.0','evidence_refs':['doc-demo-r1-p4','compat-demo-v4','stock-demo-v17']}
    scope_example={k:binding_example[k] for k in ['actor_id','company_id','customer_id','site_id']}
    approval_example={'approval_id':'approval-demo-1','proposal_id':'proposal-demo-1','run_id':'run-demo-001','binding_hash':hashed(binding_example),'scope':scope_example,'approver_id':'dispatcher-demo','policy_version':'policy-v1','decision':'APPROVED','decided_at':'2026-10-08T09:00:00+07:00','expires_at':'2026-10-09T09:00:00+07:00','expected_versions':deepcopy(binding_example['expected_versions'])}
    run_example={'run_id':'run-demo-001','definition_version':'ais-agent-v1','instruction_version':'instruction-v1','registry_version':'ais-tools-1.0.0','status':'WAITING_APPROVAL','reason_code':None,'scope':scope_example,'state_version':7,'correlation_id':'corr-demo-1','counters':{'steps':6,'tool_attempts':7,'model_turns':3,'tokens':4300,'active_ms':24000,'resumes':0},'limits':limits}
    plan_example={'run_id':'run-demo-001','plan_version':1,'goal':'Resolve demo equipment, gather evidence and prepare a proposal','steps':[{'step_id':'resolve','tool':'resolve_equipment','depends_on':[],'success':'UNAMBIGUOUS_EQUIPMENT'},{'step_id':'sop','tool':'search_approved_knowledge','depends_on':['resolve'],'success':'ELIGIBLE_EVIDENCE'},{'step_id':'stock','tool':'get_available_stock','depends_on':['sop'],'success':'FRESH_STOCK'}]}
    resume_example={'event_id':'decision-demo-1','run_id':'run-demo-001','checkpoint_version':7,'approval_id':'approval-demo-1','decision_ref':'decision-authority-demo-1','source_verified':True,'received_at':'2026-10-08T11:00:00+07:00'}
    common={'tool_version':'1.0.0','status':'ok','observed_at':'2026-10-08T09:00:00+07:00','source_version':'stock-v17','data':{'item_code':'PART-DEMO-01','warehouse_id':'WH-DEMO-01','actual_qty':'2.000','held_qty':'1.000','available_qty':'1.000','uom':'Nos'},'evidence_refs':['stock-demo-v17']}
    timeout={'tool_version':'1.0.0','status':'error','observed_at':'2026-10-08T09:00:03+07:00','code':'READ_TIMEOUT','category':'TRANSIENT','retryable':True,'correlation_ref':'corr-demo-1'}
    examples={'binding':binding_example,'approval':approval_example,'run':run_example,'plan':plan_example,'resume_event':resume_example,'stock_ok':common,'stock_timeout':timeout}
    examples['definition']={'definition_id':'ais-assistant','definition_version':'ais-agent-v1','instruction_version':'instruction-v1','registry_version':'ais-tools-1.0.0','allowed_tools':[t['name'] for t in tools],'model_policy':{'policy_version':'model-policy-demo-1','primary_model':'model-demo-placeholder','allowed_models':['model-demo-placeholder']},'execution_limits':limits}
    examples['step']={'step_id':'step-commit-draft','run_id':'run-demo-001','plan_version':2,'action_type':'WRITE_DRAFT','tool_name':'commit_approved_proposal','input_ref':'proposal-demo-1','output_ref':None,'outcome':'PENDING','attempt_count':0,'evidence_refs':binding_example['evidence_refs'],'command_key':'run-demo-001:step-commit-draft:proposal-1'}
    examples['checkpoint']={'run_id':'run-demo-001','state_version':7,'status':'WAITING_APPROVAL','plan_version':2,'pending_step_ids':['step-commit-draft'],'pending_command_keys':[examples['step']['command_key']],'evidence_refs':binding_example['evidence_refs'],'counters':run_example['counters'],'resume_condition':{'kind':'APPROVAL_DECISION','approval_id':'approval-demo-1'}}
    examples['evidence']={'evidence_id':'doc-demo-r1-p4','source_type':'DOCUMENT','source_id':'doc-demo','source_version':'r1','observed_at':'2026-10-08T09:00:00+07:00','scope_fingerprint':hashed(scope_example),'content_hash':hashed({'synthetic':'approved-demo-text'}),'support':'SUPPORTED','eligible':True,'permission_epoch':1,'document_page':4,'catalog_version':'catalog-demo-1'}
    write('examples.json',examples)
    scenarios=[
        ('valid_commit',['HT-08'],'APPLIED',1),('retry_same',['HT-12','HT-14'],'APPLIED',1),('conflict_key',['HT-14'],'IDEMPOTENCY_CONFLICT',1),
        ('tampered_payload',['HT-09'],'HASH_MISMATCH',0),('stale_object',['HT-09'],'STALE_APPROVAL',0),('expired',['HT-10'],'EXPIRED',0),
        ('rejected',['HT-10'],'REJECTED',0),('scope_changed',['HT-16'],'SCOPE_DENIED',0),('policy_changed',['HT-09'],'STALE_APPROVAL',0),
        ('crash_after_commit',['HT-12'],'APPLIED',1),('write_timeout_unknown',['HT-13'],'APPLIED',1),('cancel_before',['HT-18'],'CANCELLED',0),
        ('cancel_after',['HT-18'],'APPLIED',1),('duplicate_resume',['HT-11'],'RESUMED_ONCE',0),('forged_resume',['HT-10','HT-11'],'UNVERIFIED_EVENT',0),
        ('stock_timeout',['HT-03'],'PARTIAL_NO_SHORTAGE',0),('forged_args',['HT-07'],'SCHEMA_INVALID',0),('plan_cycle',['HT-17'],'INVALID_PLAN',0),
        ('budget_resume',['HT-17'],'BUDGET_EXHAUSTED',0),('revoked_evidence',['HT-06'],'EVIDENCE_INELIGIBLE',0),('compat_conflict',['HT-05'],'COMPATIBILITY_CONFLICT',0),
        ('retry_after_expiry',['HT-08','HT-12'],'APPLIED',1),('stale_resume',['HT-11'],'STALE_RESUME',0),('wrong_approval_resume',['HT-10','HT-11'],'STALE_RESUME',0),
        ('scope_changed_after_commit',['HT-16','HT-23'],'SCOPE_DENIED',1),('approval_scope_mismatch',['HT-09','HT-10'],'APPROVAL_SCOPE_MISMATCH',0),
    ]
    actions={
      'valid_commit':[{'op':'commit'}],
      'retry_same':[{'op':'commit'},{'op':'commit'}],
      'conflict_key':[{'op':'commit'},{'op':'change_payload','key':'quantity','value':'2.000'},{'op':'commit'}],
      'tampered_payload':[{'op':'change_payload','key':'quantity','value':'2.000'},{'op':'commit'}],
      'stale_object':[{'op':'change_version','key':'stock','value':'stock-v18'},{'op':'commit'}],
      'expired':[{'op':'advance_time','value':'2026-10-09T10:00:00+07:00'},{'op':'commit'}],
      'rejected':[{'op':'approval_decision','value':'REJECTED'},{'op':'commit'}],
      'scope_changed':[{'op':'change_scope','key':'customer_id','value':'other-customer'},{'op':'commit'}],
      'policy_changed':[{'op':'change_policy','value':'policy-v2'},{'op':'commit'}],
      'crash_after_commit':[{'op':'commit'},{'op':'lose_receipt'},{'op':'lookup'}],
      'write_timeout_unknown':[{'op':'commit_timeout'},{'op':'lookup'}],
      'cancel_before':[{'op':'cancel'},{'op':'commit'}],
      'cancel_after':[{'op':'commit'},{'op':'cancel'},{'op':'lookup'}],
      'duplicate_resume':[{'op':'resume'},{'op':'resume'}],
      'forged_resume':[{'op':'resume','source_verified':False}],
      'stock_timeout':[{'op':'stock_timeout'},{'op':'stock_timeout'},{'op':'stock_timeout'},{'op':'classify_stock_observations'}],
      'forged_args':[{'op':'validate_input','tool':'get_available_stock','arguments':{'item_code':'PART-DEMO-01','warehouse_id':'WH-DEMO-01','actor_id':'Administrator'}}],
      'plan_cycle':[{'op':'validate_plan','create_cycle':True}],
      'budget_resume':[{'op':'validate_resume_budget','tool_attempts':16}],
      'revoked_evidence':[{'op':'verify_evidence','eligible':False}],
      'compat_conflict':[{'op':'verify_compatibility','value':'CONFLICTED'}],
      'retry_after_expiry':[{'op':'commit'},{'op':'advance_time','value':'2026-10-10T10:00:00+07:00'},{'op':'commit'}],
      'stale_resume':[{'op':'resume','checkpoint_version':6}],
      'wrong_approval_resume':[{'op':'resume','approval_id':'other-approval'}],
      'scope_changed_after_commit':[{'op':'commit'},{'op':'change_scope','key':'customer_id','value':'other-customer'},{'op':'lookup'}],
      'approval_scope_mismatch':[{'op':'change_approval_scope','key':'customer_id','value':'other-customer'},{'op':'commit'}],
    }
    write('fixtures.json',{'scope':'offline_contract_conformance','synthetic':True,'protocol_vectors':[{'case_id':name,'covers':covers,'base_examples':'examples.json','actions':actions[name],'expected':{'outcome':outcome,'business_effect_count':count}} for name,covers,outcome,count in scenarios]})
    print(f'Generated {len(list((ROOT/"schemas").glob("*.json")))} schemas, {len(tools)} tools, {len(examples)} examples and {len(scenarios)} offline protocol vectors.')


if __name__=='__main__': build()
