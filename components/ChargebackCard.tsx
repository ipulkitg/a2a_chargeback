interface ChargebackCardProps {
  chargeback: {
    chargeback_id: string;
    dispute_date: string;
    reason_code: string;
    dispute_type: string;
    chargeback_amount: number;
    status: string;
    outcome: string | null;
    issuing_bank: string;
    analyst_id: string;
    response_deadline: string;
    transaction_id: string;
    transaction_amount: number;
    currency: string;
    payment_method: string;
    transaction_date: string;
    risk_level: string;
    fraud_score: number;
    customer_id: string;
    customer_name: string;
    customer_email: string;
    merchant_name: string;
  };
}

export function ChargebackCard({ chargeback }: ChargebackCardProps) {
  // Status color mapping
  const statusColors: Record<string, string> = {
    open: 'bg-blue-100 text-blue-800 border-blue-200',
    pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    closed: 'bg-gray-100 text-gray-800 border-gray-200',
    resolved: 'bg-green-100 text-green-800 border-green-200',
  };

  // Risk level color mapping
  const riskColors: Record<string, string> = {
    low: 'bg-green-50 text-green-700',
    medium: 'bg-yellow-50 text-yellow-700',
    high: 'bg-red-50 text-red-700',
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD'
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-lg text-gray-900">
            {chargeback.chargeback_id}
          </h3>
          <p className="text-sm text-gray-500">{chargeback.merchant_name}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${statusColors[chargeback.status.toLowerCase()] || statusColors.open}`}>
          {chargeback.status}
        </span>
      </div>

      {/* Amount and Dispute Info */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Chargeback Amount:</span>
          <span className="text-sm font-semibold text-gray-900">
            {formatCurrency(chargeback.chargeback_amount, chargeback.currency)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Reason:</span>
          <span className="text-sm font-medium text-gray-900">{chargeback.reason_code}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Type:</span>
          <span className="text-sm text-gray-900">{chargeback.dispute_type}</span>
        </div>
      </div>

      {/* Customer Info */}
      <div className="border-t border-gray-100 pt-3 mb-3">
        <p className="text-xs font-semibold text-gray-700 mb-1">Customer</p>
        <p className="text-sm text-gray-900">{chargeback.customer_name}</p>
        <p className="text-xs text-gray-500">{chargeback.customer_email}</p>
      </div>

      {/* Risk and Transaction Info */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${riskColors[chargeback.risk_level.toLowerCase()] || riskColors.medium}`}>
          {chargeback.risk_level} Risk
        </span>
        <span className="text-xs text-gray-500">
          Fraud Score: {(chargeback.fraud_score * 100).toFixed(0)}%
        </span>
      </div>

      {/* Dates */}
      <div className="text-xs text-gray-500 space-y-1">
        <div className="flex justify-between">
          <span>Disputed:</span>
          <span>{formatDate(chargeback.dispute_date)}</span>
        </div>
        <div className="flex justify-between">
          <span>Deadline:</span>
          <span className="font-medium text-red-600">
            {formatDate(chargeback.response_deadline)}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center">
        <span className="text-xs text-gray-500">
          Analyst: {chargeback.analyst_id}
        </span>
        {chargeback.outcome && (
          <span className="text-xs font-medium text-gray-700">
            Outcome: {chargeback.outcome}
          </span>
        )}
      </div>
    </div>
  );
}
