"use client";

import { useEffect, useRef } from "react";

const FRAG = `
precision highp float;
uniform vec2 r; uniform float t; uniform vec2 m; uniform float s;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
  return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float a=.5,v=0.;for(int i=0;i<5;i++){v+=a*n(p);p=p*2.03+vec2(1.7,9.2);a*=.5;}return v;}
void main(){
  vec2 uv=(gl_FragCoord.xy-.5*r)/r.y;
  vec2 p=uv*1.35; p.y+=s*.7;
  p+=(m-.5)*.25;
  vec2 q=vec2(fbm(p+t*.045),fbm(p+vec2(5.2,1.3)-t*.035));
  vec2 w=vec2(fbm(p+3.2*q+vec2(1.7,9.2)+t*.03),fbm(p+3.2*q+vec2(8.3,2.8)-t*.02));
  float f=fbm(p+3.4*w);
  float ink=smoothstep(.42,.9,f+.35*length(w)-.18);
  float vein=smoothstep(.0,.035,abs(f-.56));
  vec3 mag=vec3(1.,.17,.84), vio=vec3(.36,.18,.95);
  vec3 c=mix(vio,mag,smoothstep(.25,.75,w.x))*ink*ink*.62;
  c+=mag*(1.-vein)*ink*.35;
  float vig=smoothstep(1.15,.15,length(uv*vec2(.85,1.15)+vec2(0.,-.1)));
  c*=vig*(1.-s*.85);
  gl_FragColor=vec4(c,1.);
}`;

const VERT = `attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}`;

/** Magenta ink drifting in black water. Pure shader, pauses when off-screen. */
export default function InkCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current!;
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false });
    if (!gl) return;

    const sh = (type: number, src: string) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };
    const prog = gl.createProgram()!;
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const a = gl.getAttribLocation(prog, "a");
    gl.enableVertexAttribArray(a);
    gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);

    const u = (name: string) => gl.getUniformLocation(prog, name);
    const uR = u("r"), uT = u("t"), uM = u("m"), uS = u("s");

    const mouse = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 };
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let raf = 0;
    let visible = true;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5) * 0.75;
      canvas.width = Math.floor(canvas.clientWidth * dpr);
      canvas.height = Math.floor(canvas.clientHeight * dpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
    };
    const move = (e: PointerEvent) => {
      mouse.tx = e.clientX / window.innerWidth;
      mouse.ty = 1 - e.clientY / window.innerHeight;
    };
    const draw = (now: number) => {
      mouse.x += (mouse.tx - mouse.x) * 0.04;
      mouse.y += (mouse.ty - mouse.y) * 0.04;
      gl.uniform2f(uR, canvas.width, canvas.height);
      gl.uniform1f(uT, still ? 12 : now / 1000);
      gl.uniform2f(uM, mouse.x, mouse.y);
      gl.uniform1f(uS, Math.min(1, window.scrollY / window.innerHeight));
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (visible && !still) raf = requestAnimationFrame(draw);
    };

    const io = new IntersectionObserver(([entry]) => {
      const was = visible;
      visible = entry.isIntersecting;
      if (visible && !was) raf = requestAnimationFrame(draw);
    });
    io.observe(canvas);

    resize();
    raf = requestAnimationFrame(draw);
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", move);
    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", move);
    };
  }, []);

  return <canvas ref={ref} className="absolute inset-0 h-full w-full" aria-hidden />;
}
