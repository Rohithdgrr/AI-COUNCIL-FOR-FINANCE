import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Eye, Search, BarChart3, Megaphone, Users, Newspaper, Building2, TrendingUp,
  Zap, MessageSquare, BookOpen, Swords, Activity, Heart, AlertTriangle, ThumbsUp, ThumbsDown, Minus, Globe, Shield, Star, ExternalLink, RefreshCw, Play
} from 'lucide-react'
import { useBrandIntel } from '@/hooks/useMarketQuery'
import { useMCPInvoke } from '@/hooks/useMCPTools'
import AnimatedList from '@/components/ui/AnimatedList'

type BrandTab = 'overview' | 'social' | 'research' | 'competitors' | 'alerts'

const BRAND_TABS: { id: BrandTab; label: string; icon: typeof Activity }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'social', label: 'Social', icon: MessageSquare },
  { id: 'research', label: 'Research', icon: BookOpen },
  { id: 'competitors', label: 'Competitors', icon: Swords },
  { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
]

function SharpContainer({ children, title, icon: Icon, color = 'pink', extraHeaderControls = null }: any) {
  return (
    <div className="group relative h-full">
      <div className={`absolute -inset-[1px] bg-gradient-to-br from-${color}-500 to-transparent rounded-lg opacity-0 group-hover:opacity-30 transition-opacity duration-300 blur-sm pointer-events-none`} />
      <div className="relative h-full flex flex-col bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-lg overflow-hidden shadow-sm transition-shadow group-hover:shadow-[0_0_15px_rgba(200,200,210,0.2)] z-10">
        <div className={`absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-${color}-500 to-transparent opacity-50`} />
        {title && (
           <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xs font-black uppercase tracking-widest text-slate-600 flex items-center gap-2">
                 <Icon className={`w-4 h-4 text-${color}-500`} /> {title}
              </h2>
              {extraHeaderControls}
           </div>
        )}
        <div className="p-5 flex-1 flex flex-col overflow-hidden">
           {children}
        </div>
      </div>
    </div>
  )
}

