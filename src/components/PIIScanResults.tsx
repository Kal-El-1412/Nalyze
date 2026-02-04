import { ShieldAlert, Mail, Phone, CreditCard, User, ShieldCheck } from 'lucide-react';
import { DatasetCatalog } from '../services/connectorApi';

interface PIIScanResultsProps {
  catalog?: DatasetCatalog | null;
  privacyMode?: boolean;
}

const getIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case 'email':
      return Mail;
    case 'phone':
      return Phone;
    case 'credit_card':
      return CreditCard;
    case 'name':
      return User;
    default:
      return ShieldAlert;
  }
};

const getTypeLabel = (type: string) => {
  switch (type.toLowerCase()) {
    case 'email':
      return 'Email Address';
    case 'phone':
      return 'Phone Number';
    case 'credit_card':
      return 'Credit Card';
    case 'name':
      return 'Personal Name';
    default:
      return 'Sensitive Data';
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) {
    return 'bg-red-50 text-red-700 border-red-200';
  } else if (confidence >= 0.5) {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  } else {
    return 'bg-blue-50 text-blue-700 border-blue-200';
  }
};

const getConfidenceLabel = (confidence: number) => {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.5) return 'medium';
  return 'low';
};

export default function PIIScanResults({ catalog, privacyMode = true }: PIIScanResultsProps) {
  const piiColumns = catalog?.piiColumns || [];

  if (piiColumns.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-900">PII Scan Results</h3>
          <p className="text-sm text-slate-600">Columns that may contain personal information</p>
        </div>
      </div>

      <div className="space-y-2">
        {piiColumns.map((column, idx) => {
          const Icon = getIcon(column.type);
          return (
            <div
              key={idx}
              className={`flex items-center justify-between p-3 rounded-lg border ${getConfidenceColor(
                column.confidence
              )}`}
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4" />
                <div>
                  <div className="font-medium text-sm">{column.name}</div>
                  <div className="text-xs opacity-75">{getTypeLabel(column.type)}</div>
                </div>
              </div>
              <span className="text-xs font-medium uppercase px-2 py-1 bg-white/50 rounded">
                {getConfidenceLabel(column.confidence)}
              </span>
            </div>
          );
        })}
      </div>

      <div className={`mt-4 p-3 rounded-lg border ${
        privacyMode
          ? 'bg-emerald-50 border-emerald-200'
          : 'bg-amber-50 border-amber-200'
      }`}>
        <div className="flex items-start gap-2">
          <ShieldCheck className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
            privacyMode ? 'text-emerald-600' : 'text-amber-600'
          }`} />
          <p className={`text-xs ${
            privacyMode ? 'text-emerald-900' : 'text-amber-900'
          }`}>
            <strong>Privacy Mode {privacyMode ? 'ON' : 'OFF'}:</strong>{' '}
            {privacyMode
              ? 'PII is currently masked in results and excluded from AI prompts.'
              : 'Privacy Mode is off. PII may be visible and sent to AI.'}
          </p>
        </div>
      </div>
    </div>
  );
}
