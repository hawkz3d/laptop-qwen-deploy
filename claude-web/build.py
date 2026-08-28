import re, pathlib
d = pathlib.Path('.')
tpl = (d/'index.template.html').read_text(encoding='utf-8')
marked = (d/'marked.min.js').read_text(encoding='utf-8')
orig = pathlib.Path('/tmp/cdp/index.html').read_text(encoding='utf-8')
m = re.search(r'href="data:image/png;base64,([^"]+)"', orig)
fav = m.group(1)

# 修复删除按钮闭包泄漏（原版遗留 bug：var s 循环变量共享）
buggy = """      div.querySelector('.del').onclick=function(e){
        e.stopPropagation();
        if(!confirm('删除该会话?'))return;
        fetch('/api/sessions/'+s.id,{method:'DELETE',headers:hdrs()})
        .then(function(r){return r.json()})
        .then(function(d){if(d.ok&&s.id===currentSid)newSession();else loadSessions()});
      };"""
fixed = """      (function(sess){
        div.querySelector('.del').onclick=function(e){
          e.stopPropagation();
          if(!confirm('删除该会话?'))return;
          fetch('/api/sessions/'+sess.id,{method:'DELETE',headers:hdrs()})
          .then(function(r){return r.json()})
          .then(function(dd){if(dd.ok&&sess.id===currentSid)newSession();else loadSessions()});
        };
      })(s);"""
assert buggy in tpl, 'closure pattern not found'
tpl = tpl.replace(buggy, fixed)

out = tpl.replace('__MARKED_SRC__', marked).replace('__FAVICON__', fav)
(d/'index.html').write_text(out, encoding='utf-8')
print('built', len(out), 'bytes; favicon', len(fav), 'b64 chars')
