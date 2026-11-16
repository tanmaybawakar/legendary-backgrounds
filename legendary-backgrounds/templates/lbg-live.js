/*!
 * lbg-live.js — live, animated version of a legendary-backgrounds recipe.
 * Zero dependencies. ~8 KB. Draws a slow, GPU-cheap WebGL animation over the static hero image.
 *
 *   import { mountLegendaryBackground } from "./lbg-live.js";
 *   const stop = mountLegendaryBackground(heroEl, { recipe, image: "/bg/nova-desktop-1920.webp" });
 *
 * Contract:
 *  - The static <img> stays underneath and is what users see first (LCP, no-JS, no-WebGL).
 *  - prefers-reduced-motion: reduce  -> never animates (static image only).
 *  - Pauses when the hero is offscreen or the tab is hidden. DPR and render scale are capped.
 *  - Procedural families animate natively; image / terrain / ribbon / bolt / ascii recipes animate
 *    the static image itself (slow drift + light sweep + living grain).
 */

const VERT = `attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;

const FRAG = `
precision highp float;
uniform vec2 uRes; uniform float uTime; uniform float uSeed;
uniform vec3 uPal[7]; uniform int uN; uniform vec3 uPal2[7]; uniform int uN2;
uniform float uP[16]; uniform int uMode;
uniform sampler2D uImg; uniform vec2 uImgSize; uniform vec2 uFocus;
uniform float uGrain; uniform float uDither; uniform float uDitherPx; uniform float uHalftone; uniform float uHalftoneAng;

vec3 pal(float t){
  t=clamp(t,0.,1.)*float(uN-1);
  vec3 c=uPal[0];
  for(int i=0;i<6;i++){ if(i<uN-1){ c=mix(c,uPal[i+1],clamp(t-float(i),0.,1.)); } }
  return c;
}
vec3 pal2(float t){
  t=clamp(t,0.,1.)*float(uN2-1);
  vec3 c=uPal2[0];
  for(int i=0;i<6;i++){ if(i<uN2-1){ c=mix(c,uPal2[i+1],clamp(t-float(i),0.,1.)); } }
  return c;
}
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)+uSeed); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vnoise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
float fbm(vec2 p){ float a=.5,s=0.; for(int i=0;i<5;i++){ s+=a*vnoise(p); p=p*2.03+17.1; a*=.5; } return s/0.97; }
float sq(float x){ return x*x; }
float tm(float x){ return 1.-exp(-max(x,0.)); }
float sstep(float a,float b,float x){ return smoothstep(a,b,x); }

