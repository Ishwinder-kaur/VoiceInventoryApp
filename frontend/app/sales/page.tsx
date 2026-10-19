"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type SaleSummary = {
  id: number;
  customer_id: number | null;
  customer_name: string | null;
  sale_date: string;
  total: string;
  currency: string;
  payment_status: string;
  status: string;
  item_count: number;
};

export default function SalesPage() {
  const router = useRouter();

  const [sales, setSales] = useState<SaleSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSales() {
      try {
        setError(null);
        setIsLoading(true);

        const response = await fetch(
          "http://127.0.0.1:8000/sales?business_id=1&limit=20",
        );

        if (!response.ok) {
          throw new Error(
            `Failed to load sales with status ${response.status}`,
          );
        }

        const data = await response.json();

        setSales(data);
      } catch (err) {
        console.error(err);

        setError(
          "Could not load recent sales. Make sure the backend is running.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadSales();
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto min-h-screen max-w-md px-6 py-8">
        <header className="mb-8">
          <p className="text-sm font-medium text-slate-400">
            Voice Inventory
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Recent Sales
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Review the latest confirmed transactions stored in the database.
          </p>
        </header>

        {isLoading && (
          <p className="text-sm text-slate-400">
            Loading sales...
          </p>
        )}

        {error && (
          <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4">
            <p className="text-sm text-red-300">
              {error}
            </p>
          </div>
        )}

        {!isLoading && !error && sales.length === 0 && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm text-slate-400">
              No sales found yet.
            </p>
          </div>
        )}

        <div className="space-y-4">
          {sales.map((sale) => {
            const formattedDate = new Date(
              sale.sale_date,
            ).toLocaleString();

            return (
              <button
                key={sale.id}
                type="button"
                onClick={() =>
                  router.push(`/sales/${sale.id}`)
                }
                className="w-full rounded-2xl border border-slate-800 bg-slate-900 p-5 text-left transition hover:border-slate-700 hover:bg-slate-800"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {sale.customer_name ?? "Unknown customer"}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Sale #{sale.id}
                    </p>
                  </div>

                  <p className="text-lg font-bold text-emerald-400">
                    ${Number(sale.total).toFixed(2)}
                  </p>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Items
                    </p>

                    <p className="mt-1 text-slate-200">
                      {sale.item_count}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Payment
                    </p>

                    <p className="mt-1 text-slate-200">
                      {sale.payment_status}
                    </p>
                  </div>
                </div>

                <div className="mt-4 border-t border-slate-800 pt-4">
                  <p className="text-xs text-slate-500">
                    {formattedDate}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </main>
  );
}