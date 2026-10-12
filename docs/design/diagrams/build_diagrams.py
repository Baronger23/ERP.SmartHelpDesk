"""Build enterprise SVG / Draw.io diagrams with local Lucide icons.
Run: python docs/design/diagrams/build_diagrams.py
Icons license: icons/license.txt. PNGs are rendered separately in a browser.
"""
from pathlib import Path
import base64
import html
import json
import re
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
INK, MUTED, BLUE, BORDER, BG = '#0F172A', '#475569', '#1D4ED8', '#E2E8F0', '#F8FAFC'
MODULES = [
 ('M01','Khách hàng & hợp đồng','file-text','#1D4ED8','#EFF6FF',['Khách / site / người có thẩm quyền','Phạm vi, cam kết và version','Quyền lợi tại thời điểm phục vụ'],'PP-01/02 · US-01–04'),
 ('M02','Tiếp nhận & SLA','clipboard-list','#1D4ED8','#EFF6FF',['Báo lỗi, triage và ca liên quan','Mốc thực, hạn và lý do chờ','Owner, timeline và escalation'],'PP-03/04 · US-05–08'),
 ('M03','Điều phối & tác nghiệp','wrench','#047857','#ECFDF5',['Work order và từng lượt thực hiện','Kỹ năng, lịch và nguồn lực','Khôi phục, nghiệm thu, callback'],'PP-05/06 · US-09–12'),
 ('M04','Thiết bị & bảo trì','cpu','#047857','#ECFDF5',['Máy, model, cấu hình và lịch sử','Checklist, kỳ PM và cửa sổ máy','Bất thường có owner và hành động'],'PP-07/08 · US-13–16'),
 ('M05','Kho & vật tư','package','#B45309','#FFFBEB',['Tồn thực, khả dụng và giữ chỗ','Kho tổng / xe, bàn giao và trả','Tiêu hao đúng ca / máy / lượt'],'PP-09/10 · US-17–20'),
 ('M06','Mua hàng & bổ sung','shopping-cart','#B45309','#FFFBEB',['Nhu cầu ròng, đơn đang mở','Duyệt mua, PO và ETA','Nhận một phần, reject và return'],'PP-11/12 · US-21–24'),
 ('M07','Chi phí & hóa đơn','receipt','#0284C7','#F0F9FF',['Quyền lợi và phát sinh được duyệt','Công, vật tư và phí có nguồn','Hóa đơn, đối soát và điều chỉnh'],'PP-13/14 · US-25–28'),
 ('M08','Báo cáo & KPI','chart-no-axes-combined','#0284C7','#F0F9FF',['Dashboard ca cần hành động','SLA, FTFR, PM và chi phí','Công thức, kỳ và dữ liệu nguồn'],'PP-15/16 · US-29–32'),
 ('M09','Tri thức kỹ thuật','book-open','#64748B','#F8FAFC',['SOP, model, revision và người duyệt','Ingestion / hybrid retrieval / evidence','Freshness, quyền nguồn và bài học'],'PP-17/18 · US-33/34'),
]


class Canvas:
    def __init__(self,name,title,subtitle,h=1540):
        self.name,self.title,self.w,self.h,self.items=name,title,1920,h,[]
        self.box('background',0,0,self.w,h,BG,BG)
        self.text('title',64,42,title,40,bold=True)
        self.text('subtitle',64,98,subtitle,23,MUTED)
    def box(self,key,x,y,w,h,fill='#FFFFFF',stroke=BORDER,dashed=False):
        self.items.append(dict(kind='box',id=key,x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,dashed=dashed))
    def text(self,key,x,y,lines,size=22,color=INK,bold=False,width=None):
        if isinstance(lines,str): lines=[lines]
        self.items.append(dict(kind='text',id=key,x=x,y=y,lines=lines,size=size,color=color,bold=bold,w=width or max(len(s) for s in lines)*size*.65,h=len(lines)*size*1.45))
    def icon(self,key,name,x,y,size=40,color=BLUE):
        raw=(OUT/'icons'/f'{name}.svg').read_text(encoding='utf-8').replace('currentColor',color)
        self.items.append(dict(kind='icon',id=key,x=x,y=y,w=size,h=size,raw=raw))
    def edge(self,key,points,label=None,xy=None,color=BLUE):
        self.items.append(dict(kind='edge',id=key,points=points,color=color))
        if label:
            x,y=xy
            self.box(key+'-bg',x-6,y-3,len(label)*10+12,32,'#FFFFFF','#FFFFFF')
            self.text(key+'-label',x,y,label,19,MUTED)
    def footer(self,y):
        self.text('footer',64,y,'AIS · Thiết kế v3.0 · Kiến trúc mục tiêu; runtime chưa triển khai · Icon Lucide',18,MUTED)


