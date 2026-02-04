import { Database, Settings, Shield, FileText, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

interface SidebarProps {
  activeSection: 'datasets' | 'reports' | 'diagnostics';
  onSectionChange: (section: 'datasets' | 'reports' | 'diagnostics') => void;
  reportCount?: number;
  errorCount?: number;
}

export default function Sidebar({ activeSection, onSectionChange, reportCount = 0, errorCount = 0 }: SidebarProps) {
  return (
    <div className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen">
      <div className="p-6 border-b border-slate-200">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">CloakedSheets</h1>
            <p className="text-xs text-slate-600">Privacy-First AI</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        <button
          onClick={() => onSectionChange('datasets')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            activeSection === 'datasets'
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Database className="w-5 h-5" />
          <span>Datasets</span>
        </button>

        <button
          onClick={() => onSectionChange('reports')}
          className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
            activeSection === 'reports'
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5" />
            <span>Reports</span>
          </div>
          {reportCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">
              {reportCount}
            </span>
          )}
        </button>

        <button
          onClick={() => onSectionChange('diagnostics')}
          className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
            activeSection === 'diagnostics'
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5" />
            <span>Diagnostics</span>
          </div>
          {errorCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full">
              {errorCount}
            </span>
          )}
        </button>
      </nav>

      <div className="p-4 border-t border-slate-200">
        <Link
          to="/settings"
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </Link>
      </div>
    </div>
  );
}
