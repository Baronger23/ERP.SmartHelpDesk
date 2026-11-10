/* Shared Desk actions. Server permissions and command preconditions remain authoritative. */
(() => {
  if (window.shd_operations) return;
  const labels = {
    register: 'Tạo hồ sơ', activate: 'Duyệt và công bố phiên bản', revoke: 'Thu hồi hiệu lực',
    declare_materials: 'Khai báo vật tư cần chuẩn bị', cancel_service_invoice: 'Duyệt hủy hóa đơn dịch vụ',
    receive_request: 'Tiếp nhận yêu cầu', triage: 'Phân loại và xác nhận quyền lợi', acknowledge: 'Ghi phản hồi khách',
    create_work_order: 'Tạo gói công việc', assign: 'Phân công kỹ thuật viên', start_visit: 'Bắt đầu lượt tác nghiệp',
    finish_visit: 'Kết thúc lượt tác nghiệp', log_time: 'Ghi giờ công', restore: 'Xác nhận khôi phục',
    accept_work: 'Khách nghiệm thu', close_request: 'Đóng yêu cầu', wait: 'Ghi nhận chờ', end_wait: 'Kết thúc chờ',
    classify_callback: 'Phân loại tái phát', correct_restoration: 'Đính chính kết quả khôi phục',
    generate_pm: 'Sinh kỳ bảo trì', postpone_pm: 'Duyệt hoãn bảo trì', complete_pm: 'Ghi kết quả bảo trì',
    classify_finding: 'Phân loại bất thường', search_knowledge: 'Tra cứu tri thức đã duyệt',
    available_stock: 'Kiểm tra tồn khả dụng', reserve: 'Giữ chỗ vật tư', release_reservation: 'Giải phóng vật tư',
    consume: 'Ghi tiêu hao vật tư', transfer_reserved: 'Bàn giao vật tư sang kho khác',
    create_demand: 'Ghi nhu cầu vật tư', requisition: 'Chuẩn bị đề nghị mua', prepare_purchase_order: 'Chuẩn bị đơn mua',
    approve_purchase_order: 'Duyệt đơn mua đúng nội dung', receive_purchase: 'Nhận và kiểm tra hàng mua',
    propose_estimate: 'Lập dự toán phát sinh', decide_estimate: 'Khách quyết định dự toán',
    reconcile_charge: 'Đối soát khoản phí', prepare_invoice: 'Lập hóa đơn từ nguồn đã đối soát', snapshot_kpis: 'Lập báo cáo theo kỳ'
  };
  const fieldLabels = {
    requirements: 'Vật tư cần chuẩn bị', invoice: 'Hóa đơn dịch vụ', selling_price_list: 'Bảng giá bán', auto_revision: 'Tự nối với bản báo cáo trước',
    work_order_id: 'Gói công việc', request: 'Yêu cầu', origin_kind: 'Loại nguồn việc', origin: 'Nguồn việc',
    scope_text: 'Phạm vi công việc', required_for_restoration: 'Bắt buộc để khôi phục', package_key: 'Mã gói việc',
    company: 'Công ty', customer: 'Khách hàng', site: 'Địa điểm', equipment: 'Thiết bị', subject: 'Nội dung yêu cầu',
    reported_at: 'Thời điểm khách báo', received_at: 'Thời điểm AIS nhận', occurred_at: 'Thời điểm thực tế',
    service_type: 'Loại dịch vụ', reason: 'Lý do / căn cứ', owner: 'Người chịu trách nhiệm', priority: 'Mức ưu tiên',
    agreement: 'Phiên bản hợp đồng', incident: 'Sự cố', technician: 'Kỹ thuật viên', starts_at: 'Bắt đầu lịch',
    ends_at: 'Kết thúc lịch', required_skill: 'Kỹ năng yêu cầu', visit: 'Lượt tác nghiệp', outcome: 'Kết quả',
    evidence: 'Bằng chứng / ghi nhận', completed: 'Lượt đã hoàn thành công việc', hours: 'Giờ thực tế',
    billable_hours: 'Giờ tính phí', work_kind: 'Loại công', criteria: 'Tiêu chí thử máy', measurements: 'Thông số đo',
    interval: 'Khoảng chờ', eta: 'Dự kiến đáp ứng', original_incident: 'Sự cố gốc', classification: 'Phân loại',
    source_event: 'Sự kiện cần đính chính', plan: 'Kế hoạch PM', period_key: 'Số kỳ (bắt đầu từ 0)',
    occurrence: 'Kỳ bảo trì', new_due: 'Hạn mới', observations: 'Kết quả checklist', findings: 'Các bất thường',
    finding: 'Bất thường', disposition: 'Hướng xử lý', model: 'Model máy', query: 'Nội dung cần tìm',
    item: 'Vật tư / dịch vụ', warehouse: 'Kho', quantity: 'Số lượng', expires_at: 'Hết hiệu lực lúc',
    reservation: 'Phiếu giữ chỗ', target_warehouse: 'Kho nhận', needed_at: 'Ngày cần hàng', demand: 'Nhu cầu mua',
    supplier: 'Nhà cung cấp', rate: 'Đơn giá', delivery_date: 'Ngày giao dự kiến', binding_hash: 'Mã nội dung được duyệt',
    accepted_quantity: 'Số lượng đạt', rejected_quantity: 'Số lượng không đạt', rejected_warehouse: 'Kho cách ly',
    lines: 'Dòng dự toán', currency: 'Tiền tệ', estimate: 'Dự toán', approve: 'Đồng ý nội dung này',
    source_type: 'Loại nguồn phí', source_name: 'Chứng từ nguồn', billing_policy: 'Chính sách phí', labor_cost_rate: 'Giá vốn giờ công',
    period_start: 'Từ thời điểm', period_end: 'Đến trước thời điểm', as_of: 'Dữ liệu ghi nhận đến', supersedes: 'Bản báo cáo trước',
    record_type: 'Loại hồ sơ', name: 'Hồ sơ'
  };
  const links = { company:'Company', customer:'Customer', site:'SHD Site', equipment:'SHD Equipment', request:'SHD Request',
    incident:'SHD Incident', original_incident:'SHD Incident', agreement:'SHD Agreement', owner:'User', technician:'User',
    work_order_id:'SHD Work Order', visit:'SHD Visit', interval:'SHD Wait Interval', source_event:'SHD Event', plan:'SHD PM Plan',
    occurrence:'SHD PM Occurrence', finding:'SHD Finding', item:'Item', warehouse:'Warehouse', target_warehouse:'Warehouse',
    reservation:'SHD Reservation', demand:'SHD Demand', supplier:'Supplier', rejected_warehouse:'Warehouse',
    currency:'Currency', estimate:'SHD Estimate', supersedes:'SHD KPI Snapshot', selling_price_list:'Price List', invoice:'Sales Invoice' };
  const actionsByType = {
    'SHD Request':['receive_request','triage','acknowledge','create_work_order','wait','close_request'],
    'SHD Incident':['create_work_order','classify_callback'], 'SHD Work Source':['create_work_order'],
    'SHD Work Order':['declare_materials','reserve','assign','start_visit','propose_estimate','restore','accept_work','create_demand','prepare_invoice','correct_restoration'],
    'SHD Visit':['start_visit','finish_visit','log_time','consume'], 'SHD Time Log':['reconcile_charge'],
    'SHD Material Use':['reconcile_charge'], 'SHD Wait Interval':['end_wait'],
    'SHD Agreement':['activate','revoke'], 'SHD PM Plan':['activate','generate_pm','revoke'],
    'SHD PM Occurrence':['generate_pm','complete_pm','postpone_pm'], 'SHD Finding':['classify_finding'],
    'SHD Reservation':['available_stock','reserve','transfer_reserved','consume','release_reservation'],
    'SHD Demand':['create_demand','requisition','prepare_purchase_order','approve_purchase_order','receive_purchase'],
    'SHD Estimate':['propose_estimate','decide_estimate'], 'SHD Charge':['reconcile_charge','prepare_invoice','cancel_service_invoice'],
    'SHD Knowledge':['activate','search_knowledge','revoke'], 'SHD KPI Snapshot':['snapshot_kpis'],
    'SHD Access Grant':['revoke'], 'SHD Contact Authority':['revoke'], 'SHD Technician':['revoke'],
    'SHD Equipment':['revoke'], 'SHD Compatibility':['revoke']
  };
  const selects = { origin_kind:['INCIDENT','SERVICE_REQUEST','PM_OCCURRENCE'], service_type:['Repair','Consultation','PM'],
    priority:['Low','Medium','High','Urgent'], classification:['Callback','Related','New'], disposition:['Monitor','Repair','No fault'],
    work_kind:['Labor','Travel','Waiting'], source_type:['Material','Time'], billing_policy:['Warranty','Billable','Goodwill'] };
  const tables = {
    requirements: [{fieldname:'item',fieldtype:'Link',options:'Item',label:'Vật tư',reqd:1,in_list_view:1},
      {fieldname:'warehouse',fieldtype:'Link',options:'Warehouse',label:'Kho',reqd:1,in_list_view:1},
      {fieldname:'quantity',fieldtype:'Float',label:'Số lượng',reqd:1,in_list_view:1}],
    lines: [{fieldname:'item',fieldtype:'Link',options:'Item',label:'Vật tư / dịch vụ',reqd:1,in_list_view:1},
      {fieldname:'quantity',fieldtype:'Float',label:'Số lượng',reqd:1,in_list_view:1}, {fieldname:'rate',fieldtype:'Currency',label:'Đơn giá',reqd:1,in_list_view:1}],
    measurements: [{fieldname:'metric',fieldtype:'Data',label:'Chỉ tiêu',reqd:1,in_list_view:1},
      {fieldname:'value',fieldtype:'Float',label:'Giá trị',in_list_view:1}, {fieldname:'unit',fieldtype:'Data',label:'Đơn vị',reqd:1,in_list_view:1}],
    observations: [{fieldname:'key',fieldtype:'Data',label:'Mã checklist',reqd:1,in_list_view:1},
      {fieldname:'result',fieldtype:'Select',options:'Passed\nAbnormal\nNot applicable\nNot performed',label:'Kết quả',reqd:1,in_list_view:1},
      {fieldname:'value',fieldtype:'Float',label:'Giá trị',in_list_view:1}, {fieldname:'unit',fieldtype:'Data',label:'Đơn vị',in_list_view:1},
      {fieldname:'reason',fieldtype:'Data',label:'Lý do'}],
    findings: [{fieldname:'description',fieldtype:'Data',label:'Bất thường',reqd:1,in_list_view:1},
      {fieldname:'severity',fieldtype:'Data',label:'Mức ảnh hưởng',reqd:1,in_list_view:1},
      {fieldname:'service_owner',fieldtype:'Link',options:'User',label:'Người theo tiếp',reqd:1,in_list_view:1},
      {fieldname:'due_at',fieldtype:'Datetime',label:'Hạn xử lý',reqd:1}]
  };
  const cleanRows = (rows, fields) => (rows || []).map(row => Object.fromEntries(fields.map(f => [f.fieldname, row[f.fieldname] ?? null])));
  async function submit(command, payload, key, dialog, refresh) {
    const response = await frappe.call({method:'smart_helpdesk.api.execute',type:'POST',
      args:{command,payload:JSON.stringify(payload),idempotency_key:key},freeze:true,freeze_message:'Đang ghi nhận nghiệp vụ…'});
    dialog.hide();
    if (refresh) refresh();
    const record = response.message;
    if (record.doctype && record.name) {
      frappe.show_alert({message:'Đã ghi nhận: ' + (record.status || record.name),indicator:'green'});
      frappe.set_route('Form',record.doctype,record.name);
    } else {
      // Structured read results are reviewable, with escaped values.
      frappe.msgprint({title:'Kết quả',message:'<pre style="white-space:pre-wrap">'+frappe.utils.escape_html(JSON.stringify(record,null,2))+'</pre>'});
    }
  }
  function argumentField(arg, current) {
    const name=arg.name;
    let field={fieldname:name,label:fieldLabels[name] || name,reqd:arg.required,default:arg.default};
    if (links[name]) Object.assign(field,{fieldtype:'Link',options:links[name]});
    else if (selects[name]) Object.assign(field,{fieldtype:'Select',options:selects[name]});
    else if (tables[name]) Object.assign(field,{fieldtype:'Table',fields:tables[name],in_place_edit:true,data:[]});
    else if (['approve','completed','required_for_restoration','auto_revision'].includes(name)) Object.assign(field,{fieldtype:'Check',reqd:0});
    else if (name.endsWith('_at') || ['as_of','starts_at','ends_at','period_start','period_end'].includes(name)) field.fieldtype='Datetime';
    else if (['delivery_date','new_due'].includes(name)) field.fieldtype='Date';
    else if (['hours','billable_hours','rate','labor_cost_rate'].includes(name)) field.fieldtype='Float';
    else field.fieldtype=['reason','evidence','criteria','outcome','scope_text','response','subject'].includes(name)?'Small Text':'Data';
    if (name==='needed_at') field.fieldtype='Date';
    if (current && (links[name]===current.doctype)) field.default=current.name;
    else if (current && current[name] != null && typeof current[name] !== 'object') field.default=current[name];
    return field;
  }
  async function openCommand(current, refresh) {
    const {message:catalog}=await frappe.call('smart_helpdesk.api.catalog');
    const relevant=current ? catalog.filter(c=>(actionsByType[current.doctype]||[]).includes(c.command)) : catalog.filter(c=>c.command!=='register');
    if(!relevant.length) {frappe.msgprint('Không có thao tác phù hợp với vai trò và loại hồ sơ này.');return;}
    const choose = new frappe.ui.Dialog({title:'Thao tác nghiệp vụ',fields:[{fieldname:'command',label:'Thao tác',fieldtype:'Select',
      options:relevant.map(c=>({value:c.command,label:labels[c.command]||c.command})),reqd:1}],
      primary_action_label:'Tiếp tục',primary_action(values){
        choose.hide(); const selected=catalog.find(c=>c.command===values.command); const key=crypto.randomUUID();
        const fields=selected.arguments.map(arg=>argumentField(arg,current));
        if(current && selected.command==='create_work_order') {
          const kinds={'SHD Incident':'INCIDENT','SHD Request':'SERVICE_REQUEST','SHD PM Occurrence':'PM_OCCURRENCE'};
          if(kinds[current.doctype]) {
            fields.find(f=>f.fieldname==='origin_kind').default=current.incident?'INCIDENT':kinds[current.doctype];
            fields.find(f=>f.fieldname==='origin').default=current.incident || current.name;
          }
        }
        if (current && fields.some(f=>f.fieldname==='record_type')) {
          fields.find(f=>f.fieldname==='record_type').default=current.doctype;
          fields.find(f=>f.fieldname==='name').default=current.name;
        }
        const dialog=new frappe.ui.Dialog({title:labels[selected.command]||selected.command,fields,size:'large',
          primary_action_label:'Ghi nhận',async primary_action(payload){
            for(const name of Object.keys(tables)) if(payload[name]) payload[name]=cleanRows(payload[name],tables[name]);
            for(const name of ['approve','completed','required_for_restoration','auto_revision']) if(name in payload) payload[name]=Boolean(payload[name]);
            if(selected.command==='finish_visit') payload.evidence={note:payload.evidence};
            await submit(selected.command,payload,key,dialog,refresh);
          }});dialog.show();
      }});choose.show();
  }
  async function openMaster(refresh) {
    const {message:catalog}=await frappe.call('smart_helpdesk.api.master_catalog');
    const choose=new frappe.ui.Dialog({title:'Tạo hồ sơ nghiệp vụ',fields:[{fieldname:'type',fieldtype:'Select',label:'Loại hồ sơ',
      options:Object.keys(catalog),reqd:1}],primary_action_label:'Tiếp tục',primary_action(values){
      choose.hide(); const recordType=values.type; const key=crypto.randomUUID();
      const fields=catalog[recordType].map(f=>({...f,fieldtype:f.fieldtype==='JSON'?'Code':f.fieldtype,
        options:f.fieldtype==='JSON'?'JSON':f.options}));
      const dialog=new frappe.ui.Dialog({title:'Tạo '+recordType,fields,size:'large',primary_action_label:'Lưu hồ sơ',
        async primary_action(input){
          const payload={...input};
          for(const f of catalog[recordType]) if(f.fieldtype==='JSON' && payload[f.fieldname]) payload[f.fieldname]=JSON.parse(payload[f.fieldname]);
          await submit('register',{record_type:recordType,values:payload},key,dialog,refresh);
        }});dialog.show();
    }});choose.show();
  }
  window.shd_operations={openCommand,openMaster};
  const names=['Site','Access Grant','Contact Authority','Equipment','Agreement','Entitlement','Request','Incident','Work Source',
    'Work Order','Technician','Visit','Time Log','Acceptance','Wait Interval','PM Plan','PM Occurrence','Finding','Reservation',
    'Material Use','Compatibility','Demand','Estimate','Charge','Knowledge','KPI Snapshot','Event','Command'];
  for(const shortName of names){
    const doctype='SHD '+shortName;
    frappe.ui.form.on(doctype,{refresh(frm){
      frm.disable_save();
      if(frm.is_new()) {frappe.set_route('List',doctype); return;}
      frm.add_custom_button('Thao tác nghiệp vụ',()=>openCommand(frm.doc,()=>frm.reload_doc()));
    }});
    frappe.listview_settings[doctype]={onload(list){
      const current={doctype};
      list.set_primary_action=()=>list.page.set_primary_action('Thao tác nghiệp vụ',()=>openCommand(current,()=>list.refresh()));
      list.make_new_doc=()=>openCommand(current,()=>list.refresh());
      list.set_primary_action();
      list.page.add_inner_button('Tạo hồ sơ',()=>openMaster(()=>list.refresh()));
    }};
  }
})();
