// تست رابط با jsdom (DOM شبیه‌سازی‌شده، نه مرورگر واقعی) و Worker جعلی
require('fake-indexeddb/auto');
const {JSDOM}=require('jsdom'),fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..');
let html=fs.readFileSync(root+'/index.html','utf8').replace('<script src="config.js"></script>','<script>window.DABIR_API="https://api.test";</script>');
let pass=0,fail=0;const t=(n,c)=>{c?pass++:fail++;console.log(c?'ok  ':'FAIL',n)};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function boot(setup,ls){
  const log=[];let state='queued';
  const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://u.github.io/dabir/',pretendToBeVisual:true,beforeParse(w){
    w.indexedDB=indexedDB;w.URL.createObjectURL=()=>'blob:x';w.URL.revokeObjectURL=()=>{};w.Audio=function(){return{}};w.Element.prototype.scrollIntoView=()=>{};w.scrollTo=()=>{};
    if(ls)for(const k in ls)w.localStorage.setItem(k,ls[k]);
    w.XMLHttpRequest=function(){const x={upload:{},open(m,u){x.u=u},setRequestHeader(k){log.push('H '+k)},send(b){log.push('PUT '+x.u.replace('https://api.test','')+' '+b.size);setTimeout(()=>{x.upload.onprogress({loaded:b.size});x.status=200;x.onload()},3)}};return x};
    w.fetch=async(u,o={})=>{const p=u.replace('https://api.test','');log.push((o.method||'GET')+' '+p.split('?')[0]);
      const R=(b,s=200)=>({ok:s<300,status:s,json:async()=>b});
      if(p=='/api/jobs')return R({id:'0123456789abcdef',rel:7,key:'ab'.repeat(32),chunk:64*1024*1024,parts:Math.ceil(JSON.parse(o.body).size/(64*1024*1024))});
      if(p.includes('/start'))return R({ok:true});
      if(p.startsWith('/api/jobs/'))return R(state=='done'?{state:'done',payload:{error:'فایل خراب است',finished:Math.floor(Date.now()/1000)}}:{state});
      return R({},404)};
    if(setup)setup(w)}});
  await sleep(500);return{dom,w:dom.window,d:dom.window.document,log,set:s=>state=s};
}
const pressed=d=>[...d.querySelectorAll('#lpl .tag[aria-pressed="true"]')].map(b=>b.textContent.trim());
const bigFile=(w,n='x.m4a')=>new w.File([new Uint8Array(130*1024*1024)],n);
(async()=>{
 let a=await boot();
 t('repo/token fields removed',!a.d.getElementById('rp')&&!a.d.getElementById('tk')&&!/توکن|user\/repo/.test(a.d.body.textContent));
 t('no checker stripes',!a.d.querySelector('.stairs')&&!/stairs/.test(html));
 t('no old <details> language picker',!a.d.querySelector('details#lp')&&!a.d.getElementById('lp'));
 t('default target = Persian only',JSON.stringify(pressed(a.d))==='["فارسی"]');
 t('21 interactive language tags (buttons)',a.d.querySelectorAll('#lpl button.tag').length===21);
 t('counter shows 1 selected',/۱/.test(a.d.getElementById('lps').textContent));
 const tags=[...a.d.querySelectorAll('#lpl .tag')];tags[1].onclick();tags[0].onclick();
 t('toggle saved to dabir_target_languages_v1',a.w.localStorage.getItem('dabir_target_languages_v1')==='["en"]'&&JSON.stringify(pressed(a.d))==='["English"]');
 a.d.getElementById('lclr').onclick();t('clear selection',pressed(a.d).length===0&&a.w.localStorage.getItem('dabir_target_languages_v1')==='[]');
 let b=await boot(null,{dabir_target_languages_v1:'["en","de"]'});t('saved selection restored',JSON.stringify(pressed(b.d))==='["English","Deutsch"]');
 let c=await boot(null,{dabir_target_languages_v1:'{bad json'});t('corrupt storage -> Persian',JSON.stringify(pressed(c.d))==='["فارسی"]');
 let e=await boot(null,{dabir_target_languages_v1:'[]'});t('empty choice respected',pressed(e.d).length===0&&/بدون ترجمه/.test(e.d.getElementById('lps').textContent));
 // رابط دوزبانه
 t('default UI is Persian rtl',a.d.documentElement.dir==='rtl'&&a.d.documentElement.lang==='fa'&&a.d.getElementById('go').textContent==='شروع پردازش');
 a.d.querySelector('.lsw button[data-l="en"]').click();
 t('switch to English: ltr + translated + saved',a.d.documentElement.dir==='ltr'&&a.d.documentElement.lang==='en'&&a.d.getElementById('go').textContent==='Start processing'&&a.w.localStorage.getItem('dabir_ui_lang_v1')==='en'&&a.d.title.startsWith('Dabir'));
 t('English counter',/selected|No translation/.test(a.d.getElementById('lps').textContent));
 let en=await boot(null,{dabir_ui_lang_v1:'en'});t('English restored after reload',en.d.documentElement.dir==='ltr'&&en.d.getElementById('go').textContent==='Start processing');
 a.d.querySelector('.lsw button[data-l="fa"]').click();t('switch back to Persian',a.d.documentElement.dir==='rtl'&&a.d.getElementById('go').textContent==='شروع پردازش');
 const D=a.w.eval('D'),kf=Object.keys(D.fa).sort().join(),ke=Object.keys(D.en).sort().join();
 t('fa and en dictionaries have identical keys',kf===ke);
 const ph=s=>(s.match(/\{\d\}/g)||[]).sort().join();
 t('placeholders match between languages',Object.keys(D.fa).every(k=>ph(D.fa[k])===ph(D.en[k])));
 t('every data-i18n key exists',[...a.d.querySelectorAll('[data-i18n],[data-i18n-ph]')].every(x=>(x.dataset.i18n||x.dataset.i18nPh)in D.fa));
 // آپلود ۱۳۰ مگابایت از طریق Worker جعلی
 a.d.getElementById('file').onchange({target:{files:[bigFile(a.w)]}});
 t('file card shown with ext badge',!a.d.getElementById('fc').hidden&&a.d.getElementById('fx').textContent==='M4A');
 a.d.getElementById('go').click();await sleep(1500);
 const puts=a.log.filter(l=>l.startsWith('PUT'));
 t('chunked upload: 3 parts via Worker',puts.length===3&&puts[0].includes('/api/jobs/0123456789abcdef/parts/0?rel=7'));
 t('X-Key header sent, no Authorization',a.log.includes('H X-Key')&&!a.log.includes('H Authorization'));
 t('start called after last part',a.log.indexOf('POST /api/jobs/0123456789abcdef/start')>a.log.lastIndexOf(puts[2]));
 t('item queued in library',/صف/.test(a.d.querySelector('.it .sx').textContent)&&a.d.querySelector('.it .bd').classList.contains('queued'));
 t('file card cleared after start',a.d.getElementById('fc').hidden);
 a.set('running');await sleep(15500);t('status running shown',/در حال پردازش/.test(a.d.querySelector('.it .sx').textContent));
 a.set('done');await sleep(15500);t('bot error surfaced',/فایل خراب است/.test(a.d.querySelector('.it .sx').textContent)&&a.d.querySelector('.it .bd').classList.contains('error'));
 // نتیجه، SRT و کپی
 let r=await boot();const res={language:'fa',text:'سلام',translations:{en:'hello'},tlines:{en:['hello']},segments:[{s:0,e:1.5,t:'سلام',sp:null}],warnings:[]};
 r.w.eval('show('+JSON.stringify(res)+',{targets:["fa","de"]})');
 const tas=r.d.querySelectorAll('#outs textarea');
 t('result blocks with direction',tas.length===2&&tas[0].dir==='rtl'&&tas[1].dir==='ltr');
 t('notes: same-language + missing translation',/ترجمه لازم نبود/.test(r.d.getElementById('wr').textContent)&&/Deutsch/.test(r.d.getElementById('wr').textContent));
 t('SRT builder correct',r.w.eval('srt([{s:0,e:1.5,t:"a",sp:null}],null)').startsWith('1\n00:00:00,000 --> 00:00:01,500\na'));
 t('result has copy, TXT and SRT buttons',r.d.querySelectorAll('#outs details')[0].querySelectorAll('button').length===3);
 r.d.querySelector('.lsw button[data-l="en"]').click();t('result re-rendered in English',/Original text/.test(r.d.getElementById('outs').textContent)&&/Download SRT/.test(r.d.getElementById('outs').textContent));
 r.w.navigator.clipboard={writeText:async()=>{throw Error('denied')}};r.w.document.execCommand=()=>false;
 const btn=r.d.querySelector('#outs button');await r.w.eval('copy')(r.d.querySelector('textarea'),btn);t('clipboard failure reported honestly',/Copy failed/.test(btn.textContent));
 r.w.navigator.clipboard={writeText:async()=>{}};await r.w.eval('copy')(r.d.querySelector('textarea'),btn);t('clipboard success state',/Copied/.test(btn.textContent)&&btn.classList.contains('ok'));
 // حذف با تأیید
 let k=await boot(null,{});await k.w.eval('(async()=>{items.unshift({id:"q1",name:"a.mp3",size:5e6,created:Date.now(),status:"done",expiresAt:Date.now()+18e5,result:{}});render()})()');
 const base=k.d.querySelectorAll('.it').length;k.d.querySelector('.it .btn.bad').click();t('delete asks for confirmation',!k.d.getElementById('cf').hidden);
 k.d.getElementById('cfn').click();t('"No" keeps item',k.d.querySelectorAll('.it').length===base&&k.d.getElementById('cf').hidden);
 k.d.querySelector('.it .btn.bad').click();k.d.getElementById('cfy').click();await sleep(300);t('"Yes" deletes item',k.d.querySelectorAll('.it').length===base-1);
 // فشرده‌سازی
 let z=await boot(w=>{w.lamejs={Mp3Encoder:function(){}}});
 t('compress options hidden by default',z.d.getElementById('cpo').hidden===true&&!z.d.getElementById('cp').checked);
 z.d.getElementById('cp').checked=true;z.d.getElementById('cp').onchange();
 t('compress options shown and saved',z.d.getElementById('cpo').hidden===false&&JSON.parse(z.w.localStorage.getItem('dabir_compress_v1')).on===true);
 let z2=await boot(null,{dabir_compress_v1:'{"on":true,"k":24}'});t('compress choice restored',z2.d.getElementById('cp').checked&&z2.d.querySelector('input[name=cpl]:checked').value==='24');
 z.w.compressAudio=async(f,kb,onp)=>{onp(1);return new z.w.File([new Uint8Array(5*1024*1024)],'voice-dabir.mp3')};
 z.d.getElementById('file').onchange({target:{files:[bigFile(z.w,'voice.m4a')]}});z.d.getElementById('go').click();await sleep(1500);
 let pu=z.log.filter(l=>l.startsWith('PUT'));
 t('compressed upload: 1 part of 5 MB instead of 3',pu.length===1&&pu[0].endsWith(String(5*1024*1024)));
 t('library shows compression result',/رسید/.test(z.d.querySelector('.it .nm').textContent)&&/به .* رسید/.test(z.d.getElementById('st').textContent));
 let y=await boot(w=>{w.lamejs={Mp3Encoder:function(){}}});
 y.d.getElementById('cp').checked=true;y.d.getElementById('file').onchange({target:{files:[bigFile(y.w,'voice.m4a')]}});y.d.getElementById('go').click();await sleep(1500);
 pu=y.log.filter(l=>l.startsWith('PUT'));t('compression failure falls back to original (3 parts)',pu.length===3&&/ممکن نشد/.test(y.d.getElementById('st').textContent));
 let x=await boot();x.w.compressAudio=async()=>new x.w.File([new Uint8Array(140*1024*1024)],'b.mp3');
 x.d.getElementById('cp').checked=true;x.d.getElementById('file').onchange({target:{files:[bigFile(x.w,'v.m4a')]}});x.d.getElementById('go').click();await sleep(1500);
 pu=x.log.filter(l=>l.startsWith('PUT'));t('larger compressed file is discarded (original sent)',pu.length===3);
 // بدون پیکربندی API
 html=html.replace('window.DABIR_API="https://api.test";','window.DABIR_API="";');let n=await boot();n.d.getElementById('go').click();t('unconfigured API shows clear message',/پیکربندی نشده/.test(n.d.getElementById('st').textContent));
 console.log(`\n${pass} passed, ${fail} failed`);process.exit(fail?1:0)})();
