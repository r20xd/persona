/* CAT09: render immutable CAT08 artwork on a real 48-grid; never resample old CAT07 cats. */
(() => {
  const configurations = document.getElementById('cat-renderer-config');
  if (!configurations) return;
  const config = JSON.parse(configurations.textContent);
  const palette = config.palette;
  const size = 48;
  function surface() {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = size;
    return canvas;
  }
  function colour(index) { return `rgb(${palette[index].join(',')})`; }
  function prepare(image) {
    const original = document.createElement('canvas');
    original.width = image.naturalWidth; original.height = image.naturalHeight;
    const ctx = original.getContext('2d', {willReadFrequently: true});
    ctx.drawImage(image, 0, 0);
    const source = ctx.getImageData(0, 0, original.width, original.height).data;
    const grid=new Uint8Array(size*size);
    if(config.native_grid) {
      if(original.width!==size || original.height!==size) throw new Error('Invalid native grid');
      for(let pos=0;pos<size*size;pos++) {
        const offset=pos*4, alpha=source[offset+3];
        if(!alpha) continue;
        if(alpha!==255) throw new Error('Invalid native alpha');
        const index=palette.findIndex((rgb,i) => i>0 && rgb.every((v,c)=>v===source[offset+c]));
        if(index<1) throw new Error('Invalid native colour');
        grid[pos]=index;
      }
    } else {
      let left=original.width, right=0, top=original.height, bottom=0;
      for(let y=0;y<original.height;y++) for(let x=0;x<original.width;x++) {
        if(source[(y*original.width+x)*4+3] < 180) continue;
        left=Math.min(left,x); right=Math.max(right,x); top=Math.min(top,y); bottom=Math.max(bottom,y);
      }
      if(right<=left || bottom<=top) throw new Error('Empty artwork');
      const scale=Math.min(36/(right-left+1),36/(bottom-top+1));
      const width=Math.round((right-left+1)*scale), height=Math.round((bottom-top+1)*scale);
      const ox=Math.round((size-width)/2), oy=Math.round((size-height)/2);
      for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const sx=Math.min(right,left+Math.floor((x+.5)/scale));
        const sy=Math.min(bottom,top+Math.floor((y+.5)/scale));
        const pos=(sy*original.width+sx)*4;
        if(source[pos+3]<128) continue;
        let distance=Infinity, best=1;
        palette.forEach((rgb,index) => {
          if(!index) return;
          const d=rgb.reduce((sum,v,channel) => sum+(v-source[pos+channel])**2,0);
          if(d<distance) {distance=d; best=index;}
        });
        grid[(oy+y)*size+ox+x]=best;
      }
    }
    const layers={head:surface(),body:surface(),tail:surface()};
    Object.entries(layers).forEach(([name,canvas]) => {
      const context=canvas.getContext('2d'), pixels=context.createImageData(size,size);
      grid.forEach((index,pos) => {
        if(!index) return;
        const x=pos%size, y=Math.floor(pos/size), tail=config.rig.tail;
        const inTail=x>=tail[0] && x<tail[0]+tail[2] && y>=tail[1] && y<tail[1]+tail[3];
        const use=name==='tail' ? inTail : !inTail && (name==='head' ? y<=28 : y>=27);
        if(!use) return;
        pixels.data.set([...palette[index],255],pos*4);
      });
      context.putImageData(pixels,0,0);
    });
    return {layers,grid};
  }
  function render(node,pose='idle',frame=0,count=6) {
    const state=node._catRenderer;
    if(!state || !state.ready) { if(state) state.pending=[pose,frame,count]; return; }
    const canvas=node.querySelector('canvas'), ctx=canvas.getContext('2d');
    ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,size,size);
    const endpoint=frame===0 || frame===count-1;
    const f=Math.min(frame,7), phase=endpoint ? 'idle' : pose;
    let globalY=0, headY=0, headX=0, sx=1, sy=1, wag=0;
    if(phase==='idle' && pose==='idle') {
      headY=[0,0,-1,-1,0,0][frame%6]; sy=[1,1.02,1.04,1.02,1,1][frame%6];
    }
    if(phase==='jump') {
      globalY=[0,0,-1,-2,-4,-3,0,0][f]; headY=[0,2,1,0,-1,0,2,0][f];
      sx=[1,1.08,1.06,.95,.94,.96,1.08,1][f]; sy=[1,.88,.92,1.05,1.06,1.04,.90,1][f];
    }
    if(phase==='joy') {
      globalY=[0,-1,-2,-1,0,-1,-1,0][f];headY=-(frame%2);headX=frame%2;
      wag=[0,-2,-1,1,2,1,-1,0][f];sy=frame%2 ? 1.03 : 1;
    }
    if(phase==='stretch') {
      sy=[1,1.03,1.08,1.12,1.14,1.08,1.03,1][f];
      headY=[0,-1,-2,-3,-3,-2,-1,0][f];wag=frame%3-1;
    }
    if(phase==='yawn') {headY=frame>2 && frame<6 ? -1 : 0;wag=frame%3-1;}
    if(phase==='surprise') {headY=-1;sy=1.03;wag=frame%2 ? -2 : 1;}
    // Bend the free tip while the lower tail attachment remains anchored.
    let previousShift=0;
    for(let row=0;row<size;row++) {
      const tipShift=Math.round(wag*Math.max(0,Math.min(1,(42-row)/14)));
      ctx.drawImage(state.layers.tail,0,row,size,1,tipShift,row+globalY,size,1);
      if(row>0 && previousShift!==tipShift) {
        // Overlap the source scanline at the bend so a one-pixel strand cannot detach.
        ctx.drawImage(state.layers.tail,0,row,size,1,previousShift,row+globalY,size,1);
      }
      previousShift=tipShift;
    }
    if(config.character==='chaos') sx=Math.max(1,sx);
    const bw=Math.round(size*sx), bh=Math.round(size*sy), bx=Math.round((size-bw)/2);
    const by=42-Math.round(42*sy)+globalY;
    ctx.drawImage(state.layers.body,0,0,size,size,bx,by,bw,bh);
    ctx.drawImage(state.layers.head,headX,headY+globalY);
    ctx.save();ctx.translate(headX,headY+globalY);
    const eyeMode=phase==='blink' || phase==='yawn' ? 'closed' : phase==='surprise' ? 'wide' : null;
    if(eyeMode) {
      config.rig.eyes.forEach(([x,y,w,h]) => {
        ctx.fillStyle=colour(6);ctx.fillRect(x,y,w,h);
        ctx.fillStyle=colour(1);
        if(eyeMode==='closed') {
          ctx.fillRect(x+1,y+Math.floor(h/2),w-2,1);
          ctx.fillRect(x,y+Math.floor(h/2)-1,1,1);
        } else {
          const cx=x+Math.floor(w/2), cy=y+Math.floor(h/2);
          ctx.fillRect(cx,cy-2,1,1);ctx.fillRect(cx-1,cy-1,3,3);ctx.fillRect(cx,cy+2,1,1);
          ctx.fillStyle=colour(7);ctx.fillRect(cx-1,cy-1,1,1);
        }
      });
    }
    if(phase==='yawn' || phase==='surprise' || phase==='joy') {
      const [x,y,w,h]=config.rig.mouth;
      ctx.fillStyle=colour(6);ctx.fillRect(x,y,w,h);
      ctx.fillStyle=colour(1);
      if(phase==='joy') {
        ctx.fillRect(x+1,y+1,w-2,1);ctx.fillRect(x+2,y+2,w-4,2);
        ctx.fillStyle=colour(8);ctx.fillRect(x+3,y+2,2,1);
      } else if(phase==='surprise') {
        const cx=x+Math.floor(w/2), cy=y+2;
        ctx.fillRect(cx,cy-1,1,1);ctx.fillRect(cx-1,cy,1,1);
        ctx.fillRect(cx+1,cy,1,1);ctx.fillRect(cx,cy+1,1,1);
      } else {
        const opening=phase==='yawn' ? [0,1,2,4,4,3,1,0][f] : 3;
        ctx.fillRect(x+2,y+1,Math.max(2,w-4),Math.max(1,opening));
        ctx.fillStyle=colour(8);ctx.fillRect(x+3,y+opening,2,1);
      }
    }
    ctx.restore();
    node.dataset.pose=pose;node.dataset.frame=frame;
  }
  window.PersonaCat={render(node,...args) {
    try { render(node,...args); }
    catch {
      node._catRenderer.ready=false;node.dataset.renderReady='error';
      node.querySelector('canvas').hidden=true;node.querySelector('img').hidden=false;
    }
  }};
  document.querySelectorAll('[data-cat-renderer]').forEach(node => {
    const fallback=node.querySelector('img'), canvas=node.querySelector('canvas');
    const state={ready:false,pending:['idle',0,config.counts.idle]};node._catRenderer=state;
    const image=new Image();
    image.onload=() => {
      try {
        Object.assign(state,prepare(image),{ready:true});render(node,...state.pending);
        canvas.hidden=false;fallback.hidden=true;node.dataset.renderReady='true';
      } catch {state.ready=false;node.dataset.renderReady='error';canvas.hidden=true;fallback.hidden=false;}
    };
    image.onerror=() => {node.dataset.renderReady='error';};
    image.src=config.source;
  });
})();
