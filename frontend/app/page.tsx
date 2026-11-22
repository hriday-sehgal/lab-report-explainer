'use client';

import React, { useState, useEffect } from 'react';

export default function CareOSDashboard() {
  const [activeLang, setActiveLang] = useState<'en' | 'hi'>('en');
  const [activeTab, setActiveTab] = useState<'explainer' | 'evals'>('explainer');
  const [report, setReport] = useState<any>(null);
  const [evals, setEvals] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Clean initial state without auto-select
    fetch('/evals/eval_results.json')
      .then((r) => r.json())
      .then((d) => setEvals(d))
      .catch((e) => console.error(e));
  }, []);

  async function loadPreset(repId: string) {
    setLoading(true);
    try {
      const resp = await fetch(`/data/synthetic_reports/${repId}.pdf`);
      const blob = await resp.blob();
      const fd = new FormData();
      fd.append('file', blob, `${repId}.pdf`);

      const res = await fetch('/api/reports/analyze', { method: 'POST', body: fd });
      const data = await res.json();
      setReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const meta = report?.processing_metadata;
  const isLive = meta?.is_live_llm;

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* HEADER */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center font-black text-sm">H+</div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold">HeyDoc AI</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">CareOS</span>
              </div>
              <p className="text-[11px] text-slate-400">Agentic Explainer with Google ADK 2.0 & Gemini</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            {/* Live Engine Indicator */}
            <div className={`px-2.5 py-1 rounded-md border font-semibold flex items-center gap-1.5 ${isLive ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-slate-800 text-blue-300 border-slate-700'}`}>
              <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-blue-400'}`}></span>
              <span>{isLive ? `Live LLM: ${meta?.model_used}` : 'Deterministic Clinical Engine'}</span>
            </div>

            <div className="bg-slate-800 rounded-lg p-0.5 flex border border-slate-700">
              <button onClick={() => setActiveTab('explainer')} className={`px-3 py-1.5 rounded-md font-semibold ${activeTab === 'explainer' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Report</button>
              <button onClick={() => setActiveTab('evals')} className={`px-3 py-1.5 rounded-md font-semibold ${activeTab === 'evals' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>30 Evals</button>
            </div>

            <div className="bg-slate-800 rounded-lg p-0.5 flex border border-slate-700">
              <button onClick={() => setActiveLang('en')} className={`px-2 py-1 rounded-md ${activeLang === 'en' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300'}`}>EN</button>
              <button onClick={() => setActiveLang('hi')} className={`px-2 py-1 rounded-md ${activeLang === 'hi' ? 'bg-blue-600 text-white font-bold' : 'text-slate-300'}`}>हिन्दी</button>
            </div>
          </div>
        </div>
      </header>

      {/* BODY */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* PRESET PICKER */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Clinical Requisition Presets (15 Reports):</span>
            {loading && <span className="text-xs text-blue-600 animate-pulse font-semibold">Executing Pipeline...</span>}
          </div>
          <div className="flex flex-wrap gap-2 mt-3 text-xs">
            {['LAB-001', 'LAB-002', 'LAB-003', 'LAB-004', 'LAB-005', 'LAB-006', 'LAB-007', 'LAB-008', 'LAB-009', 'LAB-010', 'LAB-011', 'LAB-012', 'LAB-013', 'LAB-014', 'LAB-015'].map((id) => (
              <button
                key={id}
                onClick={() => loadPreset(id)}
                className={`px-2.5 py-1 rounded border text-[11px] font-medium transition ${report?.report_id === id ? 'bg-blue-600 text-white border-blue-600 font-bold' : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200'}`}
              >
                {id}
              </button>
            ))}
          </div>
        </div>

        {/* RESULTS VIEW */}
        {report && (
          <div className="space-y-6">
            {/* Critical Emergency Banner */}
            {report.critical_alert?.triggered && (
              <div className="bg-red-700 text-white rounded-xl p-5 border-2 border-red-800 shadow-lg">
                <span className="px-2 py-0.5 text-[10px] font-extrabold bg-white text-red-700 rounded uppercase tracking-wider">Critical Panic Value Triggered</span>
                <h3 className="text-base font-extrabold mt-1">URGENT MEDICAL ATTENTION REQUIRED</h3>
                <p className="text-xs mt-1 text-red-100 font-medium">{activeLang === 'hi' ? report.critical_alert.message_hi : report.critical_alert.message_en}</p>
              </div>
            )}

            {/* Specimen Info */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div><span className="text-slate-400 uppercase text-[10px] font-bold">Patient</span><p className="font-bold text-slate-900">{report.patient_metadata.name}</p></div>
              <div><span className="text-slate-400 uppercase text-[10px] font-bold">Panel</span><p className="font-bold text-slate-900">{report.panel_name}</p></div>
              <div><span className="text-slate-400 uppercase text-[10px] font-bold">Model Spend</span><p className="font-bold text-emerald-600">₹{meta?.estimated_cost_inr.toFixed(4)} INR</p></div>
              <div><span className="text-slate-400 uppercase text-[10px] font-bold">Latency</span><p className="font-bold text-slate-800">{meta?.latency_seconds}s</p></div>
            </div>

            {/* Next Step */}
            <div className={`p-4 rounded-xl border text-xs ${report.next_step.action === 'doctor_consult' ? 'bg-red-50/60 border-red-200' : report.next_step.action === 'follow_up_test_package' ? 'bg-blue-50/60 border-blue-200' : 'bg-emerald-50/60 border-emerald-200'}`}>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">CareOS Next Action:</span>
              <h4 className="font-bold text-slate-900 text-sm mt-0.5">{report.next_step.action.toUpperCase()}</h4>
              <p className="text-slate-700 mt-1">{activeLang === 'hi' ? report.next_step.reason_hi : report.next_step.reason_en}</p>
            </div>

            {/* Biomarker Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                <thead className="bg-slate-50 text-[10px] text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-2.5">Investigation</th>
                    <th className="px-5 py-2.5">Value</th>
                    <th className="px-5 py-2.5">Unit</th>
                    <th className="px-5 py-2.5">Range</th>
                    <th className="px-5 py-2.5">Status</th>
                    <th className="px-5 py-2.5">Evidence ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {report.biomarkers.map((b: any) => (
                    <tr key={b.item_id} className="hover:bg-slate-50">
                      <td className="px-5 py-3 font-semibold text-slate-900">{b.test_name}</td>
                      <td className={`px-5 py-3 font-mono font-bold ${b.is_critical ? 'text-red-700' : 'text-slate-800'}`}>{b.value}</td>
                      <td className="px-5 py-3 text-slate-500">{b.unit}</td>
                      <td className="px-5 py-3 text-slate-600">{b.reference_range.low !== null ? `${b.reference_range.low} - ${b.reference_range.high}` : b.reference_range.text_range}</td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${b.is_critical ? 'bg-red-600 text-white' : b.flag === 'high' ? 'bg-amber-100 text-amber-800' : b.flag === 'low' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'}`}>
                          {b.flag.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-400 text-[10px]">{b.item_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Bilingual Explanations */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">Grounded Bilingual Explanations:</h3>
              {(activeLang === 'hi' ? report.explanations_hi : report.explanations_en).map((exp: any) => (
                <div key={exp.sentence_id} className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 flex items-start justify-between text-xs gap-3">
                  <p className="text-slate-800">{exp.text}</p>
                  <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[10px] shrink-0 font-semibold">{exp.evidence_item_ids.join(', ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
