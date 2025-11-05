"use client";

import { useState, useEffect } from "react";
import Chat from "@/components/chat";
import { ChargebackCard } from "@/components/ChargebackCard";

export type ResearchData = {
  topic: string;
  summary: string;
  findings: Array<{
    title: string;
    description: string;
  }>;
  sources: string;
};

export type AnalysisData = {
  topic: string;
  overview: string;
  insights: Array<{
    title: string;
    description: string;
    importance: string;
  }>;
  conclusion: string;
};

interface Chargeback {
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
}

export default function Home() {
  const [researchData, setResearchData] = useState<ResearchData | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [chargebacks, setChargebacks] = useState<Chargeback[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch chargeback data on mount
    const fetchChargebacks = async () => {
      try {
        const response = await fetch('/api/chargebacks');
        const data = await response.json();
        setChargebacks(data.chargebacks || []);
      } catch (error) {
        console.error('Error fetching chargebacks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchChargebacks();
  }, []);

  return (
    <div className="relative flex h-screen overflow-hidden bg-[#DEDEE9] p-2">
      {/* Background blur circles - Creating the gradient effect */}
      <div
        className="absolute w-[445px] h-[445px] left-[1040px] top-[11px] rounded-full z-0"
        style={{ background: "rgba(255, 172, 77, 0.2)", filter: "blur(103px)" }}
      />
      <div
        className="absolute w-[609px] h-[609px] left-[1339px] top-[625px] rounded-full z-0"
        style={{ background: "#C9C9DA", filter: "blur(103px)" }}
      />
      <div
        className="absolute w-[609px] h-[609px] left-[670px] top-[-365px] rounded-full z-0"
        style={{ background: "#C9C9DA", filter: "blur(103px)" }}
      />
      <div
        className="absolute w-[445px] h-[445px] left-[128px] top-[331px] rounded-full z-0"
        style={{ background: "rgba(255, 243, 136, 0.3)", filter: "blur(103px)" }}
      />

      <div className="flex flex-1 overflow-hidden z-10 gap-2">
        {/* Chat Panel - Left Side */}
        <div className="w-[450px] flex-shrink-0 border-2 border-white bg-white/50 backdrop-blur-md shadow-elevation-lg flex flex-col rounded-lg overflow-hidden">
          <div className="p-6 border-b border-[#DBDBE5]">
            <h1 className="text-2xl font-semibold text-[#010507] mb-1">Chargeback Assistant</h1>
            <p className="text-sm text-[#57575B] leading-relaxed">
              Ask questions about chargebacks, transactions, or customer disputes
            </p>
          </div>

          <div className="flex-1 overflow-hidden">
            <Chat onResearchUpdate={setResearchData} onAnalysisUpdate={setAnalysisData} />
          </div>
        </div>

        {/* Chargeback Cards Canvas - Right Side */}
        <div className="flex-1 overflow-y-auto rounded-lg bg-white/30 backdrop-blur-sm">
          <div className="p-8">
            <div className="mb-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-semibold text-[#010507] mb-2">Chargeback Requests</h2>
                  <p className="text-[#57575B]">
                    All active and recent chargeback cases from the database
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-[#010507]">{chargebacks.length}</div>
                  <div className="text-sm text-[#57575B]">Total Cases</div>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-[400px] bg-white/60 backdrop-blur-md rounded-xl border-2 border-dashed border-[#DBDBE5]">
                <div className="text-center">
                  <div className="text-4xl mb-4">⏳</div>
                  <p className="text-[#57575B]">Loading chargeback data...</p>
                </div>
              </div>
            ) : chargebacks.length === 0 ? (
              <div className="flex items-center justify-center h-[400px] bg-white/60 backdrop-blur-md rounded-xl border-2 border-dashed border-[#DBDBE5]">
                <div className="text-center">
                  <div className="text-6xl mb-4">📋</div>
                  <h3 className="text-xl font-semibold text-[#010507] mb-2">No Chargebacks Found</h3>
                  <p className="text-[#57575B] max-w-md">
                    There are no chargeback requests in the database yet.
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {chargebacks.map((chargeback) => (
                  <ChargebackCard key={chargeback.chargeback_id} chargeback={chargeback} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
