import { Shield, Lock, Zap, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <header className="flex items-center justify-between mb-20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">CloakedSheets AI</h1>
          </div>
        </header>

        <main className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-200 rounded-full mb-8">
            <Lock className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-700">Privacy-First Analysis</span>
          </div>

          <h2 className="text-5xl font-bold text-slate-900 mb-6 leading-tight">
            Analyze Spreadsheets
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-600">
              Without Compromising Privacy
            </span>
          </h2>

          <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto leading-relaxed">
            CloakedSheets AI keeps your sensitive data on your device while providing powerful AI-driven analysis.
            Get insights, trends, and answers without uploading your data to the cloud.
          </p>

          <Link
            to="/app"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200"
          >
            Open App
            <ArrowRight className="w-5 h-5" />
          </Link>

          <div className="grid md:grid-cols-3 gap-8 mt-20">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center mb-4">
                <Lock className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Local-First Processing</h3>
              <p className="text-slate-600">
                Your data stays on your device. Process and analyze locally with our secure connector.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-teal-50 rounded-xl flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-teal-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">AI-Powered Insights</h3>
              <p className="text-slate-600">
                Ask questions in natural language and get instant insights, trends, and summaries.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
              <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-slate-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Enterprise Security</h3>
              <p className="text-slate-600">
                Bank-grade encryption and zero-knowledge architecture protect your sensitive data.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
