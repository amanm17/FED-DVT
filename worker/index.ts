interface Env { ASSETS: Fetcher; DB?: D1Database; RAW_DATA?: R2Bucket; COMTRADE_API_KEY?: string }

const json = (data: unknown, status=200) => new Response(JSON.stringify(data), { status, headers: { 'content-type':'application/json; charset=utf-8', 'cache-control':'public, max-age=300' } })

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (url.pathname === '/api/health') return json({ ok:true, service:'HStat.India', version:'0.1.0', database: Boolean(env.DB), rawStorage: Boolean(env.RAW_DATA) })
    if (url.pathname === '/api/products' && env.DB) {
      const rows = await env.DB.prepare('SELECT hs6, name, family FROM products ORDER BY hs6 LIMIT 500').all()
      return json(rows.results)
    }
    if (url.pathname.startsWith('/api/product/') && env.DB) {
      const hs6 = url.pathname.split('/').pop() || ''
      const product = await env.DB.prepare('SELECT * FROM products WHERE hs6 = ?').bind(hs6).first()
      if (!product) return json({error:'Product not found'},404)
      const india8 = await env.DB.prepare('SELECT * FROM india_tariff_lines WHERE parent_hs6 = ? ORDER BY code').bind(hs6).all()
      return json({ product, india8: india8.results })
    }
    if (url.pathname.startsWith('/api/')) return json({ error:'API route unavailable or database not bound' }, 503)
    return env.ASSETS.fetch(request)
  },
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    if (!env.COMTRADE_API_KEY || !env.RAW_DATA) return
    ctx.waitUntil(env.RAW_DATA.put(`manifests/scheduled-${new Date().toISOString()}.json`, JSON.stringify({status:'scheduled ingestion hook ready', timestamp:new Date().toISOString()}), {httpMetadata:{contentType:'application/json'}}))
  }
}
