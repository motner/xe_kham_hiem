const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'..','firmware','web','index.html'),'utf8');
class Element {
 constructor(id=''){this.id=id;this.value='';this.textContent='';this.dataset={};this.disabled=false;this.style={};this.children=[];this.attrs={};this.events={};this.tagName='DIV';this.classes=new Set();this.capture=null;this.classList={add:c=>this.classes.add(c),remove:c=>this.classes.delete(c),toggle:(c,v)=>v?this.classes.add(c):this.classes.delete(c)};}
 addEventListener(n,fn){(this.events[n]??=[]).push(fn)}
 trigger(n,e={}){for(const f of this.events[n]||[])f({target:this,preventDefault(){},...e})}
 setAttribute(k,v){this.attrs[k]=v}
 removeAttribute(k){delete this.attrs[k];if(k==='src')this.src='';}
 focus(){}
 getBoundingClientRect(){return {width:240,height:240,left:0,top:0}}
 setPointerCapture(id){this.capture=id}
 hasPointerCapture(id){return this.capture===id}
 releasePointerCapture(id){this.capture=null;this.trigger('lostpointercapture',{pointerId:id})}
 append(...e){this.children.push(...e)}
 prepend(e){e.parent=this;this.children.unshift(e)}
 get lastChild(){return this.children.at(-1)}
 remove(){this.parent.children.pop()}
}
const els={};for(const m of html.matchAll(/id="([^"]+)"/g))els[m[1]]=new Element(m[1]);
for(let i=0;i<4;i++)for(const kind of ['rpm','pulses','bar'])els['wheel-'+kind+'-'+i]=new Element();
const presets=[];
for(const id of ['diameter','ppr'])els[id].tagName='INPUT';els.mode.tagName='SELECT';
const doc=new Element(),win=new Element();doc.getElementById=id=>{assert(els[id],id);return els[id]};doc.createElement=()=>new Element();doc.querySelectorAll=sel=>sel==='#diameter,#ppr,#reset'?['diameter','ppr','reset'].map(i=>els[i]):[];
let now=0,fetches=0;
const savedLogin=new Map();
const sessionStorage={getItem:key=>savedLogin.get(key)||null,setItem:(key,value)=>savedLogin.set(key,value),removeItem:key=>savedLogin.delete(key)};
const ctx={document:doc,window:win,location:{protocol:'file:'},performance:{now:()=>now},Date,console,URL,AbortController,sessionStorage,setInterval(){},setTimeout(){return 1},clearTimeout(){},fetch:async()=>{fetches++;return{ok:true,json:async()=>({device:'esp32-web',motor_ready:false,encoder_ready:false})}}};vm.createContext(ctx);vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
const run=s=>vm.runInContext(s,ctx),joy=els.joystick;
assert.equal(run('state.mode'),'demo');assert.equal(fetches,0);assert.equal(joy.attrs['aria-disabled'],'false');
run('updateJoystick(.02,.02)');assert.equal(run('state.left'),0);assert.equal(els['joystick-power'].textContent,'0%');
joy.trigger('pointerdown',{pointerId:1,button:0,clientX:120,clientY:48});assert.equal(run('state.left'),120);assert.equal(run('state.right'),120);
joy.trigger('pointerdown',{pointerId:2,button:0,clientX:192,clientY:120});assert.equal(run('state.pointerId'),1);
joy.trigger('pointermove',{pointerId:2,clientX:192,clientY:120});assert.equal(run('state.right'),120);
joy.trigger('pointermove',{pointerId:1,clientX:156,clientY:84});assert(run('state.left')>run('state.right'));assert.equal(run('state.right'),0);
joy.trigger('pointermove',{pointerId:1,clientX:120,clientY:84});assert(run('state.left')>0&&run('state.left')<120);
joy.trigger('pointermove',{pointerId:1,clientX:5000,clientY:120});assert.equal(run('state.left'),120);assert.equal(run('state.right'),-120);assert.equal(els['joystick-power'].textContent,'100%');
for(let i=0;i<30;i++){now+=200;run('tick()')}
assert(+els.rpm.textContent>70);assert(+els.distance.textContent>0);assert(run('state.pulses.every(p=>p>0)'));assert(els['chart-rpm'].attrs.d.startsWith('M'));
joy.trigger('pointerup',{pointerId:2});assert.equal(run('state.pointerId'),1);
joy.trigger('pointerup',{pointerId:1});assert.equal(run('state.left'),0);assert.equal(run('state.right'),0);assert.equal(joy.capture,null);assert.equal(els['joystick-knob'].style.transform,'translate(0px,0px)');
win.trigger('keydown',{key:'ArrowUp'});win.trigger('keydown',{key:'ArrowRight'});assert.equal(run('state.right'),0);assert(run('state.left')>0);
win.trigger('keyup',{key:'ArrowRight'});assert.equal(run('state.right'),120);win.trigger('keyup',{key:'ArrowUp'});assert.equal(run('state.left'),0);
for(const ev of ['pointercancel','lostpointercapture']){joy.trigger('pointerdown',{pointerId:3,button:0,clientX:120,clientY:48});joy.trigger(ev,{pointerId:3});assert.equal(run('state.left'),0);}
for(const ev of ['blur','pagehide']){run('updateJoystick(0,1)');win.trigger(ev);assert.equal(run('state.left'),0)}
run('updateJoystick(0,1)');win.trigger('keydown',{code:'Space'});assert.equal(run('state.left'),0);
run('updateJoystick(0,.55)');assert(Math.abs(run('state.left')-60)<.001);
assert.equal(run('state.maxRpm'),120);
els.mode.value='live';run('changeMode()');assert.equal(joy.attrs['aria-disabled'],'true');assert.equal(run('state.left'),0);joy.trigger('pointerdown',{pointerId:5,button:0,clientX:120,clientY:48});assert.equal(run('state.left'),0);assert.equal(els.rpm.textContent,'—');assert.equal(fetches,0);
console.log('PASS: pointer drag, analog speed, deadzone, differential mixing, bounds, multi-touch, diagonal keys, release/cancel/blur/space stop, simulation chart and live lock.');
assert.equal(els['login-screen'].hidden,false);assert.equal(els.dashboard.hidden,true);
assert.equal(els['camera-start'].disabled,true);
run("state.authToken='camera-test';controlAvailability()");
// Camera is opt-in, independent from motor arming, and disabled in demo mode.
assert.equal(els['camera-image'].src,'');
assert.equal(els['camera-url'].value,'http://192.168.4.2:8080/stream.mjpg');
const beforeCameraFetches=fetches;
const beforeCameraSequence=run('state.sequence');
for(const invalid of ['bad address','javascript:alert(1)','ftp://192.168.4.2/video']){
  els['camera-url'].value=invalid;els['camera-start'].trigger('click');
  assert.equal(els['camera-image'].src,'');
  assert.equal(els['camera-status'].textContent,'Địa chỉ không hợp lệ');
}
els['camera-url'].value='http://192.168.4.2:8080/stream.mjpg';
els['camera-start'].trigger('click');
assert.equal(els['camera-image'].src,els['camera-url'].value);
assert.equal(els['camera-image'].hidden,false);
assert.equal(run('state.session'),null);assert.equal(run('state.sequence'),beforeCameraSequence);
assert.equal(fetches,beforeCameraFetches);
els['camera-image'].onload();assert.equal(els['camera-status'].textContent,'Đã nhận hình');
els['camera-image'].onerror();assert.equal(els['camera-status'].textContent,'Không mở được camera');
assert.equal(els['camera-image'].src,'');
els['camera-start'].trigger('click');els['camera-stop'].trigger('click');
assert.equal(els['camera-image'].src,'');assert.equal(els['camera-image'].hidden,true);
els['camera-start'].trigger('click');win.trigger('pagehide');assert.equal(els['camera-image'].src,'');
els['camera-start'].trigger('click');els.mode.value='demo';run('changeMode()');
assert.equal(els['camera-image'].src,'');assert.equal(els['camera-start'].disabled,true);
els['camera-start'].trigger('click');assert.equal(els['camera-image'].src,'');
els.mode.value='live';run('changeMode()');
console.log('PASS: camera URL validation, manual start/stop, load/error, no motor arming/API traffic, page cleanup and demo isolation.');
run('clearLogin()');


