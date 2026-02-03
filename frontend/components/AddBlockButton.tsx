'use client'

import { Plus } from 'lucide-react'
import { ScriptBlock } from '@/lib/blocks/types'

interface AddBlockButtonProps {
    onAdd: (type: ScriptBlock['type']) => void
    className?: string
}

export default function AddBlockButton({ onAdd, className = '' }: AddBlockButtonProps) {
    return (
        <div className={`flex gap-6 ${className}`}>
            {[
                { type: 'hook', label: 'ADD HOOK', color: 'from-red-500/20 to-orange-500/20', border: 'border-red-500/30', text: 'text-red-400', iconColor: 'text-red-400' },
                { type: 'body', label: 'ADD BODY', color: 'from-brand-primary-500/20 to-brand-accent-500/20', border: 'border-brand-primary-500/30', text: 'text-brand-primary-400', iconColor: 'text-brand-primary-400' },
                { type: 'cta', label: 'ADD CTA', color: 'from-green-500/20 to-emerald-500/20', border: 'border-green-500/30', text: 'text-green-400', iconColor: 'text-green-400' }
            ].map((btn) => (
                <button
                    key={btn.type}
                    onClick={() => onAdd(btn.type as any)}
                    className={`flex-1 group relative overflow-hidden p-6 bg-white/[0.02] hover:bg-white/[0.05] border-2 border-dashed ${btn.border} rounded-[2rem] transition-all duration-500 hover:scale-[1.02] active:scale-95`}
                >
                    <div className={`absolute inset-0 bg-gradient-to-br ${btn.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                    <div className="relative flex flex-col items-center justify-center gap-3">
                        <div className={`w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 group-hover:rotate-90 transition-all duration-500 shadow-xl`}>
                            <Plus className={`w-6 h-6 ${btn.iconColor}`} />
                        </div>
                        <span className={`text-[10px] font-black tracking-[0.3em] ${btn.text} uppercase`}>
                            {btn.label}
                        </span>
                    </div>
                </button>
            ))}
        </div>
    )
}