// ---- families --------------------------------------------------------------------------
float arcI(vec2 q,float off,float t){
  float R=uP[0], top=uP[1], cy=top+R; float r=length(q-vec2(0.,cy));
  float wob=.015*sin(atan(q.x,cy-q.y)*7.+t*.6)+.01*sin(t*.4);
  float d=r-R+off+wob;
  float rim = d>0. ? exp(-sq(d/uP[2])) : exp(-sq(d/uP[3]));
  float hf=.35+.65*exp(-sq((q.x-.15*sin(t*.15))/(uP[6]*uRes.x/uRes.y)));
  if(uP[10]>.5){ float inside = d<0. ? uP[4]*(1.-exp(d/uP[5]))*1.6 : 0.; return uP[7]*hf*(rim*.75+inside); }
  float inside = d<0. ? uP[4]*exp(d/uP[5]) : 0.;
  return uP[7]*hf*(rim+inside);
}
float hourI(vec2 q,float off,float t,float a){
  float R=uP[0], gap=uP[1]*(1.+.12*sin(t*.5)), cy=R+gap, soft=uP[2];
  float g=min(length(q+vec2(0.,cy))-R, length(q-vec2(0.,cy))-R);
  float lit=sstep(-soft*.3,soft,g+off);
  float core=.55+.45*exp(-sq(q.x/(.9*a)));
  float hot=.9*exp(-sq(q.y/.10))*exp(-sq(q.x/(.55*a)));
  return uP[7]*lit*(core+hot);
}
vec3 mesh(vec2 q,float t,float a){
  vec2 w=vec2(fbm(q*.8+t*.03),fbm(q*.8-t*.025+9.))-.5; q+=w*uP[0]*2.*vec2(a,1.);
  vec3 num=uPal[0]*.25; float den=.25;
  for(int i=1;i<7;i++){ if(i<uN){
    float fi=float(i);
    vec2 c=vec2(sin(fi*1.7+t*.07*(1.+.2*fi)+uSeed)*.8*a, cos(fi*2.3+t*.06+uSeed*1.3)*.75);
    float wg=exp(-dot(q-c,q-c)/(.55*.55)*2.2); num+=uPal[i]*wg; den+=wg; } }
  return num/den;
}
float warped(vec2 q,float t,float sc,float wp){
  vec2 p=q*sc; vec2 a1=vec2(fbm(p+t*.02),fbm(p+5.2-t*.018));
  vec2 b1=vec2(fbm(p+4.*wp*a1+1.7+t*.015),fbm(p+4.*wp*a1+9.2));
  return fbm(p+4.*wp*b1);
}
float bayer2(vec2 a){ a=floor(a); return fract(dot(a,vec2(.5,a.y*.75))); }
float bayer4(vec2 a){ return bayer2(.5*a)*.25+bayer2(a); }
vec3 iris(float x){ return .5+.5*cos(6.2832*x+vec3(0.,2.094,4.188)); }