(async()=>{
  const requests=[];
  ctx.location.protocol='http:';
  const status={device:'esp32-web',motor_ready:true,encoder_ready:true,armed:true,max_rpm:120,loop_ms:50,wheels:Array.from({length:4},(_,i)=>({name:['front_left','front_right','rear_left','rear_right'][i],rpm:60+i,target_rpm:80,pulses:100+i,distance_m:.5,diameter_mm:65,counts_per_rev:100}))};
  ctx.fetch=async(path,opts={})=>{requests.push({path,headers:opts.headers,body:opts.body&&JSON.parse(opts.body)});return{ok:true,json:async()=>path==='/api/status'?status:path==='/api/login'?{token:'login-token',username:'admin'}:path==='/api/arm'?{session:'test-session'}:{ok:true}};};
  await run('poll()');assert.equal(requests.length,0);
  els['login-username'].value='admin';els['login-password'].value='wrong';
  const normalFetch=ctx.fetch;
  ctx.fetch=async()=>({ok:false,status:401,json:async()=>({error:'invalid_credentials'})});
  await els['login-form'].events.submit[0]({preventDefault(){}});
  assert.equal(run('state.authToken'),null);assert.equal(els.dashboard.hidden,true);
  assert(els['login-message'].textContent.includes('không đúng'));
  ctx.fetch=normalFetch;els['login-password'].value='test-password';
  await els['login-form'].events.submit[0]({preventDefault(){}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.authToken'),'login-token');assert.equal(els.dashboard.hidden,false);
  assert.equal(els['login-screen'].hidden,true);assert.equal(els['login-password'].value,'');
  assert.equal(JSON.parse(savedLogin.get('esp32-login')).token,'login-token');
  assert(!savedLogin.get('esp32-login').includes('test-password'));
  assert.equal(run('state.session'),null);assert.equal(requests.filter(r=>r.path==='/api/arm').length,0);
  assert.equal(requests.find(r=>r.path==='/api/status').headers.Authorization,'Bearer login-token');
  await run('poll()');assert.equal(run('state.ready'),true);assert.equal(els.rpm.textContent,'61.5');assert.equal(joy.attrs['aria-disabled'],'false');
  // Real firmware returns FL, RR, RL, FR. Cards must use identity, not position.
  const originalWheels=status.wheels;
  status.wheels=[originalWheels[0],originalWheels[3],originalWheels[2],originalWheels[1]];
  await run('poll()');
  assert.equal(els['wheel-rpm-1'].textContent,'61.0');
  assert.equal(els['wheel-rpm-3'].textContent,'63.0');
  assert.equal(els['wheel-pulses-1'].textContent,'101');
  assert.equal(els['wheel-pulses-3'].textContent,'103');
  // A hidden tab sends no status requests; diagnostic ping and status never overlap.
  let beforeIdle=requests.length;doc.hidden=true;await run('poll()');
  assert.equal(requests.length,beforeIdle);doc.hidden=false;
  run('bootChecking=true');await run('poll()');assert.equal(requests.length,beforeIdle);run('bootChecking=false');
  run('polling=true');await run('pollBoot()');assert.equal(requests.length,beforeIdle);run('polling=false');
  // One lost status reply keeps driving; repeated failures stop the lease and need a new gesture.
  run("state.session='status-timeout';state.direction='joystick';state.y=1;state.left=80;state.right=80");
  ctx.fetch=async(path,opts)=>{if(path==='/api/status'){const e=new Error('timeout');e.name='AbortError';throw e;}return normalFetch(path,opts)};
  await run('poll()');assert.equal(run('state.session'),'status-timeout');assert.equal(run('state.connected'),true);
  await run('poll()');assert.equal(run('state.session'),'status-timeout');
  await run('poll()');assert.equal(run('state.session'),null);assert.equal(run('state.left'),0);
  assert(els['notice-text'].textContent.includes('2,5 giây'));
  ctx.fetch=normalFetch;beforeIdle=requests.filter(r=>r.path==='/api/arm').length;
  await run('poll()');assert.equal(run('state.connected'),true);
  assert.equal(requests.filter(r=>r.path==='/api/arm').length,beforeIdle);
  assert.equal(els.arm,undefined);assert.equal(run('state.session'),null);
  run('updateJoystick(0,1)');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'test-session');
  const command=requests.filter(r=>r.path==='/api/control').at(-1).body;
  assert.equal(requests.filter(r=>r.path==='/api/control').at(-1).headers.Authorization,'Bearer login-token');
  assert.equal(command.throttle,1);assert.equal(command.max_rpm,120);assert.equal(command.session,'test-session');
  // An isolated wheel stall stays visible without releasing the healthy wheels.
  status.stop_all_on_encoder_stall=false;
  status.wheel_faults=['encoder_or_stall:front_left'];
  const stopsBeforeWheelFault=requests.filter(r=>r.path==='/api/stop').length;
  await run('poll()');
  assert.equal(run('state.session'),'test-session');assert.equal(run('state.ready'),true);
  assert.equal(requests.filter(r=>r.path==='/api/stop').length,stopsBeforeWheelFault);
  assert(els['notice-title'].textContent.includes('Chế độ thử'));
  assert(els['notice-text'].textContent.includes('encoder_or_stall:front_left'));
  status.stop_all_on_encoder_stall=true;status.wheel_faults=[];
  const controlsBeforeRelease=requests.filter(r=>r.path==='/api/control').length;
  const stopsBeforeRelease=requests.filter(r=>r.path==='/api/stop').length;
  run('stop()');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),null);
  assert.equal(requests.filter(r=>r.path==='/api/stop').length,stopsBeforeRelease+1);
  for(let i=0;i<4;i++)await run('sendControl()');
  assert.equal(requests.filter(r=>r.path==='/api/control').length,controlsBeforeRelease);
  assert.equal(requests.filter(r=>r.path==='/api/stop').length,stopsBeforeRelease+1);
  run('emergencyStop()');assert.equal(run('state.session'),null);assert.equal(joy.attrs['aria-disabled'],'false');
  assert(requests.some(r=>r.path==='/api/stop'));
  // Idle heartbeats after STOP must not reacquire control or move the robot.
  const armsAfterStop=requests.filter(r=>r.path==='/api/arm').length;
  await run('sendControl()');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(requests.filter(r=>r.path==='/api/arm').length,armsAfterStop);
  // Release sends STOP immediately, even while a previous movement request is pending.
  run('updateJoystick(0,.5)');await new Promise(resolve=>setImmediate(resolve));
  let resolveMovement;
  ctx.fetch=async(path,opts={})=>path==='/api/control'?await new Promise(resolve=>{resolveMovement=resolve;}):normalFetch(path,opts);
  const oldMovement=run('sendControl()');await new Promise(resolve=>setImmediate(resolve));
  const immediateStops=requests.filter(r=>r.path==='/api/stop').length;
  run('stop()');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),null);
  assert.equal(requests.filter(r=>r.path==='/api/stop').length,immediateStops+1);
  resolveMovement({ok:true,json:async()=>({ok:true})});await oldMovement;
  const armsAfterRelease=requests.filter(r=>r.path==='/api/arm').length;
  for(let i=0;i<4;i++)await run('sendControl()');
  assert.equal(requests.filter(r=>r.path==='/api/arm').length,armsAfterRelease);
  assert.equal(run('state.direction'),'stop');ctx.fetch=normalFetch;
  // Returning to the dead zone also retires the lease and requires a new gesture.
  run('updateJoystick(0,.5)');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'test-session');
  const centerStops=requests.filter(r=>r.path==='/api/stop').length;
  run('updateJoystick(0,0)');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),null);
  assert.equal(requests.filter(r=>r.path==='/api/stop').length,centerStops+1);
  // A pending automatic acquisition must be released if STOP happens before its reply.
  let resolveArm;
  ctx.fetch=async(path)=>path==='/api/arm'?await new Promise(resolve=>{resolveArm=resolve;}):{ok:true,json:async()=>({ok:true})};
  const armPromise=run("state.direction='joystick';state.y=1;sendControl()");
  await new Promise(resolve=>setImmediate(resolve));
  run('emergencyStop()');
  resolveArm({ok:true,json:async()=>({session:'late-session'})});await armPromise;
  assert.equal(run('state.session'),null);assert.equal(run('state.direction'),'stop');
  assert.equal(joy.attrs['aria-disabled'],'false');
  // A new gesture after STOP acquires control again without any arm button.
  ctx.fetch=normalFetch;run('updateJoystick(0,1)');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'test-session');
  assert.equal(requests.filter(r=>r.path==='/api/control').at(-1).body.throttle,1);
  // Releasing the joystick while acquisition is pending must cancel that motion.
  run('emergencyStop()');
  ctx.fetch=async(path)=>path==='/api/arm'?await new Promise(resolve=>{resolveArm=resolve;}):{ok:true,json:async()=>({ok:true})};
  const releasePromise=run("state.direction='joystick';state.y=1;sendControl()");
  await new Promise(resolve=>setImmediate(resolve));
  run('stop()');resolveArm({ok:true,json:async()=>({session:'released-before-reply'})});await releasePromise;
  assert.equal(run('state.session'),null);assert.equal(run('state.y'),0);
  // A new drag before a cancelled acquisition replies must use the new direction/power.
  let firstAcquisition=true;
  ctx.fetch=async(path,opts={})=>{
    if(path==='/api/arm'&&firstAcquisition){firstAcquisition=false;return await new Promise(resolve=>{resolveArm=resolve;});}
    return normalFetch(path,opts);
  };
  const oldDrag=run("state.direction='joystick';state.y=1;sendControl()");
  await new Promise(resolve=>setImmediate(resolve));
  run('stop();updateJoystick(0,.5)');
  resolveArm({ok:true,json:async()=>({session:'old-drag'})});await oldDrag;
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'test-session');
  const latestPower=requests.filter(r=>r.path==='/api/control').at(-1).body.throttle;
  assert(latestPower>0&&latestPower<.6);
  // A fresh gesture waits for the prior STOP response before acquiring a new lease.
  let resolveStop;
  ctx.fetch=async(path,opts={})=>path==='/api/stop'?await new Promise(resolve=>{resolveStop=resolve;}):normalFetch(path,opts);
  run('emergencyStop()');
  const beforeDelayedStop=requests.filter(r=>r.path==='/api/arm').length;
  run('updateJoystick(0,1)');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(requests.filter(r=>r.path==='/api/arm').length,beforeDelayedStop);
  resolveStop({ok:true,json:async()=>({ok:true})});await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'test-session');
  // A failed command releases the session and resets the joystick.
  run("state.session='failed-session';state.ready=true;state.connected=true;controlAvailability()");
  ctx.fetch=async()=>{throw new Error('network failure')};
  await run('sendControl()');assert.equal(run('state.session'),null);assert.equal(run('state.left'),0);
  // A real local deadline replaces the browser's unhelpful AbortError and stops motion.
  const originalSetTimeout=ctx.setTimeout,originalClearTimeout=ctx.clearTimeout;
  let expireRequest,clearedDeadline=0;
  ctx.setTimeout=(callback,ms)=>{assert.equal(ms,400);expireRequest=callback;return 'deadline'};
  ctx.clearTimeout=id=>{if(id==='deadline')clearedDeadline++};
  ctx.fetch=async(path,opts)=>path==='/api/control'?await new Promise((resolve,reject)=>{
    opts.signal.addEventListener('abort',()=>{const e=new Error('signal is aborted without reason');e.name='AbortError';reject(e)},{once:true});
  }):normalFetch(path,opts);
  const timedCommand=run("state.session='timeout-lease';state.direction='joystick';state.y=1;state.left=80;state.right=80;sendControl()");
  await new Promise(resolve=>setImmediate(resolve));
  // A lost command retries at once while the firmware watchdog still guards the car.
  expireRequest();await timedCommand;await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'timeout-lease');assert.equal(run('state.direction'),'joystick');
  expireRequest();await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),'timeout-lease');
  const expireCommand=expireRequest;ctx.setTimeout=originalSetTimeout;
  expireCommand();await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.session'),null);assert.equal(run('state.left'),0);
  assert.equal(run('state.direction'),'stop');assert.equal(clearedDeadline,3);
  assert(els.events.children.some(row=>row.children[1].textContent.includes('/api/control sau 400 ms')));
  assert(!els.events.children.some(row=>row.children[1].textContent.includes('signal is aborted without reason')));
  // The deadline also covers a response body which stalls after HTTP headers arrive.
  ctx.setTimeout=(callback,ms)=>{assert.equal(ms,1200);expireRequest=callback;return 'deadline'};
  ctx.fetch=async(path,opts)=>({ok:true,json:()=>new Promise((resolve,reject)=>{
    opts.signal.addEventListener('abort',()=>{const e=new Error('signal is aborted without reason');e.name='AbortError';reject(e)},{once:true});
  })});
  const stalledBody=run("requestJSON('/api/status',{},1200)");
  const bodyCheck=assert.rejects(stalledBody,e=>e.name==='TimeoutError'&&e.timeoutMs===1200&&e.path==='/api/status');
  await new Promise(resolve=>setImmediate(resolve));expireRequest();await bodyCheck;
  assert.equal(clearedDeadline,4);
  ctx.setTimeout=originalSetTimeout;ctx.clearTimeout=originalClearTimeout;
  console.log('PASS: command deadline stops and releases the lease, localized timeout includes endpoint/deadline, stalled JSON body is bounded.');
  // Logout stops the active lease, clears saved credentials and rejects a late arm.
  ctx.fetch=normalFetch;
  run("state.session='logout-session';state.ready=true;state.connected=true;controlAvailability()");
  els.logout.trigger('click');await new Promise(resolve=>setImmediate(resolve));
  assert.equal(run('state.authToken'),null);assert.equal(run('state.session'),null);
  assert.equal(els.dashboard.hidden,true);assert.equal(savedLogin.has('esp32-login'),false);
  assert(requests.some(r=>r.path==='/api/logout'&&r.headers.Authorization==='Bearer login-token'));
  // A token invalidated by an ESP32 restart returns to the form and stops motion.
  run("state.authToken='expired';state.username='admin';state.session='expired-lease';state.ready=true;state.connected=true;loginView();controlAvailability();startCamera()");
  ctx.fetch=async()=>({ok:false,status:401,json:async()=>({error:'login_required'})});
  await run('poll()');assert.equal(run('state.authToken'),null);assert.equal(run('state.session'),null);
  assert.equal(els['camera-image'].src,'');assert.equal(els.dashboard.hidden,true);
  assert(els['login-message'].textContent.includes('không còn hợp lệ'));
  // A confirmed brownout can be discovered without authentication after reconnect.
  run("state.bootId='boot-before';state.authToken='lost-token';state.session='old-lease';state.connected=false;state.ready=true;loginView();startCamera()");
  const bootRequests=[];
  const brownoutBoot={id:'boot-after',reason:'brownout',brownout:true,cause:1,raw_cause:3};
  ctx.fetch=async(path,opts)=>{bootRequests.push({path,opts});return{ok:true,json:async()=>({message:'ESP32 online',boot:brownoutBoot})}};
  await run('pollBoot()');
  assert.equal(run('state.authToken'),null);assert.equal(run('state.session'),null);
  assert.equal(els['power-alert'].hidden,false);assert(els['power-title'].textContent.includes('sụt nguồn'));
  assert(els['login-message'].textContent.includes('sụt nguồn'));
  assert.equal(els['camera-image'].src,'');
  assert.deepEqual(bootRequests.map(r=>r.path),['/api/ping']);
  assert.equal(JSON.parse(savedLogin.get('esp32-boot')).warning,'brownout');
  // Dismissal survives repeated polling of the same boot; no automatic rearming.
  els['power-dismiss'].trigger('click');await run('pollBoot()');
  assert.equal(els['power-alert'].hidden,true);assert.equal(run('state.session'),null);
  // Brownout metadata on a 401 response must also survive returning to login.
  run("state.bootId='boot-previous';state.authToken='lost-again';state.connected=true;state.ready=true;state.session='old-again'");
  ctx.fetch=async()=>({ok:false,status:401,json:async()=>({error:'login_required',boot:{...brownoutBoot,id:'boot-next'}})});
  await run('poll()');assert.equal(els['power-alert'].hidden,false);
  assert.equal(run('state.authToken'),null);assert(els['login-message'].textContent.includes('sụt nguồn'));
  // Ordinary power-on and transient packet loss must not be confirmed as brownout.
  els['power-dismiss'].trigger('click');
  ctx.fetch=async()=>({ok:true,json:async()=>({message:'ESP32 online',boot:{id:'power-cycle',reason:'power_on',brownout:false}})});
  await run('pollBoot()');
  assert(els['power-title'].textContent.includes('cấp nguồn lại'));
  assert(els['power-message'].textContent.includes('Chưa đủ dữ liệu'));
  els['power-dismiss'].trigger('click');
  ctx.fetch=async()=>{throw new Error('radio timeout')};await run('pollBoot()');
  assert.equal(els['power-alert'].hidden,true);
  // A late login response after switching to demo must not unlock the dashboard for real driving.
  let resolveLogin;
  ctx.fetch=async(path)=>path==='/api/login'?await new Promise(resolve=>{resolveLogin=resolve;}):{ok:true,json:async()=>({ok:true})};
  els['login-password'].value='test-password';
  const pendingLogin=els['login-form'].events.submit[0]({preventDefault(){}});
  els.mode.value='demo';run('changeMode()');
  resolveLogin({ok:true,json:async()=>({token:'late-login',username:'admin'})});await pendingLogin;
  assert.equal(run('state.authToken'),null);assert.equal(run('state.mode'),'demo');
  // Demo must continue to send no traffic after leaving live mode.
  const before=requests.length;els.mode.value='demo';run('changeMode();updateJoystick(0,1)');await run('sendControl()');assert.equal(requests.length,before);
  // Ban do: toa do, huong, loc diem do va chong nhay moc khi bo khoi dong lai.
  const near=(actual,expected)=>assert(Math.abs(actual-expected)<1e-6,actual+' != '+expected);
  run('map.track=.2;mapReset();mapStep(1,1)');near(run('map.y'),1);near(run('map.x'),0);near(run('map.len'),1);
  run('mapStep(.1*Math.PI/2,-.1*Math.PI/2)');near(run('map.th'),Math.PI/2);near(run('map.y'),1);near(run('map.len'),1);
  run('mapStep(1,1)');near(run('map.x'),1);near(run('map.y'),1);
  assert.equal(run('mapScan(0,100)'),true);assert.equal(run('map.walls.size'),1);assert.deepEqual(run('[...map.walls.values()][0].map(v=>Math.round(v*1e6)/1e6)'),[2,1]);
  run('mapScan(0,100.5)');assert.equal(run('map.walls.size'),1);
  for(const bad of ['mapScan(0,1)','mapScan(0,151)','mapScan(NaN,50)','mapScan(0,Infinity)'])assert.equal(run(bad),false);assert.equal(run('map.walls.size'),1);
  run('mapReset();mapLive([0,0,0,0].map(()=>({signed_distance_m:1})))');near(run('map.y'),0);assert.deepEqual(run('map.last'),[1,1]);
  run('mapLive([0,0,0,0].map(()=>({signed_distance_m:1.5})))');near(run('map.y'),.5);
  run('mapLive([0,0,0,0].map(()=>({signed_distance_m:9})))');near(run('map.y'),.5);assert.deepEqual(run('map.last'),[9,9]);
  run('mapLive([{},{},{},{}])');assert.equal(els['map-status'].textContent,'Firmware chưa gửi vị trí');
  run('map.y=5;mapReset()');near(run('map.y'),0);assert.equal(run('map.path.length'),1);run('map.track=.16');
  // Quay ve trong mo phong: xoay dau, di nguoc lai duong cu, huy duoc, khong gui lenh toi xe.
  const fetchBefore=requests.length,step=n=>{for(let i=0;i<n;i++){now+=200;run('tick()')}};
  run('stop();mapReset();state.rpm=[0,0,0,0];map.track=.16;updateJoystick(0,.7)');step(25);run('updateJoystick(.5,.5)');step(10);run('updateJoystick(0,.6)');step(15);run('stop()');step(8);
  assert(run('map.route.length')>5);const farAway=run('Math.hypot(map.x,map.y)');assert(farAway>.8,'farAway '+farAway);
  els['map-return'].trigger('click');assert.equal(run('map.ret'),true);step(4);
  assert(Math.abs(run('map.th'))>0,'xoay');assert(run('state.left*state.right')<0,'xoay tai cho truoc khi di');
  let guard=0;while(run('map.ret')&&guard++<1500){now+=200;run('tick()')}
  assert.equal(run('map.ret'),false,'chua ve sau '+guard+' buoc');assert(run('Math.hypot(map.x,map.y)')<.08,'lech '+run('Math.hypot(map.x,map.y)'));
  assert.equal(run('state.left'),0);assert.equal(els['drive-status'].textContent,'Đã về điểm xuất phát · mô phỏng');assert.equal(run('map.route.length'),1);
  run('updateJoystick(0,.7)');step(15);run('stop()');step(6);els['map-return'].trigger('click');step(3);run('updateJoystick(0,.5)');assert.equal(run('map.ret'),false,'joystick huy');
  run('stop()');els['map-return'].trigger('click');step(2);win.trigger('keydown',{code:'Space'});assert.equal(run('map.ret'),false,'phim cach huy');assert.equal(run('state.left'),0);
  els['map-return'].trigger('click');els['map-return'].trigger('click');assert.equal(run('map.ret'),false,'bam lai de huy');
  assert.equal(requests.length,fetchBefore,'mo phong khong gui lenh');
  run('stop();mapReset();state.mode="live";startReturn();state.mode="demo"');assert.equal(run('map.ret'),false,'xe that khong co quay ve');
  run('stop();mapReset()');
  // Ne vat can trong mo phong: dat vat can tren duong ve, xe khong duoc dam va van ve duoc.
  const boxGap=()=>run('map.boxes.reduce((m,b)=>Math.min(m,Math.hypot(Math.max(Math.abs(map.x-b[0])-.15,0),Math.max(Math.abs(map.y-b[1])-.15,0))),9)');
  run('stop();mapReset();state.rpm=[0,0,0,0];map.track=.16;updateJoystick(0,.7)');step(45);run('stop()');step(8);
  const straightY=run('map.y');assert(straightY>1.2,'y '+straightY);
  els['map-return'].trigger('click');step(25);
  assert.equal(run('mapAddBox(map.x-.05,map.y-.65)'),true,'dat duoc vat can phia truoc xe');let closest=9,avoided=0;guard=0;
  while(run('map.ret')&&guard++<3000){now+=200;run('tick()');closest=Math.min(closest,boxGap());avoided=Math.max(avoided,run('map.nav?.avoid||0'));}
  assert.equal(run('map.ret'),false,'chua ve sau '+guard+' buoc');assert(avoided>=1,'chua ne lan nao');assert(closest>.1,'qua sat vat can '+closest);
  assert.equal(els['drive-status'].textContent,'Đã về điểm xuất phát · mô phỏng');assert(run('Math.hypot(map.x,map.y)')<.1,'lech '+run('Math.hypot(map.x,map.y)'));
  assert.equal(run('map.boxes.length'),1,'vat can van con sau khi ve');
  // Bam lai dung vat can thi go, qua sat xe thi tu choi.
  run('mapAddBox(map.boxes[0][0],map.boxes[0][1])');assert.equal(run('map.boxes.length'),0);assert.equal(run('mapAddBox(map.x,map.y)'),false);
  // Bi vay kin: xe dung han va bao khong tim duoc duong.
  run('stop();mapReset();updateJoystick(0,.7)');step(30);run('stop()');step(8);
  run('for(const [dx,dy] of [[0,.55],[.3,.55],[-.3,.55],[0,-.55],[.3,-.55],[-.3,-.55],[.55,0],[.55,.3],[.55,-.3],[-.55,0],[-.55,.3],[-.55,-.3],[.55,.55],[-.55,.55],[.55,-.55],[-.55,-.55]])map.boxes.push([map.x+dx,map.y+dy])');
  closest=9;els['map-return'].trigger('click');guard=0;while(run('map.ret')&&guard++<3000){now+=200;run('tick()');closest=Math.min(closest,boxGap());}
  assert.equal(run('map.ret'),false,'chua dung');assert.match(els['drive-status'].textContent,/Không tìm được đường về/);assert.equal(run('state.left'),0);assert(closest>.05,'dam khi bi vay '+closest);
  run('stop();mapReset()');
  // Du lieu firmware: vi tri, duong di, duong ve, diem quet; moi diem chi ve mot lan.
  run('stop();mapReset();map.epoch=null;map.trailSeq=0;map.scanSeq=0');
  const fw=(extra)=>({pose:{x:1,y:2,th:.5,length_m:3,route:9,epoch:7},trail:[],nav:{active:false,state:'idle',result:null,avoid:0},scan:{sweeping:false,sweep_id:2,seen_echo:true,front_cm:42.4,points:[]},...extra});
  run('globalThis.fwData=null');const setFw=d=>{ctx.fwData=d;run('mapLive([],fwData)')};
  setFw(fw({trail:[[1,0,.1,0],[2,0,.2,0]],scan:{sweeping:false,sweep_id:2,seen_echo:true,front_cm:42.4,points:[[1,1,1],[2,1.01,1.01]]}}));
  near(run('map.x'),1);near(run('map.th'),.5);assert.equal(run('map.path.length'),3);assert.equal(run('map.walls.size'),1);assert.match(els['map-scan'].textContent,/42 cm/);
  setFw(fw({trail:[[1,0,.1,0],[2,0,.2,0]]}));assert.equal(run('map.path.length'),3,'khong ve lai diem cu');
  setFw(fw({trail:[[3,0,.15,1],[4,0,.1,1]],nav:{active:true,state:'avoid_scan',avoid:1}}));assert.equal(run('map.back.length'),1);assert.equal(run('map.back[0].length'),3);assert.equal(run('map.path.length'),0);assert.equal(els['map-status'].textContent,'Gặp vật cản · đang quét');
  setFw(fw({trail:[[5,0,.05,0]]}));assert.equal(run('map.liveBack'),false);assert.equal(run('map.path.length'),2);
  setFw({...fw(),pose:{...fw().pose,epoch:8}});assert.equal(run('map.walls.size'),0,'firmware dat lai ban do');
  setFw(fw({scan:null,pose:{...fw().pose,epoch:8}}));assert.match(els['map-scan'].textContent,/Chưa bật/);
  setFw(fw({scan:{sweeping:false,sweep_id:0,seen_echo:false,front_cm:null,points:[]},pose:{...fw().pose,epoch:8}}));assert.match(els['map-scan'].textContent,/Chưa nhận tín hiệu/);
  // Khi xe tu quay ve, trang khong duoc gui lenh joystick lam huy viec quay ve.
  els.mode.value='live';run('changeMode()');run("state.authToken='t';state.connected=true;state.ready=true;state.session='s';state.returning=true");
  const sentBefore=requests.length;await run('sendControl()');assert.equal(requests.length,sentBefore,'khong gui control khi dang quay ve');
  run('disarm()');assert.equal(run('state.returning'),false);run("state.authToken=null;state.connected=null;state.ready=false");
  els.mode.value='demo';run('changeMode()');
  console.log('PASS: simulated obstacle placement, removal, avoidance and blocked stop.');
  console.log('PASS: map odometry, heading, obstacle projection and filtering, live baseline protection, reset.');
  console.log('PASS: real API telemetry rendering, persistent login/logout flow, joystick commands, lease release without idle control traffic, immediate STOP during pending movement, dead-zone release, session invalidation, automatic control acquisition, STOP/release cancellation and fresh-gesture restart, network-failure stop, demo isolation.');
})().catch(error=>{console.error(error);process.exitCode=1});
