(()=>{const u="https://visits.rezaramji.workers.dev/hit";let s="";try{s=sessionStorage.v||(sessionStorage.v=Math.random().toString(36).slice(2))}catch(e){}
const send=(p,e)=>{try{navigator.sendBeacon(u,JSON.stringify({p,t:document.title,r:document.referrer,s,w:screen.width+"x"+screen.height,e}))}catch(x){}};
send(location.pathname+location.search,0);const dl=/\.(pdf|zip|dmg|pkg|exe|gz|tgz|tar|7z|csv|xlsx?|epub)([?#]|$)|\/releases\//i;
const click=ev=>{if(ev.type=="auxclick"&&ev.button!=1)return;const a=ev.target.closest&&ev.target.closest("a,[data-visit-click]");if(!a)return;if(a.dataset.visitClick)return send(a.dataset.visitClick,1);
const h=a.href||"";if(!h||!(a.hasAttribute("download")||dl.test(h)))return;try{const f=new URL(h).pathname,n=f.split("/").pop();send("download "+decodeURIComponent(/^(latest|releases)?$/.test(n)?f:n),1)}catch(x){}};
document.addEventListener("click",click);document.addEventListener("auxclick",click)})()
