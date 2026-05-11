const fs = require('fs');
const path = 'static/js/line-items.ui.js';
try{
  const src = fs.readFileSync(path,'utf8');
  // attempt to compile
  new Function(src);
  console.log('OK');
}catch(e){
  console.error('PARSE_ERROR', e && e.message);
  if(e && e.stack) console.error(e.stack);
  process.exit(1);
}