void main(){
  vec2 uv=gl_FragCoord.xy/uRes; float a=uRes.x/uRes.y;
  vec2 q=vec2((uv.x*2.-1.)*a, (1.-uv.y)*2.-1.);
  float t=uTime;
  vec3 col;
  if(uP[9]>.5) q.y=-q.y;
  if(uMode==0||uMode==1){
    float disp=uP[8];
    vec3 c;
    for(int k=0;k<3;k++){
      float off=(float(k)-1.)*disp;
      float I = uMode==0 ? arcI(q,off,t) : hourI(q,off,t,a);
      vec3 cc=pal(tm(I)); c[k]=cc[k];
    }
    col=c;
  } else if(uMode==2){
    col=mesh(q,t,a);
  } else if(uMode==3){
    float f=warped(q,t,uP[2]*.9,uP[3]);
    f=clamp((f-.25)/.5,0.,1.);
    float v= uP[0]>.5 ? pow(clamp(1.-abs(2.*f-1.),0.,1.),uP[1]) : clamp(.5+(f-.5)*uP[4],0.,1.);
    col=pal(v);
  } else if(uMode==4){
    float f=warped(q,t,uP[3]*.9,uP[4]); f=clamp((f-.25)/.5,0.,1.);
    if(uP[0]>.5){ float thr=uP[1], w=uP[2];
      float I=exp(-sq((f-thr)/w))+.55*exp(-sq((f-thr-w*2.2)/(w*.6)));
      col=pal(tm(I*1.4));
    } else { col=pal(fract(f*uP[1]+t*.01)); }
  } else if(uMode==5){
    float I=0.;
    for(int k=0;k<3;k++){ if(float(k)<uP[2]){
      float fk=float(k); float fr=2.2/a*uP[4];
      float ph=uSeed*(fk+1.)*3.1+t*(.12+fk*.05);
      float ridge=uP[0]+fk*.07+uP[1]*(sin(q.x*1.1*fr+ph)+.45*sin(q.x*2.3*fr+ph*1.3)+.18*sin(q.x*4.1*fr-ph))/(1.+fk*.4);
      float d=q.y-ridge;
      float line= d<0. ? exp(d/.035) : exp(-d/.05);
      float fill= d>0. ? exp(-d/uP[5])*.55 : 0.;
      I=max(I,(line*1.2+fill)/(1.+fk*.6)); } }
    col=pal(tm(I*uP[3]));
  } else if(uMode==6){
    vec3 base=pal((q.y+1.)*.5);
    float R=uP[0], cy=uP[1]+R; float sd=length(q-vec2(0.,cy))-R;
    float env=exp(-pow(max(sd,0.)/uP[2],1.4))*sstep(-.25,.05,sd);
    vec3 band=1.-uP[4]+uP[4]*iris(sd/uP[3]+.1+t*.03);
    col=base*(1.-env*uP[5])+band*base*env*uP[5];
  } else {
    // image: slow drift (ken-burns), light sweep, living grain
    // starts exactly on the static still (t=0) so the fade-in is seamless, then breathes
    float s=1.+.035*(1.-cos(t*.05));
    vec2 drift=vec2(sin(t*.031),1.-cos(t*.027))*.010;
    float ia=uImgSize.x/uImgSize.y; vec2 iuv=uv;
    if(a>ia){ iuv.y=(iuv.y-.5)*ia/a+.5; } else { iuv.x=(iuv.x-.5)*a/ia+.5; }
    iuv=(iuv-uFocus)/s+uFocus+drift;
    col=texture2D(uImg,vec2(iuv.x,1.-iuv.y)).rgb;
    float sweep=exp(-sq((uv.x+uv.y*.4)-fract(t*.018+.75)*2.4+.4)/.08)*sstep(0.,6.,t);
    col+=col*sweep*.10;
  }
  // ---- live finishing: halftone / ordered dither / grain ----
  if(uHalftone>0.){
    float cs=uHalftone*min(uRes.x,uRes.y)/1200.; float an=radians(uHalftoneAng);
    mat2 m=mat2(cos(an),-sin(an),sin(an),cos(an));
    vec2 g=m*gl_FragCoord.xy/cs; vec2 f=fract(g)-.5;
    float L=dot(col,vec3(.2126,.7152,.0722));
    float r=sqrt(clamp(L,0.,1.))*.62*1.1;
    float dotm=sstep(r+1./cs,r-1./cs,length(f));
    col=mix(col*.18,min(col*1.15,1.),dotm);
  }
  if(uDither>1.){
    vec2 px=floor(gl_FragCoord.xy/max(1.,uDitherPx*min(uRes.x,uRes.y)/1200.));
    float b=bayer4(px);
    col=floor(col*(uDither-1.)+.5+(b-.5))/(uDither-1.);
  }
  float n=h21(gl_FragCoord.xy+fract(t*7.)*911.)-.5;
  float L=dot(col,vec3(.2126,.7152,.0722));
  col+=n*uGrain*2.2*(.45+.55*(1.-abs(L*2.-1.)));
  gl_FragColor=vec4(clamp(col,0.,1.),1.);
}`;

const MODES = { arc: 0, dome: 0, horizon: 0, hourglass: 1, mesh: 2, liquid: 3, thermal: 4, waves: 5, iridescent: 6, image: 7 };

function hex(h) {
  h = h.replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}

const DEFAULT_PAL = {
  glow: ["#030308", "#0a1a5c", "#2f5bff", "#9b7bff", "#ffffff"],
  mesh: ["#1a1f6b", "#ff5a8a", "#ff9e5e", "#5b6cff", "#7fe7ff"],
  liquid: ["#1b1530", "#3c2a6e", "#c05bd6", "#ffb08a", "#fff3d6"],
  thermal: ["#2a1fd6", "#7a2cff", "#ff2bd6", "#ff3b1f", "#ffb000", "#5cff7a"],
  iridescent: ["#fbfaff", "#e9ecff"],
  waves: ["#000000", "#2a0b4a", "#6a2a9c", "#ff4f6a", "#ff9a3c", "#ffe9a8"],
};

/** Map a recipe (same JSON the Python renderer uses) onto shader mode + uniforms. */
export function recipeToUniforms(recipe) {
  const fam = recipe.family || "glow";
  const p = recipe.params || {};
  const finish = recipe.finish || [];
  const has = (op) => finish.find((f) => f.op === op);
  let mode = MODES[fam] ?? 7;
  const shape = p.shape || "arc";
  if (fam === "glow") mode = MODES[shape] ?? 7; // ribbon / bolt -> animated image
  if (has("ascii") || has("pixelate")) mode = 7; // glyph looks live on the static image
  const P = new Float32Array(16);
  let pal = p.palette || DEFAULT_PAL[fam] || DEFAULT_PAL.glow;
  if (fam === "thermal" && p.mode === "edge")
    pal = ["#000000"].concat(p.palette || ["#1a0a6b", "#3d2bff", "#b63cff", "#ff2b6a", "#ff7a00", "#ffd200", "#fffbe0"]);
  if (fam === "thermal" && p.mode !== "edge") pal = pal.concat([pal[0]]);
  if (mode === 0) {
    const dome = shape === "dome";
    P.set([p.radius ?? (shape === "horizon" ? 8 : dome ? 1.5 : 1.7), p.edge_y ?? (dome ? 0.35 : 0.15), p.rim_out ?? 0.1, p.rim_in ?? 0.3,
      p.fill ?? (dome ? 0.55 : 0.25), p.fill_width ?? 0.9, p.spread ?? 1.1, p.intensity ?? 1.6, p.dispersion ?? 0.02, p.flip ? 1 : 0, dome ? 1 : 0]);
  } else if (mode === 1) {
    P.set([p.radius ?? 1.25, p.gap ?? 0.14, p.softness ?? 0.22, 0, 0, 0, 0, p.intensity ?? 1.6, p.dispersion ?? 0.02, p.flip ? 1 : 0]);
  } else if (mode === 2) {
    P.set([p.warp ?? 0.35]);
  } else if (mode === 3) {
    P.set([p.mode === "ridge" ? 1 : 0, p.sharpness ?? 3, p.scale ?? 1.6, p.warp ?? 0.35, p.contrast ?? 1]);
  } else if (mode === 4) {
    const edge = p.mode === "edge";
    P.set([edge ? 1 : 0, edge ? p.threshold ?? 0.55 : p.cycles ?? 1.6, p.width ?? 0.06, p.scale ?? 1.8, p.warp ?? 0.4]);
  } else if (mode === 5) {
    P.set([p.horizon ?? 0.05, p.amplitude ?? 0.09, p.layers ?? 2, p.intensity ?? 1.5, p.frequency ?? 1, p.fill_depth ?? 0.5]);
  } else if (mode === 6) {
    P.set([p.radius ?? 1.9, p.edge_y ?? -0.6, p.width ?? 0.5, p.period ?? 0.45, p.saturation ?? 0.55, p.strength ?? 0.85]);
    if (p.shape !== "arch") mode = 7;
  }
  const grain = has("grain");
  const dither = has("dither");
  const half = has("halftone");
  return {
    mode, P, pal: pal.slice(0, 7).map(hex), pal2: (p.palette2 || pal).slice(0, 7).map(hex),
    seed: ((recipe.seed ?? 1) * 0.6180339) % 1,
    // image mode: the still already carries baked grain, so the live grain only adds shimmer
    grain: (grain ? grain.amount ?? 0.05 : 0.035) * (mode === 7 ? 0.45 : 1),
    dither: dither && mode !== 7 ? dither.levels ?? 4 : 0, ditherPx: dither ? dither.pixel ?? 3 : 3,
    halftone: half && mode !== 7 ? half.cell ?? 9 : 0, halftoneAng: half ? half.angle ?? 22 : 22,
    focus: recipe.focus || [0.5, 0.5],
  };
}

export function mountLegendaryBackground(container, { recipe, image, speed = 1, maxDpr = 1.5, scale = 0.6, fadeMs = 900 } = {}) {
  if (typeof window === "undefined" || !container) return () => {};
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return () => {};
  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true");
  Object.assign(canvas.style, { position: "absolute", inset: "0", width: "100%", height: "100%", opacity: "0",
    transition: `opacity ${fadeMs}ms ease`, pointerEvents: "none" });
  const gl = canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power" });
  if (!gl) return () => {};
  const u = recipeToUniforms(recipe);
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn("[lbg]", gl.getShaderInfoLog(s)); return null; } return s; };
  const vs = sh(gl.VERTEX_SHADER, VERT), fs = sh(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) return () => {};
  const prog = gl.createProgram(); gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return () => {};
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = (n) => gl.getUniformLocation(prog, n);
  const flat = (arr) => { const o = new Float32Array(21); arr.forEach((c, i) => o.set(c, i * 3)); return o; };
  gl.uniform3fv(U("uPal"), flat(u.pal)); gl.uniform1i(U("uN"), u.pal.length);
  gl.uniform3fv(U("uPal2"), flat(u.pal2)); gl.uniform1i(U("uN2"), u.pal2.length);
  gl.uniform1fv(U("uP"), u.P); gl.uniform1i(U("uMode"), u.mode); gl.uniform1f(U("uSeed"), u.seed);
  gl.uniform1f(U("uGrain"), u.grain); gl.uniform1f(U("uDither"), u.dither); gl.uniform1f(U("uDitherPx"), u.ditherPx);
  gl.uniform1f(U("uHalftone"), u.halftone); gl.uniform1f(U("uHalftoneAng"), u.halftoneAng);
  gl.uniform2f(U("uFocus"), u.focus[0], 1 - u.focus[1]);
  const uRes = U("uRes"), uTime = U("uTime");

  let ready = u.mode !== 7;
  if (u.mode === 7) {
    if (!image) return () => {};
    const tex = gl.createTexture(); const img = new Image(); img.crossOrigin = "anonymous";
    const upload = () => {
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
      gl.uniform2f(U("uImgSize"), img.naturalWidth, img.naturalHeight); ready = true;
    };
    img.src = image;
    // decode fully before upload so the first visible frame is never a blank texture
    (img.decode ? img.decode() : new Promise((r) => (img.onload = r))).then(upload, () => {});
  }
  if (getComputedStyle(container).position === "static") container.style.position = "relative";
  container.appendChild(canvas);

  const resize = () => {
    // image mode needs full res; procedural fields are soft, so render small and let CSS upscale
    const s = u.mode === 7 || u.dither || u.halftone ? 1 : scale; // print textures need native pixels
    const dpr = Math.min(window.devicePixelRatio || 1, maxDpr) * s;
    canvas.width = Math.max(2, Math.round(container.clientWidth * dpr));
    canvas.height = Math.max(2, Math.round(container.clientHeight * dpr));
    gl.viewport(0, 0, canvas.width, canvas.height); gl.uniform2f(uRes, canvas.width, canvas.height);
  };
  const ro = new ResizeObserver(resize); ro.observe(container); resize();

  let visible = true, raf = 0, shown = false, drawn = 0, t0 = performance.now(), acc = 0, last = t0;
  const frame = (now) => {
    raf = 0;
    if (!visible || document.hidden) return;
    acc += Math.min(64, now - last) * speed; last = now;
    if (ready) {
      gl.uniform1f(uTime, (u.mode === 7 ? 0 : 20) + acc / 1000); gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (!shown && ++drawn > 1) { shown = true; canvas.style.opacity = "1"; } // reveal after 2 real frames
    }
    raf = requestAnimationFrame(frame);
  };
  const kick = () => { if (!raf && visible && !document.hidden) { last = performance.now(); raf = requestAnimationFrame(frame); } };
  const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; kick(); }); io.observe(container);
  document.addEventListener("visibilitychange", kick);
  kick();
  return () => { cancelAnimationFrame(raf); io.disconnect(); ro.disconnect(); document.removeEventListener("visibilitychange", kick); canvas.remove(); };
}
