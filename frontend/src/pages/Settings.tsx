import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSettingsStore } from '@/store/settingsStore'
import { settingsApi } from '@/lib/api'
import {
  Save, CheckCircle2, Settings as SettingsIcon, Key, Cpu,
  MessageSquare, Type, Zap, Database, RotateCcw,
  Eye, EyeOff, ShieldCheck, HardDrive, Sparkles, Moon, Sun, Monitor
} from 'lucide-react'

type SettingsTab = 'general' | 'response' | 'appearance' | 'advanced' | 'datasources'

function PasswordInput({ label, value, onChange }: { label: string, value: string, onChange: (v: string) => void }) {
  const [show, setShow] = useState(false);
  return (
    <div className="group relative">
      <div className="absolute -inset-[1px] bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm pointer-events-none" />
      <div className="relative bg-white/90 backdrop-blur-md border border-slate-200 rounded-lg flex items-center transition-all group-focus-within:border-indigo-500 group-focus-within:shadow-[0_0_15px_rgba(79,70,229,0.15)] group-hover:border-transparent z-10">
        <div className="px-4 py-2.5 flex flex-col justify-center flex-1">
          <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">{label}</label>
          <input 
            type={show ? "text" : "password"} 
            value={value} 
            onChange={e => onChange(e.target.value)} 
            placeholder="••••••••••••••••"
            className="w-full bg-transparent text-sm font-mono font-medium text-slate-900 outline-none placeholder:text-slate-300" 
          />
        </div>
        <button onClick={() => setShow(!show)} className="w-10 h-10 shrink-0 flex items-center justify-center text-slate-400 hover:text-indigo-600 transition-colors">
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
    </div>
  )
}

function FancySlider({ label, value, min, max, step, onChange, icon: Icon, unit = '' }: any) {
  const percentage = ((value - min) / (max - min)) * 100;
  return (
    <div className="group relative">
       <div className="absolute -inset-[1px] bg-gradient-to-r from-violet-500 to-indigo-500 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm pointer-events-none" />
       <div className="relative bg-white/90 backdrop-blur-md border border-slate-200 p-5 rounded-lg transition-all group-hover:border-transparent z-10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Icon className="w-4 h-4 text-slate-500" />
              <span className="text-[11px] font-bold uppercase tracking-widest text-slate-700">{label}</span>
            </div>
            <div className="px-2 py-0.5 bg-slate-100/50 border border-slate-200 rounded text-xs font-black text-slate-800">
              {value}{unit}
            </div>
          </div>
          <div className="relative h-1.5 rounded-none bg-slate-200 overflow-visible flex items-center cursor-pointer">
            <div className="absolute left-0 h-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]" style={{ width: `${percentage}%` }} />
            {/* The sharp knob */}
            <div 
               className="absolute w-2 h-4 bg-white border border-indigo-500 shadow-sm"
               style={{ left: `calc(${percentage}% - 4px)` }}
            />
            <input 
              type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(Number(e.target.value))} 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
            />
          </div>
          <div className="flex justify-between mt-3">
            <span className="text-[9px] font-bold uppercase text-slate-400">{min}{unit}</span>
            <span className="text-[9px] font-bold uppercase text-slate-400">{max}{unit}</span>
          </div>
       </div>
    </div>
  )
}

function SharpCard({ children, title, subtitle, icon: Icon, color = 'indigo' }: any) {
  return (
     <div className="group relative">
        <div className={`absolute -inset-[1px] bg-gradient-to-b from-${color}-500/20 to-transparent rounded-lg opacity-0 group-hover:opacity-50 transition-opacity duration-500 blur-md pointer-events-none`} />
        <div className="relative flex flex-col h-full bg-white/80 backdrop-blur-xl border border-slate-200/80 rounded-lg overflow-hidden shadow-sm hover:shadow-[0_0_30px_rgba(200,200,210,0.2)] transition-shadow duration-300 z-10">
           {/* Card sharp header edge */}
           <div className={`absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-${color}-500 to-transparent opacity-50`} />
           
           <div className="p-6 md:p-8 flex-1">
              <div className="flex items-center gap-4 mb-8">
                 <div className={`w-8 h-8 flex items-center justify-center text-${color}-600 bg-${color}-50 border border-${color}-100 rounded-md`}>
                    <Icon className="w-4 h-4" />
                 </div>
                 <div>
                    <h3 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h3>
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">{subtitle}</p>
                 </div>
              </div>
              <div className="space-y-6">
                 {children}
              </div>
           </div>
        </div>
     </div>
  );
}

