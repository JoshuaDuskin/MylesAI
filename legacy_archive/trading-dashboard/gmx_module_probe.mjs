import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
try {
  const v2=require('@gmx-io/sdk/v2');
  const contracts=require('@gmx-io/sdk/configs/contracts');
  if(typeof v2.GmxApiSdk!=='function') throw new Error('GmxApiSdk export missing');
  if(typeof v2.PrivateKeySigner!=='function') throw new Error('PrivateKeySigner export missing');
  if(typeof contracts.getContract!=='function') throw new Error('getContract export missing');
  const sdk=new v2.GmxApiSdk({chainId:42161});
  console.log(JSON.stringify({ok:true,sdk:'2.1.1',client:typeof sdk.fetchMarkets==='function',loader:'commonjs-via-createRequire'}));
} catch (e) {
  console.error(e && e.stack ? e.stack : String(e));
  process.exit(2);
}
