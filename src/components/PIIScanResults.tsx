import { ShieldAlert, Mail, Phone, CreditCard, User } from 'lucide-react';

interface PIIColumn {
  name: string;
  type: 'email' | 'phone' | 'credit_card' | 'name';
  confidence: 'high' | 'medium' | 'low';
}

const mockPIIColumns: PIIColumn[] = [
  { name: 'customer_email', type: 'email', confidence: 'high' },
  { name: 'contact_phone', type: 'phone', confidence: 'high' },
  { name: 'billing_email', type: 'email', confidence: 'medium' },
  { name: 'full_name', type: 'name', confidence: 'high' },
];

const getIcon = (type: PIIColumn['type']) => {
  switch (type) {
    case 'email':
      return Mail;
    case 'phone':
      return Phone;
    case 'credit_card':
      return CreditCard;
    case 'name':
      return User;
  }
};

const getTypeLabel = (type: PIIColumn['type']) => {
  switch (type) {
    case 'email':
      return 'Email Address';
    case 'phone':
      return 'Phone Number';
    case 'credit_card':
      return 'Credit Card';
    case 'name':
      return 'Personal Name';
  }
};

const getConfidenceColor = (confidence: PIIColumn['confidence']) => {
  switch (confidence) {
    case 'high':
      return 'bg-red-50 text-red-700 border-red-200';
    case 'medium':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'low':
      return 'bg-blue-50 text-blue-700 border-blue-200';
  }
};

export default function PIIScanResults() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">PII Scan Results</h3>
          <p className="text-sm text-slate-600">Columns that may contain personal information</p>
        </div>
      </div>

      <div className="space-y-2">
        {mockPIIColumns.map((column, idx) => {
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
                {column.confidence}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <p className="text-xs text-slate-600">
          <strong>Note:</strong> This is a preview feature. PII detection runs locally and columns
          are automatically masked when privacy settings are enabled.
        </p>
      </div>
    </div>
  );
}
