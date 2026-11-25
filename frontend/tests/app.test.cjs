// Unit-level DOM harness; this does not replace visual browser QA.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../app.js'),'utf8');
const eventId = '33333333-3333-4333-8333-333333333333';
const userId = '11111111-1111-4111-8111-111111111111';
const event = {id:eventId,title:'Design <script>alert(1)</script>',capacity:12,status:'open',organizer_id:userId};
function setup(responder,hash='#/events',savedUser='') {
  const nodes = new Map();
  const node = selector => {
    if(!nodes.has(selector)) nodes.set(selector,{innerHTML:'',textContent:'',value:'',dataset:{},handlers:{},addEventListener(type,fn){this.handlers[type]=fn;},setAttribute(){},removeAttribute(){},focus(){},showModal(){},close(){}});
    return nodes.get(selector);
  };
  const calls = [];
  const context = vm.createContext({document:{querySelector:node,querySelectorAll:()=>[],title:''},location:{hash},sessionStorage:{getItem:()=>savedUser,setItem(){}},window:{addEventListener(){},scrollTo(){}},AbortController,Intl,URL,Blob,setTimeout:()=>0,clearTimeout(){},fetch:async(url,options)=>{calls.push({url,options});const result = await responder(url,options);return {ok:result.status<400,status:result.status,json:async()=>result.body};}});
  vm.runInContext(source,context);
  return {node,calls,context,run:expression=>vm.runInContext(expression,context)};
}
const tick = () => new Promise(resolve=>setImmediate(resolve));
test('event list escapes server content and filters by title',async()=>{
  const app=setup(()=>({status:200,body:{data:[event]}})); await tick();
  assert.match(app.node('#event-results').innerHTML,/Design &lt;script&gt;/);
  assert.doesNotMatch(app.node('#event-results').innerHTML,/<script>/);
  app.node('#event-search').value='no such event';app.node('#event-search').handlers.input();
  assert.match(app.node('#event-results').innerHTML,/No matching events/);
});
test('registration sends exactly the backend contract and displays confirmation',async()=>{
  const app=setup((url,options)=>({status:options.method==='POST'?201:200,body:{data:options.method==='POST'?{id:'registration'}:event}}),`#/events/${eventId}`,userId);await tick();
  await app.node('#register').handlers.click();
  const write=app.calls.find(c=>c.options.method==='POST');
  assert.equal(write.url,'/api/registrations');
  assert.deepEqual(JSON.parse(write.options.body),{user_id:userId,event_id:eventId});
  assert.match(app.node('#registration-result').innerHTML,/Your place is confirmed/);
  assert.equal(app.node('#register').disabled,true);
});
test('capacity conflict is surfaced and enables another attempt',async()=>{
  const app=setup((url,options)=>options.method==='POST'?{status:409,body:{error:'Event capacity has been reached'}}:{status:200,body:{data:event}},`#/events/${eventId}`,userId);await tick();
  await app.node('#register').handlers.click();
  assert.match(app.node('#registration-result').innerHTML,/Event capacity has been reached/);
  assert.equal(app.node('#register').disabled,false);
});
test('personal registrations use the selected user and nested event',async()=>{
  const app=setup(()=>({status:200,body:{data:[{id:'registration',event_id:eventId,events:event,created_at:'2026-11-25T10:00:00Z'}]}}),'#/registrations',userId);await tick();
  assert.equal(app.calls[0].url,`/api/me/registrations?user_id=${userId}`);
  assert.match(app.node('#main').innerHTML,/Registration confirmed/);
});
test('missing profile never requests personal data',async()=>{
  const app=setup(()=>{throw Error('Should not fetch');},'#/registrations');await tick();
  assert.equal(app.calls.length,0);assert.match(app.node('#main').innerHTML,/Set user ID/);
});
test('attendee page fetches detail and guest list and handles unlimited capacity',async()=>{
  const app=setup(url=>({status:200,body:{data:url.endsWith('/registrations')?[]:{...event,capacity:null}}}),`#/organizer/${eventId}`);await tick();
  assert.equal(app.calls.length,2);assert.match(app.node('#main').innerHTML,/No limit/);assert.match(app.node('#attendee-results').innerHTML,/guest list starts here/);
});
test('network failure produces a retry action',async()=>{
  const app=setup(()=>{throw Error('offline');});await tick();
  assert.match(app.node('#main').innerHTML,/Unable to reach the server/);assert.equal(typeof app.node('#retry').handlers.click,'function');
});
test('CSV export neutralizes formulas and escapes quotes',async()=>{
  const app=setup(()=>({status:200,body:{data:[]}}));await tick();
  assert.equal(app.run('csvCell("=1+1")'),'"\'=1+1"');
  assert.equal(app.run('csvCell(\'a"b\')'),'"a""b"');
});