export default function Brand() {
  const [activeTab, setActiveTab] = useState<BrandTab>('overview')
  const [brand, setBrand] = useState('')
  const [competitor, setCompetitor] = useState('')
  const invoke = useMCPInvoke()
  const brandIntel = useBrandIntel()

  const handleSentiment = () => {
    if (!brand.trim()) return
    invoke.mutate({ tool: 'reddit_sentiment', params: { subreddit: brand.trim().toLowerCase().replace(/\s+/g, ''), limit: 10 } })
  }

  const handleCompetitor = () => {
    if (!competitor.trim()) return
    invoke.mutate({ tool: 'wikipedia_search', params: { query: competitor.trim(), limit: 5 } })
  }

  const handleCompanyProfile = () => {
    if (!brand.trim()) return
    invoke.mutate({ tool: 'company_profile', params: { symbol: brand.trim().toUpperCase() } })
  }

  const result = invoke.data?.result as Record<string, unknown> | undefined

  const redditPosts = ((brandIntel.data?.supplychain_reddit?.posts || []) as Array<Record<string, unknown>>)
  const logisticsPosts = ((brandIntel.data?.logistics_reddit?.posts || []) as Array<Record<string, unknown>>)
  const wikiArticles = ((brandIntel.data?.wiki_articles?.results || []) as Array<Record<string, unknown>>)

  const sentimentScore = useMemo(() => {
    const allPosts = [...redditPosts, ...logisticsPosts]
    if (allPosts.length === 0) return 50
    const avgScore = allPosts.reduce((a, p) => a + Number(p.score || 0), 0) / allPosts.length
    const avgComments = allPosts.reduce((a, p) => a + Number(p.num_comments || 0), 0) / allPosts.length
    return Math.min(100, Math.max(0, Math.round(50 + (avgScore > 10 ? 15 : avgScore > 5 ? 5 : -5) + (avgComments > 5 ? 10 : 0))))
  }, [redditPosts, logisticsPosts])

  const brandHealthScore = useMemo(() => {
    const sentimentWeight = sentimentScore * 0.4
    const engagementWeight = Math.min((redditPosts.length + logisticsPosts.length) * 2, 30)
    const researchWeight = Math.min(wikiArticles.length * 5, 30)
    return Math.round(sentimentWeight + engagementWeight + researchWeight)
  }, [sentimentScore, redditPosts, logisticsPosts, wikiArticles])

  return (
    <div className="relative min-h-[calc(100vh-4rem)] bg-[#f8fafc] overflow-hidden p-4 md:p-8 text-slate-800">
      <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px] opacity-30 pointer-events-none" />
      
      <div className="max-w-[1400px] mx-auto relative z-10 flex flex-col h-full gap-5">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-end justify-between gap-5 shrink-0 border-b border-slate-200 pb-5">
          <div className="flex items-center gap-4">
             <div className="w-12 h-12 bg-slate-900 text-white rounded-md flex items-center justify-center shadow-lg shadow-slate-900/20">
                <Eye className="w-6 h-6" />
             </div>
             <div>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-none">Brand Intel Center</h1>
                <div className="flex items-center gap-2 mt-2">
                   <div className="w-2 h-2 rounded-none bg-pink-500 animate-pulse shadow-[0_0_8px_rgba(236,72,153,0.8)]" />
                   <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Live Global Scan Active</p>
                </div>
             </div>
          </div>
          
          <div className="flex gap-2 w-full md:w-auto overflow-x-auto no-scrollbar pb-1">
             {BRAND_TABS.map(tab => {
                const isActive = activeTab === tab.id;
                return (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)} 
                     className={`flex items-center gap-2 px-5 py-2.5 shrink-0 border rounded-[4px] text-xs font-bold uppercase tracking-widest transition-all ${isActive ? 'bg-slate-900 text-white border-slate-800 shadow-md' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
                     <tab.icon className={`w-3.5 h-3.5 ${isActive ? 'text-pink-400' : 'text-slate-400'}`} /> {tab.label}
                  </button>
                )
             })}
          </div>
        </div>

        {/* Content Viewport */}
        <motion.div layout layoutRoot className="flex-1 w-full flex flex-col gap-5 overflow-y-auto no-scrollbar pb-6 pr-1 relative z-20">
          <AnimatePresence mode="wait">
             <motion.div key={activeTab} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} transition={{ duration: 0.15 }} className="w-full">
                
                {/* ── OVERVIEW TAB ── */}
                {activeTab === 'overview' && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                     <div className="md:col-span-1 flex flex-col gap-5">
                        <SharpContainer title="Overall Brand Health" icon={Heart} color="pink">
                           <div className="flex flex-col items-center gap-6 my-auto justify-center py-6">
                             <div className="relative w-32 h-32 shrink-0">
                               <svg className="w-32 h-32 -rotate-90 drop-shadow-sm" viewBox="0 0 100 100">
                                 <circle cx="50" cy="50" r="44" fill="none" stroke="#f1f5f9" strokeWidth="8" />
                                 <circle cx="50" cy="50" r="44" fill="none" stroke="#ec4899" strokeWidth="8" strokeDasharray={`${brandHealthScore * 2.76} 276`} strokeLinecap="square" className="transition-all duration-1000" />
                               </svg>
                               <div className="absolute inset-0 flex flex-col items-center justify-center">
                                 <span className="text-4xl font-black text-slate-900 leading-none">{brandHealthScore}</span>
                                 <span className="text-xs font-bold uppercase tracking-widest text-slate-500 mt-1">Index</span>
                               </div>
                             </div>
                             <div className="flex flex-col gap-4 w-full px-2">
                               {[
                                 { label: 'Calculated Sentiment', pct: sentimentScore, c: 'bg-pink-500' },
                                 { label: 'Market Engagement', pct: Math.min(redditPosts.length * 4, 100), c: 'bg-violet-500' },
                                 { label: 'Research Visibility', pct: Math.min(wikiArticles.length * 10, 100), c: 'bg-blue-500' },
                               ].map(v => (
                                 <div key={v.label}>
                                   <div className="flex justify-between text-xs font-black uppercase tracking-wider text-slate-600 mb-1.5">
                                     <span>{v.label}</span><span>{v.pct}%</span>
                                   </div>
                                   <div className="w-full h-1.5 bg-slate-100"><div className={`h-full ${v.c}`} style={{ width: `${v.pct}%` }} /></div>
                                 </div>
                               ))}
                             </div>
                           </div>
                        </SharpContainer>
                        
                        <SharpContainer title="Sentiment Breakdown" icon={BarChart3} color="violet">
                           <div className="grid grid-cols-3 gap-3 h-full items-center py-4">
                              <div className="text-center p-3 rounded bg-emerald-50/50 border border-emerald-100">
                                 <ThumbsUp className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                                 <p className="text-xl font-black text-slate-800">{Math.round(sentimentScore * 0.6)}%</p>
                                 <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-1">Positive</p>
                              </div>
                              <div className="text-center p-3 rounded bg-slate-50 border border-slate-200">
                                 <Minus className="w-6 h-6 text-slate-400 mx-auto mb-2" />
                                 <p className="text-xl font-black text-slate-800">{Math.round(sentimentScore * 0.25)}%</p>
                                 <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-1">Neutral</p>
                              </div>
                              <div className="text-center p-3 rounded bg-red-50/50 border border-red-100">
                                 <ThumbsDown className="w-6 h-6 text-red-500 mx-auto mb-2" />
                                 <p className="text-xl font-black text-slate-800">{Math.round(sentimentScore * 0.15)}%</p>
                                 <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-1">Negative</p>
                              </div>
                           </div>
                        </SharpContainer>
                     </div>

                     <div className="md:col-span-2">
                        <SharpContainer title="Live Knowledge Aggregation" icon={Globe} color="blue">
                           <div className="grid grid-cols-2 gap-5 h-full min-h-[400px]">
                              {/* Reddit Col */}
                              <div className="flex flex-col border border-slate-200 rounded bg-slate-50/50 p-3 overflow-hidden h-[500px]">
                                 <p className="text-xs font-black uppercase tracking-widest text-slate-600 mb-3 px-1 border-b border-slate-200 pb-2 flex items-center gap-2"><Users className="w-3.5 h-3.5 text-pink-500" /> Reddit Vector</p>
                                 {brandIntel.isLoading ? <div className="animate-pulse space-y-3"><div className="h-14 bg-slate-200 rounded"/><div className="h-14 bg-slate-200 rounded"/></div> : (
                                    <AnimatedList items={redditPosts.slice(0, 10)} containerHeight="450px" itemClassName="!p-0"
                                       renderItem={p => (
                                          <div className="bg-white p-3 border border-slate-200 rounded mb-3 shadow-sm hover:border-slate-300 transition-colors">
                                             <p className="text-sm font-bold text-slate-800 line-clamp-2 leading-relaxed">{String(p.title || '')}</p>
                                             <div className="flex items-center justify-between mt-3">
                                                <span className="text-xs font-bold text-slate-500">u/{String(p.author).substring(0, 15)}</span>
                                                <div className="flex gap-3 text-xs font-black"><span className="text-emerald-600">▲{Number(p.score)}</span><span className="text-slate-400">💬{Number(p.num_comments)}</span></div>
                                             </div>
                                          </div>
                                       )}
                                    />
                                 )}
                              </div>
                              {/* Wiki Col */}
                              <div className="flex flex-col border border-slate-200 rounded bg-slate-50/50 p-3 overflow-hidden h-[500px]">
                                 <p className="text-xs font-black uppercase tracking-widest text-slate-600 mb-3 px-1 border-b border-slate-200 pb-2 flex items-center gap-2"><Newspaper className="w-3.5 h-3.5 text-blue-500" /> Media Vector</p>
                                 {brandIntel.isLoading ? <div className="animate-pulse space-y-3"><div className="h-16 bg-slate-200 rounded"/><div className="h-16 bg-slate-200 rounded"/></div> : (
                                    <AnimatedList items={wikiArticles.slice(0, 8)} containerHeight="450px" itemClassName="!p-0"
                                       renderItem={a => (
                                          <a href={String(a.url||'#')} target="_blank" rel="noreferrer" className="block bg-white p-3 border border-slate-200 rounded mb-3 shadow-sm hover:border-blue-400 transition-colors">
                                             <p className="text-sm font-bold text-blue-800 line-clamp-2 leading-tight">{String(a.title || '')}</p>
                                             <p className="text-xs font-medium text-slate-500 line-clamp-2 mt-2 leading-relaxed">{String(a.snippet || '').replace(/<[^>]*>?/gm, '')}</p>
                                          </a>
                                       )}
                                    />
                                 )}
                              </div>
                           </div>
                        </SharpContainer>
                     </div>
                  </div>
                )}

                {/* ── SOCIAL TAB ── */}
                {activeTab === 'social' && (
                  <div className="flex flex-col gap-5">
                    <SharpContainer title="Social Sentiment Engine" icon={BarChart3} color="pink">
                        <div className="flex gap-3 items-center p-4 bg-slate-50 border border-slate-200 rounded mb-5">
                           <input type="text" value={brand} onChange={e => setBrand(e.target.value)} placeholder="Type Subreddit or Brand (e.g. supplychain)..." className="flex-1 bg-white border border-slate-300 rounded px-4 py-2.5 text-sm font-bold outline-none focus:border-pink-500 text-slate-800" />
                           <button onClick={handleSentiment} className="px-6 py-2.5 bg-pink-600 hover:bg-pink-700 text-white text-xs font-black uppercase tracking-widest rounded shadow-sm flex items-center gap-2"><Search className="w-4 h-4" /> Analyze</button>
                        </div>
                        {result && (
                           <div className="mb-5 bg-slate-900 border border-slate-800 rounded p-5 relative overflow-hidden">
                              <div className="absolute top-0 right-0 w-32 h-32 bg-pink-500 blur-[80px] opacity-20 pointer-events-none" />
                              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4 text-pink-400" /> AI Sentiment Analysis</h3>
                              <pre className="text-xs text-slate-300 font-mono overflow-auto">{JSON.stringify(result, null, 2)}</pre>
                           </div>
                        )}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 min-h-[400px]">
                           <div className="flex flex-col border border-slate-200 rounded p-3">
                              <h3 className="text-xs font-black uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2"><Users className="w-4 h-4 text-pink-500" /> r/supplychain Live</h3>
                              <AnimatedList items={redditPosts} containerHeight="400px" itemClassName="!p-0"
                                 renderItem={p => (
                                    <div className="bg-slate-50 p-3 border border-slate-200 rounded mb-3">
                                       <p className="text-sm font-bold text-slate-800 line-clamp-2">{String(p.title || '')}</p>
                                       <div className="flex justify-between mt-2"><span className="text-xs font-bold text-slate-500">u/{String(p.author)}</span><div className="flex gap-3 text-xs font-black"><span className="text-emerald-600">▲{Number(p.score)}</span><span className="text-slate-400">💬{Number(p.num_comments)}</span></div></div>
                                    </div>
                                 )}
                              />
                           </div>
                           <div className="flex flex-col border border-slate-200 rounded p-3">
                              <h3 className="text-xs font-black uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2"><Users className="w-4 h-4 text-orange-500" /> r/logistics Live</h3>
                              <AnimatedList items={logisticsPosts} containerHeight="400px" itemClassName="!p-0"
                                 renderItem={p => (
                                    <div className="bg-slate-50 p-3 border border-slate-200 rounded mb-3">
                                       <p className="text-sm font-bold text-slate-800 line-clamp-2">{String(p.title || '')}</p>
                                       <div className="flex justify-between mt-2"><span className="text-xs font-bold text-slate-500">u/{String(p.author)}</span><div className="flex gap-3 text-xs font-black"><span className="text-emerald-600">▲{Number(p.score)}</span><span className="text-slate-400">💬{Number(p.num_comments)}</span></div></div>
                                    </div>
                                 )}
                              />
                           </div>
                        </div>
                    </SharpContainer>
                  </div>
                )}

                {/* ── RESEARCH TAB ── */}
                {activeTab === 'research' && (
                  <div className="flex flex-col gap-5">
                    <SharpContainer title="Company Intel Lookup" icon={Building2} color="violet">
                        <div className="flex gap-3 items-center p-4 bg-slate-50 border border-slate-200 rounded mb-5">
                           <input type="text" value={brand} onChange={e => setBrand(e.target.value)} placeholder="Type Stock Symbol (e.g. AAPL, TSM)..." className="flex-1 bg-white border border-slate-300 rounded px-4 py-2.5 text-sm font-bold outline-none focus:border-violet-500 text-slate-800" />
                           <button onClick={handleCompanyProfile} className="px-6 py-2.5 bg-violet-600 hover:bg-violet-700 text-white text-xs font-black uppercase tracking-widest rounded shadow-sm flex items-center gap-2"><Search className="w-4 h-4" /> Deep Scan</button>
                        </div>
                        {result && (
                           <div className="mb-5 bg-slate-900 border border-slate-800 rounded p-5 relative overflow-hidden">
                              <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500 blur-[80px] opacity-20 pointer-events-none" />
                              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2"><Building2 className="w-4 h-4 text-violet-400" /> Company Profile Output</h3>
                              <pre className="text-xs text-slate-300 font-mono overflow-auto">{JSON.stringify(result, null, 2)}</pre>
                           </div>
                        )}
                        <div className="flex flex-col border border-slate-200 rounded p-3 min-h-[300px]">
                            <h3 className="text-xs font-black uppercase tracking-widest text-slate-600 mb-3 flex items-center gap-2"><Newspaper className="w-4 h-4 text-blue-500" /> Reference Articles (Wikipedia)</h3>
                            <AnimatedList items={wikiArticles} containerHeight="400px" itemClassName="!p-0"
                               renderItem={a => (
                                  <a href={String(a.url||'#')} target="_blank" rel="noreferrer" className="block bg-slate-50 p-4 border border-slate-200 rounded mb-3 hover:border-blue-400 hover:bg-white transition-all">
                                     <p className="text-sm font-bold text-blue-800 mb-2">{String(a.title || '')}</p>
                                     <p className="text-xs font-medium text-slate-600">{String(a.snippet || '').replace(/<[^>]*>?/gm, '')}</p>
                                  </a>
                               )}
                            />
                        </div>
                    </SharpContainer>
                  </div>
                )}

                {/* ── COMPETITORS TAB ── */}
                {activeTab === 'competitors' && (
                  <div className="flex flex-col gap-5">
                    <SharpContainer title="Competitor Comparison" icon={Swords} color="blue">
                        <div className="flex gap-3 items-center p-4 bg-slate-50 border border-slate-200 rounded mb-5">
                           <input type="text" value={competitor} onChange={e => setCompetitor(e.target.value)} placeholder="Type Competitor Name..." className="flex-1 bg-white border border-slate-300 rounded px-4 py-2.5 text-sm font-bold outline-none focus:border-blue-500 text-slate-800" />
                           <button onClick={handleCompetitor} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-black uppercase tracking-widest rounded shadow-sm flex items-center gap-2"><Search className="w-4 h-4" /> Compare</button>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
                          {[
                            { name: 'Your Brand', score: brandHealthScore, sentiment: sentimentScore, color: 'bg-pink-500', iconColor: 'text-pink-500', badge: 'You' },
                            { name: 'Competitor A', score: Math.round(brandHealthScore * 0.85), sentiment: Math.round(sentimentScore * 0.9), color: 'bg-blue-500', iconColor: 'text-blue-500', badge: 'Rival' },
                            { name: 'Competitor B', score: Math.round(brandHealthScore * 0.72), sentiment: Math.round(sentimentScore * 0.75), color: 'bg-amber-500', iconColor: 'text-amber-500', badge: 'Rival' },
                          ].map(comp => (
                            <div key={comp.name} className="border border-slate-200 rounded-md p-5 bg-white shadow-sm flex flex-col">
                               <div className="flex justify-between items-center mb-4">
                                  <div className="flex items-center gap-2">
                                     <Star className={`w-5 h-5 ${comp.iconColor} fill-current/20`} />
                                     <span className="text-sm font-bold text-slate-900">{comp.name}</span>
                                  </div>
                                  <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${comp.badge === 'You' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{comp.badge}</span>
                               </div>
                               <div className="space-y-4 flex-1">
                                  <div>
                                     <div className="flex justify-between text-xs font-bold text-slate-600 mb-1.5"><span>Health Score</span><span>{comp.score}</span></div>
                                     <div className="w-full h-1.5 bg-slate-100"><div className={`h-full ${comp.color}`} style={{ width: `${comp.score}%` }} /></div>
                                  </div>
                                  <div>
                                     <div className="flex justify-between text-xs font-bold text-slate-600 mb-1.5"><span>Sentiment</span><span>{comp.sentiment}%</span></div>
                                     <div className="w-full h-1.5 bg-slate-100"><div className={`h-full ${comp.color}`} style={{ width: `${comp.sentiment}%` }} /></div>
                                  </div>
                               </div>
                            </div>
                          ))}
                        </div>

                        {result && (
                           <div className="bg-slate-900 border border-slate-800 rounded p-5 relative overflow-hidden">
                              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500 blur-[80px] opacity-20 pointer-events-none" />
                              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2"><Swords className="w-4 h-4 text-blue-400" /> AI Competitor Intel</h3>
                              <pre className="text-xs text-slate-300 font-mono overflow-auto">{JSON.stringify(result, null, 2)}</pre>
                           </div>
                        )}
                    </SharpContainer>
                  </div>
                )}

                {/* ── ALERTS TAB ── */}
                {activeTab === 'alerts' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                     <SharpContainer title="System Flagged Events" icon={AlertTriangle} color="amber">
                        <div className="space-y-3 py-2">
                           {[
                              { c: 'bg-amber-50 border-amber-200 text-amber-800', t: 'Sentiment Drop Detected', i: AlertTriangle, d: '-12% in 24h sector', m: '2h' },
                              { c: 'bg-blue-50 border-blue-200 text-blue-800', t: 'Emerging Competitor', i: Building2, d: 'Brand Y mentioned heavily', m: '4h' },
                              { c: 'bg-emerald-50 border-emerald-200 text-emerald-800', t: 'ESG Article Spike', i: Globe, d: '+45% traffic increment', m: '6h' }
                           ].map((a, i) => (
                              <div key={i} className={`flex items-start gap-4 p-4 rounded border ${a.c}`}>
                                 <div className="p-2 rounded bg-white shadow-sm shrink-0"><a.i className="w-4 h-4" /></div>
                                 <div className="flex-1 min-w-0">
                                    <p className="text-sm font-bold">{a.t}</p>
                                    <p className="text-xs font-medium opacity-90 mt-1">{a.d}</p>
                                 </div>
                                 <span className="text-[10px] font-black uppercase opacity-60 shrink-0">{a.m}</span>
                              </div>
                           ))}
                        </div>
                     </SharpContainer>
                     <SharpContainer title="Intrusion & Tracking Defense" icon={Shield} color="indigo">
                        <div className="grid grid-cols-1 gap-3 py-2">
                           {[
                              { l: 'Keyword Listening Protocol', s: 'active', bg: 'bg-emerald-50 border-emerald-200' },
                              { l: 'Adversary Tracking Network', s: 'active', bg: 'bg-emerald-50 border-emerald-200' },
                              { l: 'PR Crisis Net Detection', s: 'standby', bg: 'bg-slate-50 border-slate-200' },
                              { l: 'Social Volatility Check', s: 'alert', bg: 'bg-amber-50 border-amber-200' }
                           ].map(item => (
                              <div key={item.l} className={`flex items-center justify-between p-4 rounded border ${item.bg}`}>
                                 <span className="text-sm font-bold text-slate-800">{item.l}</span>
                                 <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded ${item.s === 'active' ? 'bg-emerald-500 text-white shadow-[0_0_10px_rgba(16,185,129,0.5)]' : item.s === 'alert' ? 'bg-amber-500 text-white animate-pulse' : 'bg-slate-200 text-slate-600'}`}>{item.s}</span>
                              </div>
                           ))}
                        </div>
                     </SharpContainer>
                  </div>
                )}

             </motion.div>
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  )
}
