const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'templates', 'add_maintenance_record.html');
const src = fs.readFileSync(file,'utf8');
const re = /<script(?:[^>]*?)>([\s\S]*?)<\/script>/gi;
let m; let idx=0;
while((m=re.exec(src))){
    idx++;
    const content = m[1];
    // skip external scripts (content likely whitespace)
    if(!content || !content.trim()) continue;
    try{
        new Function(content);
        console.log('OK script index', idx, 'length', content.length);
    }catch(e){
        console.error('BROKEN script index', idx, 'error:', e && e.message);
        const lines = content.split('\n');
        const previewStart = Math.max(0, Math.floor(lines.length/2)-10);
        console.error('--- preview around middle ---');
        for(let i=Math.max(0,previewStart); i<Math.min(lines.length, previewStart+40); i++){
            console.error((i+1)+': '+lines[i]);
        }
        process.exit(1);
    }
}
console.log('Checked', idx, 'script tags');
