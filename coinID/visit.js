(()=>{const u="/_e";let s="";try{s=sessionStorage.v||(sessionStorage.v=Math.random().toString(36).slice(2))}catch(e){}
const v=Math.random().toString(36).slice(2),P=location.pathname+location.search,n=navigator,mq=q=>{try{return matchMedia(q).matches}catch(e){}};
const send=(p,e,o)=>{try{n.sendBeacon(u,JSON.stringify(Object.assign({p,t:document.title,r:document.referrer,s,v,w:screen.width+"x"+screen.height,e},o)))}catch(x){}};
const c=n.connection||{},nt=()=>(performance.getEntriesByType&&performance.getEntriesByType("navigation")[0])||{};let tz="";try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone}catch(e){}
send(P,0,{l:(n.languages||[n.language]).join(","),vp:innerWidth+"x"+innerHeight,dpr:devicePixelRatio,tz,x:{url:location.href,nav:nt().type,cores:n.hardwareConcurrency,mem:n.deviceMemory,touch:n.maxTouchPoints,plat:n.platform,
net:c.effectiveType,down:c.downlink,rtt:c.rtt,save:c.saveData,dark:mq("(prefers-color-scheme: dark)"),motion:mq("(prefers-reduced-motion: reduce)"),contrast:mq("(prefers-contrast: more)"),coarse:mq("(pointer: coarse)"),
avail:screen.availWidth+"x"+screen.availHeight,depth:screen.colorDepth,orient:(screen.orientation||{}).type,gpc:n.globalPrivacyControl,dnt:n.doNotTrack,frame:top!==self,hidden:document.visibilityState!="visible",app:mq("(display-mode: standalone)")}});
const dl=/\.(pdf|zip|dmg|pkg|exe|gz|tgz|tar|7z|csv|xlsx?|epub)([?#]|$)|\/releases\//i;let shown=document.visibilityState=="visible"?Date.now():0,seen=0,deep=0,clicks=0,copies=0;
const depth=()=>{const h=document.documentElement.scrollHeight;deep=Math.max(deep,h?Math.min(100,Math.round(100*(scrollY+innerHeight)/h)):100)};depth();addEventListener("scroll",depth,{passive:true});addEventListener("load",depth);
const end=()=>{if(!shown)return;seen+=Date.now()-shown;shown=0;const t=nt();send(P,2,{d:seen,sc:deep,x:{clicks,copies,ttfb:Math.round(t.responseStart||0),dom:Math.round(t.domContentLoadedEventEnd||0),load:Math.round(t.loadEventEnd||0)}})};
document.addEventListener("visibilitychange",()=>{document.visibilityState=="hidden"?end():shown=shown||Date.now()});addEventListener("pagehide",end);
document.addEventListener("copy",()=>{copies++;send("copy",1)});
const click=ev=>{clicks++;if(ev.type=="auxclick"&&ev.button!=1)return;const a=ev.target.closest&&ev.target.closest("a,[data-visit-click]");if(!a)return;if(a.dataset.visitClick)return send(a.dataset.visitClick,1);
const h=a.href||"";if(!h)return;try{const l=new URL(h),f=l.pathname,m=f.split("/").pop();if(a.hasAttribute("download")||dl.test(h))return send("download "+decodeURIComponent(/^(latest|releases)?$/.test(m)?f:m),1);
if(l.protocol=="mailto:")return send("out email",1);if(/^https?:$/.test(l.protocol)&&l.host!=location.host)send("out "+l.host+decodeURIComponent(f).replace(/\/$/,""),1)}catch(x){}};
document.addEventListener("click",click);document.addEventListener("auxclick",click)})()