export default function Settings() {
  const { settings, updateSettings, reset } = useSettingsStore()
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleSave = async () => {
    try {
      await settingsApi.update(settings as unknown as Record<string, unknown>)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch { } 
  }

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
    { id: 'general', label: 'System Core', icon: <SettingsIcon className="w-3.5 h-3.5" /> },
    { id: 'response', label: 'LLM Params', icon: <MessageSquare className="w-3.5 h-3.5" /> },
    { id: 'appearance', label: 'Interface', icon: <Type className="w-3.5 h-3.5" /> },
    { id: 'datasources', label: 'Data Feeds', icon: <Database className="w-3.5 h-3.5" /> },
    { id: 'advanced', label: 'Tuning', icon: <Zap className="w-3.5 h-3.5" /> },
  ]

  return (
    <div className="relative min-h-[calc(100vh-4rem)] bg-[#f8fafc] overflow-hidden p-4 md:p-8 selection:bg-indigo-500/20 text-slate-800">
      
      {/* Structural Minimal Background */}
      <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px] opacity-30 pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10 flex flex-col h-full gap-8">
        
        {/* Sharp Header */}
        <div className="flex flex-col md:flex-row items-end justify-between gap-6 shrink-0 border-b border-slate-200 pb-6">
          <div className="flex items-center gap-4">
             <div className="relative flex items-center justify-center w-12 h-12 bg-slate-900 text-white rounded-md shadow-lg shadow-slate-900/20">
               <SettingsIcon className="w-6 h-6" />
             </div>
             <div>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight">Configuration</h1>
                <div className="flex items-center gap-2 mt-1">
                   <div className="w-1.5 h-1.5 rounded-none bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                   <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400">Settings Registry Valid</p>
                </div>
             </div>
          </div>

          <div className="flex gap-3">
             <button onClick={reset} className="px-5 py-2.5 rounded-md text-[10px] font-black uppercase tracking-widest text-slate-500 bg-white border border-slate-200 shadow-sm transition-all hover:border-slate-300 hover:text-slate-800 flex items-center gap-2">
                <RotateCcw className="w-3.5 h-3.5" /> Reset Default
             </button>
             <div className="relative group/btn">
               <div className="absolute -inset-[1px] bg-indigo-500/50 rounded-md opacity-0 group-hover/btn:opacity-100 blur transition-opacity" />
               <button onClick={handleSave} className="relative px-6 py-2.5 rounded-md text-[10px] font-black uppercase tracking-widest text-white bg-slate-900 border border-slate-800 shadow-lg transition-all active:scale-95 flex items-center gap-2 group-hover/btn:bg-indigo-600 group-hover/btn:border-indigo-500 backdrop-blur-md">
                  {saveSuccess ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Save className="w-3.5 h-3.5" />}
                  {saveSuccess ? 'Committed' : 'Save Config'}
               </button>
             </div>
          </div>
        </div>

        {/* Layout */}
        <div className="flex-1 flex flex-col md:flex-row gap-8 items-start">
           
           {/* Minimal Sharp Sidebar */}
           <div className="w-full md:w-64 shrink-0 flex flex-col gap-1">
             {tabs.map(tab => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`relative w-full flex items-center gap-3 px-4 py-3 rounded-md text-xs font-bold uppercase tracking-widest transition-colors outline-none group ${isActive ? 'text-indigo-600 bg-white border border-indigo-100 shadow-[0_4px_20px_rgba(99,102,241,0.05)]' : 'text-slate-500 border border-transparent hover:bg-slate-200/50 hover:text-slate-900'}`}
                  >
                     {isActive && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-1/2 bg-indigo-500 rounded-r-md shadow-[0_0_10px_rgba(99,102,241,0.8)]" />}
                     <span className={`transition-colors ${isActive ? 'text-indigo-500' : 'text-slate-400 group-hover:text-slate-500'}`}>
                        {tab.icon}
                     </span>
                     <span>{tab.label}</span>
                  </button>
                )
             })}
             
             <div className="mt-8 border-t border-slate-200 pt-4 px-4 flex items-center gap-3 opacity-60">
                <ShieldCheck className="w-5 h-5 text-slate-500" />
                <p className="text-[8px] font-black text-slate-400 uppercase tracking-widest leading-relaxed">Local Environment Active<br/>No External Broadcast</p>
             </div>
           </div>

           {/* Content Canvas */}
           <motion.div layout layoutRoot className="flex-1 w-full gap-6 flex flex-col">
              <AnimatePresence mode="wait">
                 <motion.div
                   key={activeTab}
                   initial={{ opacity: 0, y: 5 }}
                   animate={{ opacity: 1, y: 0 }}
                   exit={{ opacity: 0, y: -5 }}
                   transition={{ duration: 0.2 }}
                   className="space-y-6"
                 >
                    {activeTab === 'general' && (
                       <>
                          <SharpCard title="API Keys" subtitle="Telemetry Configuration" icon={Key} color="indigo">
                             <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <PasswordInput label="LLM Provider Key" value={settings.api_key} onChange={v => updateSettings({ api_key: v })} />
                                <PasswordInput label="MCP Router Key" value={settings.mcp_api_key} onChange={v => updateSettings({ mcp_api_key: v })} />
                             </div>
                          </SharpCard>
                          
                          <SharpCard title="RAG Engine" subtitle="Vector Tuning & Thresholds" icon={Cpu} color="violet">
                             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                                <FancySlider label="Top-K Retrieval" value={settings.rag_top_k} min={1} max={20} step={1} onChange={(v: number) => updateSettings({ rag_top_k: v })} icon={Database} unit=" docs" />
                                <FancySlider label="Chunk Size" value={settings.rag_chunk_size} min={512} max={4096} step={128} onChange={(v: number) => updateSettings({ rag_chunk_size: v })} icon={HardDrive} unit=" tks" />
                                <FancySlider label="Chunk Overlap" value={settings.rag_chunk_overlap} min={0} max={500} step={50} onChange={(v: number) => updateSettings({ rag_chunk_overlap: v })} icon={Sparkles} unit=" tks" />
                             </div>
                          </SharpCard>
                       </>
                    )}

                    {activeTab === 'appearance' && (
                       <SharpCard title="Visual Identity" subtitle="Aesthetics & Scalability" icon={Monitor} color="cyan">
                          <div className="space-y-10">
                             {/* Theme Mode Minimal */}
                             <div>
                                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Color Protocol</h4>
                                <div className="flex flex-wrap gap-3">
                                   {[
                                     { id: 'light', icon: Sun, label: 'Luminous Mode' },
                                     { id: 'dark', icon: Moon, label: 'Obsidian Mode' },
                                     { id: 'system', icon: Monitor, label: 'System Sync' }
                                   ].map(theme => {
                                      const isSel = settings.theme === theme.id || (theme.id === 'light' && !settings.theme)
                                      return (
                                        <button key={theme.id} onClick={() => updateSettings({ theme: theme.id })} className={`flex items-center gap-3 px-5 py-3 border rounded-md transition-all group relative ${isSel ? 'bg-slate-900 border-slate-900 text-white shadow-lg' : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'}`}>
                                           <div className={`absolute -inset-[1px] bg-slate-900 rounded-md opacity-0 transition-opacity blur shadow-[0_0_10px_rgba(15,23,42,0.4)] pointer-events-none ${isSel ? 'opacity-100' : 'group-hover:opacity-30'}`} z-index="-1" />
                                           <theme.icon className={`w-4 h-4 relative z-10 ${isSel ? 'text-slate-300' : 'text-slate-400'}`} />
                                           <span className="text-xs font-bold uppercase tracking-widest relative z-10">{theme.label}</span>
                                        </button>
                                      )
                                   })}
                                </div>
                             </div>

                             {/* Typography Sharp */}
                             <div>
                                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Baseline Typography Scale</h4>
                                <div className="inline-flex items-center p-1 bg-slate-100 border border-slate-200 rounded-md shadow-inner">
                                   {['small', 'medium', 'large'].map(s => {
                                      const isSel = settings.font_size === s
                                      return (
                                        <button key={s} onClick={() => updateSettings({ font_size: s })} className={`px-6 py-2.5 rounded text-[10px] font-black uppercase tracking-widest transition-all ${isSel ? 'bg-white text-slate-900 shadow-sm border border-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                                           {s}
                                        </button>
                                      )
                                   })}
                                </div>
                             </div>
                          </div>
                       </SharpCard>
                    )}
                    
                    {['response', 'datasources', 'advanced'].includes(activeTab) && (
                       <div className="bg-white/80 backdrop-blur-xl border border-slate-200 border-dashed rounded-lg flex flex-col items-center justify-center text-center p-20 opacity-80">
                          <SettingsIcon className="w-10 h-10 text-slate-300 mb-4 animate-[spin_8s_linear_infinite]" />
                          <h3 className="text-sm font-black text-slate-600 tracking-widest uppercase">Parameter Immutable</h3>
                          <p className="text-[10px] font-bold text-slate-400 max-w-sm mt-2 uppercase tracking-widest leading-relaxed">This subspace is currently controlled by core system variables and cannot be mutated.</p>
                       </div>
                    )}

                 </motion.div>
              </AnimatePresence>
           </motion.div>
        </div>
      </div>
    </div>
  )
}
