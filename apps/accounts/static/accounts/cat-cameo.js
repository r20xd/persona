/* Owner-scoped walks and private, explicitly submitted page ratings. */
(() => {
  const projection=document.getElementById('cat-walk-preference');
  if(!projection) return;
  const {owner}=JSON.parse(projection.textContent);
  const keys={enabled:`persona.cat.walk.${owner}.enabled`,next:`persona.cat.walk.${owner}.v2.next`};
  let memory={},storageWorks=true;
  function read(key) {try {return localStorage.getItem(key);} catch {storageWorks=false;return memory[key]??null;}}
  function write(key,value) {memory[key]=String(value);try {localStorage.setItem(key,String(value));} catch {storageWorks=false;}}
  const enabled=()=>read(keys.enabled)!=='false';
  const random=(min,max)=>min+Math.random()*(max-min);
  const root=document.querySelector('[data-cat-cameo]'), toggle=document.querySelector('[data-cat-walk-toggle]');
  const preferenceStatus=document.querySelector('[data-walk-preference-status]');
  function updateToggle() {
    if(toggle) toggle.checked=enabled();
    if(preferenceStatus && !storageWorks) preferenceStatus.textContent='Хранилище браузера недоступно. Настройка действует до закрытия страницы.';
  }
  updateToggle();
  if(toggle) toggle.closest(".cat-walk-setting").hidden=false;
  addEventListener('storage',event=>{if(event.key===keys.enabled) updateToggle();});
  if(toggle) toggle.addEventListener('change',()=>{write(keys.enabled,toggle.checked);updateToggle();});
  if(!root) return;
  const traveller=root.querySelector('[data-cameo-traveller]'), pet=root.querySelector('[data-cameo-pet]');
  const bubble=root.querySelector('[data-cameo-bubble]'), node=root.querySelector('[data-cat-renderer]');
  const config=JSON.parse(document.getElementById('cat-renderer-config').textContent);
  const questions=JSON.parse(document.getElementById('cat-rating-questions').textContent);
  const ratingForm=root.querySelector('[data-cameo-rating]');
  const questionText=root.querySelector('[data-rating-question]');
  const ratingStatus=root.querySelector('[data-rating-status]');
  const stars=[...root.querySelectorAll('[data-rating-value]')];
  const answers=new Map();
  let question=null,lastQuestion=null,pending=false,shownQuestion=false;
  function selectQuestion() {
    if(!shownQuestion) {
      const choices=questions.filter(item=>item.key!==lastQuestion);
      const pool=choices.length ? choices : questions;
      question=pool[Math.floor(Math.random()*pool.length)];
      lastQuestion=question.key;shownQuestion=true;
    }
  }
  function showRating() {
    if(!question) return;
    questionText.textContent=question.text;
    const value=answers.get(question.key)||0;
    stars.forEach(button=>{
      const selected=Number(button.dataset.ratingValue)<=value;
      button.classList.toggle('is-selected',selected);
      button.querySelector('[aria-hidden]').textContent=selected?'★':'☆';
      button.setAttribute('aria-pressed',String(Number(button.dataset.ratingValue)===value));
      button.setAttribute('aria-disabled',String(pending));
    });
    ratingStatus.textContent=pending ? 'Сохраняю оценку…' : value ? `Сохранено: ${value} из 5. Спасибо!` : '1 — плохо, 5 — отлично';
  }
  stars.forEach(button=>button.addEventListener('click',async()=>{
    if(pending || !question) return;
    const asked=question, rating=button.dataset.ratingValue;
    const data=new FormData(ratingForm);
    data.set('question',asked.key);data.set('rating',rating);
    pending=true;stars.forEach(star=>{star.setAttribute('aria-disabled','true');});
    ratingStatus.textContent='Сохраняю оценку…';
    try {
      const response=await fetch(ratingForm.action,{method:'POST',body:data,credentials:'same-origin',headers:{'Accept':'application/json'}});
      const result=await response.json();
      if(!response.ok || result.question!==asked.key || result.rating!==Number(rating)) throw new Error('rating');
      answers.set(asked.key,result.rating);
      pending=false;
      showRating();
    } catch {
      pending=false;stars.forEach(star=>{star.setAttribute('aria-disabled','false');});
      if(question===asked) ratingStatus.textContent='Не удалось сохранить. Нажми на звезду, чтобы повторить.';
    }
  }));
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let timer=0,raf=0,alive=true,visible=false,interacting=false,hovered=false;
  let previousFocus=null,elapsed=0,last=0,duration=0,direction=1,kind='run',x=0,y=0,joyStart=0;
  const inlineMedia=matchMedia('(max-width: 850px)');
  const inlineSlot=root.closest('[data-assistant-cameo-slot]');
  const inline=()=>!!inlineSlot && inlineMedia.matches;
  function suppressed() {
    const active=document.activeElement, g=geometry();
    return g.width-g.left<g.size+24 || (!inline() && g.height-g.bottom<g.size+80) || !enabled() || reduced.matches || document.hidden ||
      !!document.querySelector('dialog[open],[role="dialog"][aria-modal="true"],[data-workspace-menu][open]') ||
      !!active?.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])');
  }
  let lastPaint='';
  function geometry() {
    const size=48*Math.max(1,Math.round(2*devicePixelRatio))/devicePixelRatio;
    if(inline()) return {width:inlineSlot.clientWidth,height:size,size,left:0,bottom:0};
    const nav=document.querySelector('.campus-nav');
    const rect=nav?.getBoundingClientRect();
    const bottom=rect && rect.top>innerHeight/2 && rect.bottom>=innerHeight-20 ? innerHeight-rect.top : 0;
    const sidebar=document.querySelector('.workspace-sidebar')?.getBoundingClientRect();
    const left=sidebar && sidebar.height>innerHeight*.7 && sidebar.width<innerWidth*.5 ? sidebar.right+12 : 12;
    return {width:innerWidth,height:innerHeight,size,left,bottom:Math.max(16,bottom+12)};
  }
  let wasInline=inline();
  function position() {
    const g=geometry(), maxX=Math.max(g.left,g.width-g.size-12),maxY=g.height-g.bottom-g.size;
    x=Math.max(g.left,Math.min(x,maxX));
    if(!inline()) y=wasInline?maxY:Math.max(interacting?80:12,Math.min(y,maxY));
    wasInline=inline();
    const snap=value=>Math.round(value*devicePixelRatio)/devicePixelRatio;
    pet.style.width=pet.style.height=`${g.size}px`;
    traveller.style.width=inline()?'100%':`${g.size}px`;
    traveller.style.height=inline()?'auto':`${g.size}px`;
    if(inline()) {
      traveller.style.transform='none';
      pet.style.transform=`translateX(${snap(x)}px)`;
      bubble.style.left='0px';bubble.style.maxHeight='none';
      return;
    }
    pet.style.transform='none';
    traveller.style.transform=`translate(${snap(x)}px,${snap(y)}px)`;
    bubble.style.left=`${Math.min(0,g.width-12-x-bubble.offsetWidth)}px`;
    bubble.style.maxHeight=`${Math.max(44,y-16)}px`;
  }
  function paint(pose,frame) {
    const key=`${pose}/${frame}`;
    if(lastPaint!==key) {window.PersonaCat?.render(node,pose,frame,config.counts[pose]);lastPaint=key;}
  }
  function schedule() {
    clearTimeout(timer);timer=0;if(!alive || visible || suppressed()) return;
    let next=Number(read(keys.next));
    if(!Number.isFinite(next) || next<=0) {next=Date.now()+random(3000,6000);write(keys.next,next);}
    timer=setTimeout(attempt,Math.min(2147483647,Math.max(0,next-Date.now())));
  }
  function restoreFocus() {
    if(!root.contains(document.activeElement)) return;
    const target=previousFocus?.isConnected && previousFocus!==document.body ? previousFocus : document.getElementById('main');
    target?.focus({preventScroll:true});
  }
  function hide(restore=true) {
    if(restore) restoreFocus();
    cancelAnimationFrame(raf);raf=0;visible=false;interacting=false;hovered=false;
    root.hidden=true;bubble.hidden=true;pet.setAttribute('aria-expanded','false');
    paint('idle',0);
  }
  function tick(now) {
    if(!alive || !visible) return;
    if(suppressed()) {hide();schedule();return;}
    const delta=last ? Math.min(100,now-last) : 0;last=now;
    if(interacting) {
      const frame=Math.min(config.counts.joy-1,Math.floor((now-joyStart)/110));
      paint('joy',frame);
      if(frame===config.counts.joy-1) {raf=0;return;}
    } else if(!hovered && !root.contains(document.activeElement)) {
      elapsed+=delta;
      if(elapsed>=duration) {hide();schedule();return;}
      const progress=elapsed/duration,g=geometry();
      x=direction===1 ? g.left+progress*(g.width-g.size-12-g.left) : g.width-g.size-12-progress*(g.width-g.size-12-g.left);
      const hop=kind==='hop' ? Math.abs(Math.sin(progress*Math.PI*4))*48 : Math.abs(Math.sin(elapsed/110))*3;
      y=inline()?0:g.height-g.bottom-g.size-hop;
      paint(kind==='hop'?'jump':'idle',kind==='hop'?Math.floor((elapsed%800)/100):Math.floor((elapsed%1080)/180));
      position();
    }
    raf=requestAnimationFrame(tick);
  }
  function attempt() {
    if(!alive) return;
    timer=0;
    if(suppressed() || node.dataset.renderReady!=='true') return;
    const next=Number(read(keys.next));
    if(next>Date.now()) {schedule();return;}
    // Claim cooldown before showing, so navigation and other tabs share the same interval.
    write(keys.next,Date.now()+random(20000,40000));
    previousFocus=document.activeElement;duration=random(6000,9000);direction=Math.random()<.5?1:-1;kind=Math.random()<.5?'run':'hop';
    root.dataset.walk=kind;visible=true;interacting=false;elapsed=0;last=0;shownQuestion=false;
    root.hidden=false;node.style.transform=direction===1?'scaleX(-1)':'none';
    const g=geometry();x=direction===1?g.left:g.width-g.size-12;y=g.height-g.bottom-g.size;position();
    raf=requestAnimationFrame(tick);
  }
  pet.addEventListener('pointerenter',()=>{hovered=true;});
  pet.addEventListener('pointerleave',()=>{hovered=false;});
  pet.addEventListener('click',()=>{
    if(!bubble.hidden) {
      bubble.hidden=true;
      pet.setAttribute('aria-expanded','false');
      pet.focus({preventScroll:true});
      interacting=false;
      last=0;
      cancelAnimationFrame(raf);
      raf=requestAnimationFrame(tick);
      return;
    }
    selectQuestion();showRating();interacting=true;hovered=false;bubble.hidden=false;pet.setAttribute('aria-expanded','true');
    joyStart=performance.now();last=0;cancelAnimationFrame(raf);position();raf=requestAnimationFrame(tick);
  });
  function dismiss() {write(keys.next,Date.now()+random(20000,40000));hide();schedule();}
  root.querySelector('[data-cameo-close]').addEventListener('click',dismiss);
  root.querySelector('[data-cameo-disable]').addEventListener('click',()=>{write(keys.enabled,false);hide();schedule();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape' && visible) dismiss();});
  function suppressChanged() {
    if(suppressed()) {clearTimeout(timer);timer=0;if(visible) hide();}
    else if(!visible) schedule();
  }
  document.addEventListener('focusin',suppressChanged);
  document.addEventListener('focusout',()=>{clearTimeout(timer);timer=setTimeout(suppressChanged,0);});
  document.addEventListener('visibilitychange',suppressChanged);
  reduced.addEventListener('change',suppressChanged);
  // Open dialogs can change without a focus event. Observe only their open state.
  const observer=new MutationObserver(suppressChanged);
  observer.observe(document.body,{subtree:true,attributes:true,attributeFilter:['open','aria-modal','data-render-ready']});
  addEventListener('resize',()=>{if(visible) {if(suppressed()) {hide();schedule();} else position();}});
  addEventListener('storage',event=>{if(Object.values(keys).includes(event.key)) {if(!enabled()) {clearTimeout(timer);timer=0;hide();}else if(!visible) schedule();}});
  addEventListener('pagehide',()=>{alive=false;clearTimeout(timer);hide(false);observer.disconnect();});
  addEventListener('pageshow',event=>{if(event.persisted) {alive=true;observer.observe(document.body,{subtree:true,attributes:true,attributeFilter:['open','aria-modal','data-render-ready']});schedule();}});
  schedule();
})();