def card(c,i,x,y,w=572,h=196,compact=False):
    code,title,ico,accent,fill,lines,trace=MODULES[i]
    c.box(code,x,y,w,h,fill,accent)
    c.icon(code+'-icon',ico,x+22,y+22,38,accent)
    c.text(code+'-title',x+76,y+21,f'{code}  {title}',26,bold=True,width=w-98)
    c.text(code+'-body',x+24,y+79,lines[:2] if compact else lines,22,MUTED,width=w-48)
    if not compact: c.text(code+'-trace',x+24,y+169,trace,18,accent,True,width=w-48)


def overview():
    c=Canvas('01_tong_quan_he_thong','Smart HelpDesk & Maintenance','Từ giá trị doanh nghiệp đến domain và Agent Harness · AIS dịch vụ bảo trì công nghiệp B2B',1660)
    c.box('value',64,146,1792,62,INK,INK)
    c.text('value-text',92,163,'Khôi phục đúng cam kết  •  Phòng ngừa thực hiện được  •  Vật tư có trách nhiệm  •  Phí minh bạch  •  Cải tiến có dữ liệu',24,'#FFFFFF')
    c.text('actors-label',64,237,'Người dùng và quyền quyết định',24,BLUE,True)
    actors=[('Khách / người duyệt','factory'),('Điều phối / KTV','wrench'),('Kho / mua hàng','truck'),('Kế toán dịch vụ','receipt'),('Quản lý / quản trị','users')]
    for i,(s,ico) in enumerate(actors):
        x=64+i*364
        c.box('actor'+str(i),x,278,336,70)
        c.icon('actor-icon'+str(i),ico,x+18,296,32)
        c.text('actor-text'+str(i),x+65,300,s,23,bold=True)
    c.text('channels-label',64,373,'Kênh tiếp nhận và tác nghiệp',24,BLUE,True)
    channels=[('Portal khách hàng','globe','Báo lỗi, tiến độ, đồng ý và nghiệm thu'),('Desk web / điện thoại','users','Nhân sự AIS tác nghiệp theo vai trò'),('Hotline / Zalo: nhập hộ','message-circle','Kênh ngoài hệ thống ở phạm vi ban đầu')]
    for i,(s,ico,body) in enumerate(channels):
        x=64+i*610
        c.box('channel'+str(i),x,412,572,82,'#EFF6FF','#BFDBFE')
        c.icon('channel-icon'+str(i),ico,x+20,436,32)
        c.text('channel-title'+str(i),x+68,426,s,24,BLUE,True)
        c.text('channel-body'+str(i),x+68,462,body,20,MUTED)
        c.edge('channel-edge'+str(i),[(x+286,496),(x+286,516)])
    c.text('modules-label',64,526,'Năng lực nghiệp vụ · mỗi module có owner, quy tắc, dữ liệu và tiêu chí nghiệm thu',25,BLUE,True)
    for i in range(9): card(c,i,64+(i%3)*610,575+(i//3)*220)
    c.box('harness',64,1238,1792,94,'#F0F9FF','#0284C7')
    c.icon('harness-icon','cpu',88,1266,38,'#0284C7')
    c.text('harness-title',149,1251,'Agent Harness — runtime điều phối ngang M01–M10',28,'#0284C7',True)
    c.text('harness-body',149,1291,'Plan → Act → Observe → Evaluate/Replan  •  Typed tools  •  Durable checkpoint  •  Approval  •  Evidence / budget',22,MUTED)
    c.box('M10',64,1360,1792,108,'#EFF6FF',BLUE)
    c.icon('M10-icon','shield-check',90,1390,42)
    c.text('M10-title',150,1378,'M10  Quản trị & kiểm soát — authority nghiệp vụ xuyên suốt',28,BLUE,True)
    c.text('M10-body',150,1421,'Identity / scope  •  Approval bind payload/version  •  Audit  •  Chất lượng dữ liệu  •  Thu hồi quyền và phục hồi',22,MUTED)
    c.text('M10-trace',1500,1386,'PP-19/20 · US-37–40',20,BLUE)
    c.edge('platform-edge',[(960,1470),(960,1495)])
    c.box('platform',64,1500,1792,84,INK,INK)
    c.icon('platform-icon','database',91,1525,32,'#FFFFFF')
    c.text('platform-title',144,1515,'Ứng viên hiện thực: ERPNext / Frappe + runtime state store',26,'#FFFFFF',True)
    c.text('platform-body',144,1554,'Domain transactions / validation / quyền server • command receipt / outbox • API • jobs • Local hoặc Cloud',21,'#CBD5E1')
    c.footer(1610)
    return c


def journey():
    c=Canvas('02_chuoi_gia_tri','Chuỗi giá trị dịch vụ và các điểm bàn giao','Không chỉ đóng ticket: từ quyền lợi tới kết quả kỹ thuật, thương mại và cải tiến',1100)
    c.box('ribbon',64,150,1792,100,'#EFF6FF','#BFDBFE')
    c.icon('ribbon-icon','factory',88,177,44)
    c.text('ribbon-title',154,169,'Khách hàng mua khả năng khôi phục, tính dự đoán và trách nhiệm',29,BLUE,True)
    c.text('ribbon-body',154,210,'Một ca có thể nhiều lượt đến; hoàn tất kỹ thuật ≠ khách chấp nhận ≠ đã lập hóa đơn ≠ đã thanh toán',22,MUTED)
    steps=[('Cam kết','file-text','M01',['Khách / site / phạm vi','Cam kết và quyền lợi'],['Coverage version','Người có thẩm quyền']),('Tiếp nhận','clipboard-list','M02',['Báo lỗi, triage, owner','Mốc thực và thời hạn'],['Yêu cầu có context','Hạn có nguồn']),('Chuẩn bị','calendar-clock','M03 · M05',['Người, slot, kỹ năng','Giữ chỗ atomic / dụng cụ'],['Work order / booking','Nguồn lực khả dụng']),('Thực hiện','wrench','M03 · M04',['Visit, thử máy, công','M03 ghi nghiệm thu'],['Kết quả kỹ thuật','Vật tư thực dùng']),('Quyết toán','receipt','M07',['Nhận nghiệm thu M03','Phí có nguồn và approval'],['Charge có nguồn','Hóa đơn / đối soát']),('Cải tiến','chart-no-axes-combined','M08 · M09',['Chất lượng và chi phí','Tri thức được review'],['Hành động quản lý','SOP / PM tốt hơn'])]
    c.text('chain-label',64,294,'Chuỗi chính',25,BLUE,True)
    for i,(title,ico,mods,actions,outputs) in enumerate(steps):
        x=64+i*303
        c.box('step'+str(i),x,348,276,358)
        c.icon('step-icon'+str(i),ico,x+22,370,42)
        c.text('step-number'+str(i),x+213,376,f'{i+1:02}',26,BLUE,True)
        c.text('step-title'+str(i),x+22,432,title,28,bold=True)
        c.text('step-module'+str(i),x+22,476,mods,21,BLUE,True)
        c.text('step-action'+str(i),x+22,522,actions,21,MUTED)
        c.box('step-output'+str(i),x+16,606,244,80,'#F0F9FF','#E0F2FE')
        c.text('step-output-text'+str(i),x+28,620,outputs,20,INK,True)
        if i<5: c.edge('step-edge'+str(i),[(x+278,466),(x+299,466)])
    c.text('branch-label',64,744,'Luồng bổ sung và ngoại lệ cần giữ lịch sử',25,BLUE,True)
    branches=[('Bảo trì phòng ngừa','cpu',['M04 sinh kỳ PM → M03 thực hiện','Finding → M02 ca sửa hoặc action theo dõi']),('Thiếu vật tư / nguồn lực','package',['M05 shortage → M06 mua / nhận accepted','M02/M03 giữ lý do chờ, ETA và lượt tiếp theo']),('Phát sinh / sự cố tái phát','badge-check',['Thay scope → khách/phê duyệt M07','Callback → review, ca gốc và quyết định phí'])]
    for i,(s,ico,body) in enumerate(branches):
        x=64+i*610
        c.box('branch'+str(i),x,794,572,142)
        c.icon('branch-icon'+str(i),ico,x+20,816,32)
        c.text('branch-title'+str(i),x+70,816,s,24,BLUE,True)
        c.text('branch-body'+str(i),x+22,862,body,21,MUTED)
    c.box('controls',64,972,1792,64,INK,INK)
    c.text('controls-text',88,991,'M10 xuyên suốt: identity / scope → phê duyệt đúng → transaction / chống trùng → audit và dữ liệu có thể đối soát',23,'#FFFFFF')
    c.footer(1060)
    return c


def relationships():
    c=Canvas('03_quan_he_module','Quan hệ giữa các module nghiệp vụ','Luồng chính trên hình + bảng bàn giao bổ sung · không suy ra microservices',1820)
    pos={0:(64,220),1:(700,220),2:(1336,220),3:(64,630),4:(700,630),6:(1336,630),8:(64,1040),5:(700,1040),7:(1336,1040)}
    c.edge('coverage',[(556,272),(700,272)],'Quyền lợi',(576,240))
    c.edge('work',[(1192,272),(1336,272)],'Giao việc',(1212,240))
    c.edge('result',[(1336,335),(1192,335)],'Kết quả',(1212,345))
    c.edge('finding',[(556,675),(624,675),(624,333),(700,333)],'Máy / finding',(577,465))
    c.edge('material-demand',[(1582,370),(1582,460),(946,460),(946,630)],'Nhu cầu / visit',(963,490))
    c.edge('technical-cost',[(1728,370),(1728,630)],'Công / nghiệm thu',(1737,500))
    c.edge('approved-scope',[(1430,630),(1430,500),(1408,500),(1408,370)],'Duyệt scope/phí',(1231,548))
    c.edge('valuation',[(1192,702),(1336,702)],'Tiêu hao',(1212,669))
    c.edge('shortage',[(860,780),(860,1040)],'Nhu cầu thiếu',(706,882))
    c.edge('accepted-receipt',[(1058,1040),(1058,780)],'Hàng nhận đạt',(1075,882))
    c.edge('knowledge',[(310,1040),(310,780)],'SOP / model',(329,885))
    c.edge('financial-source',[(1582,780),(1582,1040)],'Phí / chứng từ',(1600,886))
    for i,(x,y) in pos.items(): card(c,i,x,y,w=492,h=150,compact=True)
    c.text('analytics-note',1358,1198,'M08 còn đọc M01–M06 theo kỳ và quyền',19,MUTED)
    c.box('handoffs',64,1240,1792,300)
    c.text('handoffs-title',88,1256,'Bàn giao bổ sung theo hợp đồng logic',25,BLUE,True)
    c.text('handoffs-left',88,1305,[
        'M01 → M07: coverage snapshot / quyền lợi tính phí',
        'M04 → M03: kỳ PM / checklist / nguồn công việc',
        'M07 → M02: approval / pending / dispute',
        'M03 / M04 → M09: bài học qua quality review'],22,MUTED)
    c.text('handoffs-right',960,1305,[
        'M09 → Harness / M03: tri thức có nguồn và scope',
        'M01–M07 → M08: facts theo kỳ / quyền / watermark',
        'M03 → M02: khôi phục / nghiệm thu do M03 ghi',
        'M10 ↔ mọi module: quyền / policy / approval / audit'],22,MUTED)
    c.text('handoffs-note',88,1470,'Bảng là phần của sơ đồ: giữ các quan hệ này khi dựng lại; không thêm đường chéo qua khối và nhãn.',21,MUTED)
    c.box('M10',64,1580,1792,64,'#EFF6FF',BLUE)
    c.icon('M10-icon','shield-check',84,1594,34)
    c.text('M10-title',139,1599,'M10  Identity / scope • approval • audit • chất lượng dữ liệu và vận hành — áp dụng cho tất cả module',23,BLUE,True)
    c.box('harness-relations',64,1670,1792,64,'#F0F9FF','#0284C7')
    c.text('harness-relations-text',88,1689,'Harness ↔ M01–M10 qua capabilities / gateway: reads, proposals, approved drafts; authority vẫn thuộc domain',22,'#0284C7',True)
    c.footer(1770)
    return c


def agent_harness():
    c=Canvas('05_agent_harness','Agent Harness và orchestration','Single orchestrator + specialized capabilities + controlled Tool Gateway · thiết kế mục tiêu v3',1500)
    c.box('channel',64,157,1792,68)
    c.icon('channel-icon','users',88,175,32)
    c.text('channel-title',146,176,'KTV / điều phối / quản lý → chat, portal hoặc contextual assistant',27,bold=True)
    c.edge('gateway-edge',[(960,227),(960,255)])
    c.box('gateway',64,260,1792,87,'#EFF6FF',BLUE)
    c.icon('gateway-icon','globe',88,285,34)
    c.text('gateway-title',146,273,'Agent Gateway: identity, company / customer / site scope, session, rate limit',27,BLUE,True)
    c.text('gateway-body',146,314,'Trusted context do server xác thực • nội dung chat/tài liệu không cấp quyền',22,MUTED)
    c.edge('gateway-harness',[(960,350),(960,383)])
    c.box('controller',64,390,1792,493,'#FFFFFF','#CBD5E1')
    c.text('controller-label',92,411,'Harness / single orchestrator · pin instruction, model policy, registry và limits',26,BLUE,True)
    components=[
      ('Context & intent','clipboard-list',['Resolve máy / ca và mục tiêu','Route simple lookup hoặc task plan']),
      ('Task planner','calendar-clock',['Steps, dependencies và success predicate','Replan có reason, không reset budget']),
      ('Execution controller','wrench',['Tool dispatch, limits, lease / fencing','Retry / checkpoint / resume có kiểm soát']),
      ('Observation & evaluator','cpu',['Typed data, error, unknown, conflict','Đủ bằng chứng thì finish; thiếu thì dừng']),
      ('Evidence verifier','badge-check',['Model / revision / page / applicability','Claim support và conflict / freshness']),
      ('Policy & approval gate','shield-check',['Exact hash, scope, version và expiry','Revalidate trước commit, authority M10'])]
    for i,(title,ico,body) in enumerate(components):
        x,y=92+(i%3)*588,470+(i//3)*150
        c.box('component'+str(i),x,y,560,132,'#F8FAFC')
        c.icon('component-icon'+str(i),ico,x+18,y+22,32)
        c.text('component-title'+str(i),x+65,y+18,title,25,bold=True)
        c.text('component-body'+str(i),x+20,y+64,body,21,MUTED)
    c.box('loop',92,785,1732,69,'#0F172A','#0F172A')
    c.text('loop-title',119,805,'Plan → Act → Observe → Evaluate → Replan / Finish   |   Stop: evidence đủ, cần người, quyền, budget hoặc cancel',24,'#FFFFFF')
    supports=[('Knowledge capability · M09','book-open',['Hybrid retrieval / rerank / citations','Live model/version/scope/catalog checks','SOP / manual / lesson đã duyệt']),
              ('Controlled ERP Tool Gateway','shield-check',['Typed args / RBAC-ABAC / validation','Prepare → approve → revalidate → commit','Idempotency receipt / reconcile UNKNOWN']),
              ('Durable state & memory','database',['Run / plan / steps / evidence refs','Checkpoint / lease / CAS / resume inbox','Session/task memory không là fact ERP'])]
    for i,(title,ico,body) in enumerate(supports):
        x=64+i*610
        c.edge('support-edge'+str(i),[(x+286,885),(x+286,945)])
        c.box('support'+str(i),x,950,572,177,'#EFF6FF','#BFDBFE')
        c.icon('support-icon'+str(i),ico,x+20,974,32)
        c.text('support-title'+str(i),x+66,969,title,24,BLUE,True)
        c.text('support-body'+str(i),x+22,1020,body,21,MUTED)
    c.edge('business-edge',[(960,1129),(960,1183)])
    c.box('business',64,1188,1792,95,'#ECFDF5','#047857')
    c.text('business-title',92,1205,'Business systems & data: M01–M08 facts • M09 Knowledge • M10 policy / approval authority',26,'#047857',True)
    c.text('business-body',92,1248,'Baseline: reads / proposals / approved business drafts · reservation và submit thực hiện trong workflows nghiệp vụ',22,MUTED)
    c.box('observability',64,1340,1792,80,INK,INK)
    c.text('observability-title',92,1355,'Xuyên suốt: tracing • audit • evaluation • cumulative budget • security / authority boundaries',26,'#FFFFFF',True)
    c.text('observability-body',92,1392,'Schemas + offline contract vectors ≠ ERP/LLM runtime integration đã đạt',21,'#CBD5E1')
    c.footer(1450)
    return c


def deployment():
    c=Canvas('06_kien_truc_trien_khai','Kiến trúc triển khai mục tiêu','Smart HelpDesk & Maintenance · Production topology từ thiết bị người dùng đến cloud/VPC, dữ liệu và DevSecOps',1280)

    def server_card(key,x,title,badge,icon,accent,fill,lines):
        c.box(key,x,421,315,274,fill,accent)
        c.box(key+'-icon-bg',x+16,440,56,56,accent,accent)
        c.icon(key+'-icon',icon,x+28,452,32,'#FFFFFF')
        c.text(key+'-title',x+87,434,title,21,INK,True)
        c.text(key+'-badge',x+87,468,badge,17,accent,True)
        c.box(key+'-body-bg',x+14,514,287,160,'#FFFFFF','#FFFFFF')
        c.text(key+'-body',x+28,526,['• '+line for line in lines],18,MUTED)

    # Devices / roles — same layered visual language as the system architecture poster.
    c.box('device-band',24,136,1872,126,'#DCEEFF','#BFDBFE')
    c.text('device-title',44,154,'Thiết bị',25,'#0B3478',True)
    c.text('device-subtitle',44,190,['người dùng','(theo vai trò)'],19,'#0B3478')
    devices=[
      ('Khách hàng','globe',['Laptop / tablet / điện thoại','Web Portal responsive']),
      ('Kỹ thuật viên','wrench',['Điện thoại / tablet công ty','Desk/Portal + ảnh hiện trường']),
      ('Điều phối & vận hành','users',['Máy tính văn phòng','ERPNext Desk theo role']),
      ('Quản lý','chart-no-axes-combined',['Laptop / tablet','Dashboard & phê duyệt']),
      ('Quản trị hệ thống','shield-check',['Máy quản trị tin cậy','VPN / bastion / console'])]
    for i,(title,ico,body) in enumerate(devices):
        x=190+i*337
        c.box('device'+str(i),x,153,322,91,'#FFFFFF','#D8E7F5')
        c.icon('device-icon'+str(i),ico,x+18,177,38,'#0B4F9C')
        c.text('device-title'+str(i),x+72,162,title,21,'#082C6A',True)
        c.text('device-body'+str(i),x+72,199,body,16,'#294E82')
        c.edge('device-edge'+str(i),[(x+161,246),(x+161,276)],color='#0B4F9C')

    # Public edge.
    c.box('edge-band',24,282,1872,96,'#0B4F9C','#0B4F9C')
    c.text('edge-title',44,301,'Internet &',24,'#FFFFFF',True)
    c.text('edge-title-2',44,333,'vùng biên',24,'#FFFFFF',True)
    edge_items=[
      ('DNS + CDN','globe','Tên miền · cache static'),
      ('WAF + Rate limit','shield-check','Lọc tấn công · giới hạn tải'),
      ('TLS Load Balancer','cpu','HTTPS 443 · health routing'),
      ('Ingress routes','file-text','/web · /api · /socket · /agent')]
    for i,(title,ico,body) in enumerate(edge_items):
        x=220+i*415
        if i: c.box('edge-divider'+str(i),x-20,303,2,54,'#8DBBE9','#8DBBE9')
        c.icon('edge-icon'+str(i),ico,x,309,40,'#FFFFFF')
        c.text('edge-item-title'+str(i),x+58,298,title,21,'#FFFFFF',True)
        c.text('edge-item-body'+str(i),x+58,334,body,17,'#DCEEFF')
    # Private application subnet with deployable node pools.
    c.box('app-band',24,399,1872,320,'#EAF6FF','#BAE0F8')
    c.text('app-title',43,421,['Máy chủ','ứng dụng'],24,'#0B3478',True)
    c.text('app-subtitle',43,492,['Private subnet','Container · scale'],16,'#294E82')
    c.box('app-inner',164,412,1712,293,'#FFFFFF','#D8E7F5')
    server_card('web-pool',185,'Web node pool','2 INSTANCE','globe','#1D4ED8','#EFF6FF',[
      'frontend / Nginx','Portal & Desk assets','Reverse proxy nội bộ','Stateless · health check'])
    server_card('backend-pool',522,'ERPNext Backend','2 INSTANCE','cpu','#1D4ED8','#EFF6FF',[
      'Frappe + custom app','M01–M10 · REST API','RBAC · validation','Transaction / enqueue job'])
    server_card('realtime-pool',859,'Realtime node','≥ 1 INSTANCE','users','#0284C7','#F0F9FF',[
      'Node / Socket.IO','WSS realtime updates','Redis pub/sub','Reconnect / fallback REST'])
    server_card('worker-pool',1196,'Worker node pool','≥ 2 INSTANCE','wrench','#047857','#ECFDF5',[
      'queue-short / default','queue-long / reports','scheduler: 1 active','Retry + idempotency'])
    server_card('ai-pool',1533,'AI node pool','1 → N INSTANCE','book-open','#7C3AED','#F5F3FF',[
      'Agent Gateway / Harness','Orchestrator + checkpoint','RAG ingestion / retrieval','ERP Tool Gateway only'])
    c.edge('edge-to-app',[(342,380),(342,417)],color='#0B4F9C')
    c.edge('web-backend',[(501,558),(519,558)],color='#1D4ED8')
    c.edge('backend-realtime',[(838,558),(856,558)],color='#0284C7')

    # External systems and AI egress.
    c.box('integration-band',24,739,1872,143,'#E8E2FF','#C4B5FD')
    c.text('integration-title',43,754,['Dịch vụ','bên ngoài','& tích hợp'],20,'#3B258A',True)
    integrations=[
      ('Identity Provider','shield-check',['OIDC / SAML · MFA','Map role/scope tại ERP']),
      ('Đối tác / thiết bị','globe',['REST API có schema','Rate limit · audit · timeout']),
      ('Email · SMS · Zalo','message-circle',['Worker/adapter gửi thông báo','Callback phải xác thực']),
      ('LLM / Embedding API','book-open',['AI node → HTTPS 443','Không nhận ERP secret'])]
    for i,(title,ico,body) in enumerate(integrations):
        x=190+i*420
        c.box('integration'+str(i),x,760,400,101,'#FFFFFF','#D9D0FF')
        c.box('integration-icon-bg'+str(i),x+16,781,48,48,'#7C3AED','#7C3AED')
        c.icon('integration-icon'+str(i),ico,x+25,790,30,'#FFFFFF')
        c.text('integration-title'+str(i),x+78,769,title,20,'#3B258A',True)
        c.text('integration-body'+str(i),x+78,805,body,16,MUTED)
    c.edge('backend-partner',[(679,697),(679,724),(810,724),(810,756)],color='#1D4ED8')
    c.edge('worker-notify',[(1353,697),(1353,730),(1230,730),(1230,756)],color='#047857')
    c.edge('ai-llm',[(1690,697),(1690,736),(1650,736),(1650,756)],color='#7C3AED')

    # Private data subnet.
    c.box('data-band',24,902,1872,152,'#E5F4FF','#BAE0F8')
    c.text('data-title',43,929,['Máy chủ','dữ liệu'],23,'#0B3478',True)
    c.text('data-subtitle',43,993,['Private subnet','Không public'],15,'#294E82',True)
    data_items=[
      ('MariaDB Primary','database',['Read / write','Nguồn facts giao dịch']),
      ('DB Replica','database',['Standby / failover','Backup nhất quán']),
      ('Redis Cache','cpu',['Session · cache','Có thể tái tạo']),
      ('Redis Queue','cpu',['RQ jobs · pub/sub','Backlog / retry']),
      ('Object Storage','file-text',['File · ảnh · SOP','Signed URL · backup']),
      ('Vector DB','book-open',['Embedding + metadata','Citation về tài liệu nguồn'])]
    for i,(title,ico,body) in enumerate(data_items):
        x=164+i*284
        c.box('data'+str(i),x,921,268,112,'#FFFFFF','#CFE5F4')
        c.icon('data-icon'+str(i),ico,x+16,945,34,'#0B4F9C')
        c.text('data-title'+str(i),x+62,931,title,19,'#082C6A',True)
        c.text('data-body'+str(i),x+62,968,body,15,MUTED)
    c.edge('db-replication',[(432,977),(441,977)],color='#0B4F9C')

    # Cross-cutting DevSecOps / operations.
    c.box('ops-band',24,1074,1872,133,'#DDEFFF','#BFDBFE')
    c.text('ops-title',43,1097,['DevSecOps','& vận hành'],23,'#0B3478',True)
    ops=[
      ('CI/CD + Registry','cpu',['Test · scan · ký image','Staging → Production']),
      ('Secrets / KMS','shield-check',['Vault · rotation','Không secret trong image/Git']),
      ('Monitoring & Logs','chart-no-axes-combined',['Metrics · trace · correlation','Web · worker · DB · AI']),
      ('Backup & Restore','database',['DB + files + config + index','Mã hóa · restore test']),
      ('Release & Scaling','wrench',['Rolling / blue-green','Health gate · rollback'])]
    for i,(title,ico,body) in enumerate(ops):
        x=180+i*335
        c.box('ops'+str(i),x,1092,315,94,'#FFFFFF','#D1E4F4')
        c.icon('ops-icon'+str(i),ico,x+16,1117,32,'#1D4ED8')
        c.text('ops-title'+str(i),x+62,1102,title,19,'#082C6A',True)
        c.text('ops-body'+str(i),x+62,1138,body,15,MUTED)

    c.text('legend-title',42,1224,'Chú thích:',17,'#0B3478',True)
    c.edge('legend-main',[(183,1240),(257,1240)],color='#1D4ED8')
    c.text('legend-main-text',270,1225,'Luồng request / API',16,MUTED)
    c.edge('legend-private',[(500,1240),(574,1240)],color='#0284C7')
    c.text('legend-private-text',587,1225,'Kết nối private network',16,MUTED)
    c.box('legend-boundary',870,1227,28,24,'#EAF6FF','#BAE0F8')
    c.text('legend-boundary-text',913,1225,'Vùng triển khai / trust boundary',16,MUTED)
    c.text('footer',1392,1227,'AIS · Deployment Architecture v1.0 · Thiết kế production mục tiêu',14,MUTED)
    return c


def svg(c):
    root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width=str(c.w),height=str(c.h),viewBox=f'0 0 {c.w} {c.h}',role='img')
    ET.SubElement(root,'title').text=c.title
    ET.SubElement(root,'desc').text='Thiết kế mục tiêu AIS. Icon Lucide, chữ và đường nối vector.'
    defs=ET.SubElement(root,'defs')
    for color in {e['color'] for e in c.items if e['kind']=='edge'}:
        marker=ET.SubElement(defs,'marker',id='arrow'+color[1:],viewBox='0 0 10 10',refX='9',refY='5',markerWidth='7',markerHeight='7',orient='auto')
        ET.SubElement(marker,'path',d='M0 0 L10 5 L0 10z',fill=color)
    for e in c.items:
        if e['kind']=='box':
            attrs=dict(x=str(e['x']),y=str(e['y']),width=str(e['w']),height=str(e['h']),rx='14',fill=e['fill'],stroke=e['stroke'])
            attrs['stroke-width']='1.5'
            if e['dashed']: attrs['stroke-dasharray']='8 6'
            ET.SubElement(root,'rect',attrs)
        elif e['kind']=='text':
            for j,line in enumerate(e['lines']):
                attrs=dict(x=str(e['x']),y=str(e['y']+e['size']+j*e['size']*1.45),fill=e['color'])
                attrs.update({'font-size':str(e['size']),'font-family':'Segoe UI, Inter, Arial, sans-serif','font-weight':'700' if e['bold'] else '400'})
                ET.SubElement(root,'text',attrs).text=line
        elif e['kind']=='icon':
            icon=ET.fromstring(e['raw'])
            for a in ['x','y']: icon.set(a,str(e[a]))
            icon.set('width',str(e['w'])); icon.set('height',str(e['h'])); root.append(icon)
        else:
            d='M'+' L'.join(f'{x} {y}' for x,y in e['points'])
            ET.SubElement(root,'path',d=d,fill='none',stroke=e['color'],attrib={'stroke-width':'2.5','marker-end':'url(#arrow'+e['color'][1:]+')'})
    return ET.tostring(root,encoding='unicode',xml_declaration=True)


def drawio(canvases):
    doc=ET.Element('mxfile',host='app.diagrams.net',type='device')
    for c in canvases:
        diagram=ET.SubElement(doc,'diagram',id=c.name,name=c.title)
        model=ET.SubElement(diagram,'mxGraphModel',page='1',pageScale='1',pageWidth=str(c.w),pageHeight=str(c.h),grid='1',gridSize='8')
        root=ET.SubElement(model,'root'); ET.SubElement(root,'mxCell',id='0'); ET.SubElement(root,'mxCell',id='1',parent='0')
        for e in c.items:
            common={'id':e['id'],'parent':'1'}
            if e['kind']=='edge':
                points=e['points']
                style=f'edgeStyle=none;endArrow=block;endFill=1;strokeWidth=2.5;strokeColor={e["color"]};'
                for side,point in [('source',points[0]),('target',points[-1])]:
                    for node in c.items:
                        if node['kind']!='box' or not re.fullmatch(r'M\d{2}',node['id']): continue
                        x,y=point
                        if node['x']<=x<=node['x']+node['w'] and node['y']<=y<=node['y']+node['h']:
                            common[side]=node['id']
                            prefix='exit' if side=='source' else 'entry'
                            style+=f'{prefix}X={(x-node["x"])/node["w"]};{prefix}Y={(y-node["y"])/node["h"]};{prefix}Perimeter=0;'
                            break
                cell=ET.SubElement(root,'mxCell',**common,edge='1',style=style)
                geom=ET.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
                for which,p in [('sourcePoint',points[0]),('targetPoint',points[-1])]: ET.SubElement(geom,'mxPoint',x=str(p[0]),y=str(p[1]),attrib={'as':which})
                if len(points)>2:
                    arr=ET.SubElement(geom,'Array',attrib={'as':'points'})
                    for x,y in points[1:-1]: ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
                continue
            if e['kind']=='box':
                style=f'rounded=1;arcSize=8;fillColor={e["fill"]};strokeColor={e["stroke"]};strokeWidth=1.5;dashed={int(e["dashed"])};'; value=''
            elif e['kind']=='icon':
                data=base64.b64encode(e['raw'].encode()).decode()
                style=f'shape=image;imageAspect=0;aspect=fixed;image=data:image/svg+xml,{data};'; value=''
            else:
                style=f'text;html=0;align=left;verticalAlign=top;spacing=0;overflow=visible;whiteSpace=wrap;fontFamily=Segoe UI;fontSize={e["size"]};fontColor={e["color"]};fontStyle={int(e["bold"])};'; value='\n'.join(e['lines'])
            cell=ET.SubElement(root,'mxCell',**common,value=value,vertex='1',style=style)
            ET.SubElement(cell,'mxGeometry',x=str(e['x']),y=str(e['y']),width=str(e['w']),height=str(e['h']),attrib={'as':'geometry'})
    ET.indent(doc)
    return ET.tostring(doc,encoding='unicode',xml_declaration=True)


def validate_documents():
    root=OUT.parent
    report={'version':'3.0','date':'2026-10-08','files':[],'missing_links':[]}
    for p in sorted(root.rglob('*.md')):
        s=p.read_text(encoding='utf-8')
        report['files'].append({'path':p.relative_to(root).as_posix(),'words':len(s.split()),'bytes':len(s.encode()),'user_stories':sorted(set(re.findall(r'US-\d{2}',s))),'functions':sorted(set(re.findall(r'M\d{2}-F\d{2}',s)))})
        for target in re.findall(r'\]\(([^)]+)\)',s):
            if re.match(r'https?://|[A-Za-z]:/|#',target): continue
            if not (p.parent/target.split('#')[0]).exists(): report['missing_links'].append({'file':str(p),'target':target})
    report['total_words']=sum(f['words'] for f in report['files'])
    (root/'design_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert not report['missing_links'],report['missing_links']
    return report


def ai_gallery():
    names={'01':'Harness / component','02':'Orchestration / lifecycle','03':'State và memory','04':'RAG ingestion / retrieval','05':'Tool gateway contract','06':'Reasoning / planning / execution','07':'Security và HITL','08':'Observability / evaluation','09':'E2E scenarios'}
    cards=[]
    for p in sorted(OUT.glob('ai_*.svg')):
        code=p.name.split('_')[1]
        title=names.get(code,code)+' · hình '+p.stem[-2:]
        cards.append(f'<article><h2>{html.escape(title)}</h2><a href="{p.name}"><img src="{p.name}" alt="{html.escape(title)}"></a></article>')
    body='<!doctype html><html lang="vi"><meta charset="utf-8"><title>Agent Harness · Sổ sơ đồ chi tiết</title><style>body{margin:0;padding:24px;background:#f8fafc;color:#0f172a;font-family:Segoe UI,sans-serif}h1{font-size:28px}main{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}article{padding:18px;border:1px solid #e2e8f0;background:white;border-radius:12px}h2{font-size:18px}img{width:100%;height:540px;object-fit:contain}a{color:#1d4ed8}</style><h1>Agent Harness · Các sơ đồ chi tiết v3</h1><p>State, sequence, RAG, tool gate và evaluation. Mở từng SVG để đọc đầy đủ hoặc dùng sổ sơ đồ để phóng to.</p><p><a href="index.html">Mở sổ sơ đồ</a> · <a href="../ai_architecture/readme.md">Đọc 9 tài liệu AI</a></p><main>'+''.join(cards)+'</main></html>'
    (OUT/'ai_review.html').write_text(body,encoding='utf-8')


if __name__=='__main__':
    views=[overview(),journey(),relationships(),agent_harness(),deployment()]
    for c in views: (OUT/f'{c.name}.svg').write_text(svg(c),encoding='utf-8')
    (OUT/'thiet_ke_doanh_nghiep.drawio').write_text(drawio(views),encoding='utf-8')
    (OUT/'01_tong_quan_he_thong.drawio').write_text(drawio([views[0]]),encoding='utf-8')
    ai_gallery()
    r=validate_documents()
    print(f'Generated {len(views)} views; {len(r["files"])} documents, {r["total_words"]} words; links valid.')
