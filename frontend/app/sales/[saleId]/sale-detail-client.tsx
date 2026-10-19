"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type SaleItem = {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
};

type Payment = {
  id: number;
  amount: string;
  currency: string;
  payment_method: string | null;
  payment_status: string;
  paid_at: string | null;
};

type InventoryMovement = {
  id: number;
  product_id: number;
  product_name: string;
  movement_type: string;
  quantity: number;
  created_at: string;
};

type SaleDetail = {
  id: number;
  business_id: number;

  customer_id: number | null;
  customer_name: string | null;

  stall_event_id: number | null;

  sale_date: string;

  currency: string;

  subtotal: string;
  discount: string;
  tax: string;
  total: string;

  payment_status: string;
  status: string;

  items: SaleItem[];
  payments: Payment[];
  inventory_movements: InventoryMovement[];
};

type SaleDetailClientProps = {
  saleId: string;
};

export default function SaleDetailClient({
  saleId,
}: SaleDetailClientProps) {
  const router = useRouter();

  const [sale, setSale] = useState<SaleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSale() {
      try {
        setError(null);
        setIsLoading(true);

        const response = await fetch(
          `http://127.0.0.1:8000/sales/${saleId}`,
        );

        if (!response.ok) {
          throw new Error(
            `Failed to load sale with status ${response.status}`,
          );
        }

        const data = await response.json();

        setSale(data);
      } catch (err) {
        console.error(err);

        setError(
          "Could not load sale details. Make sure the backend is running.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    loadSale();
  }, [saleId]);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto min-h-screen max-w-md px-6 py-8">
        <button
          type="button"
          onClick={() => router.back()}
          className="mb-6 text-sm font-medium text-slate-400 transition hover:text-white"
        >
          ← Back
        </button>

        <header className="mb-8">
          <p className="text-sm font-medium text-slate-400">
            Voice Inventory
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Sale Details
          </h1>

          {sale && (
            <p className="mt-2 text-sm text-slate-500">
              Sale #{sale.id}
            </p>
          )}
        </header>

        {isLoading && (
          <p className="text-sm text-slate-400">
            Loading sale...
          </p>
        )}

        {error && (
          <div className="rounded-2xl border border-red-900 bg-red-950/30 p-4">
            <p className="text-sm text-red-300">
              {error}
            </p>
          </div>
        )}

        {sale && !isLoading && !error && (
          <div className="space-y-5">
            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Total
                  </p>

                  <p className="mt-2 text-3xl font-bold text-emerald-400">
                    ${Number(sale.total).toFixed(2)}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Status
                  </p>

                  <p className="mt-2 text-sm font-medium text-white">
                    {sale.status}
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    {sale.payment_status}
                  </p>
                </div>
              </div>

              <div className="mt-5 border-t border-slate-800 pt-4">
                <p className="text-xs text-slate-500">
                  {new Date(sale.sale_date).toLocaleString()}
                </p>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Customer
              </p>

              <p className="mt-2 text-lg font-semibold text-white">
                {sale.customer_name ?? "Unknown customer"}
              </p>

              {sale.customer_id && (
                <p className="mt-1 text-xs text-slate-500">
                  Customer #{sale.customer_id}
                </p>
              )}
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Items
              </p>

              <div className="mt-4 space-y-4">
                {sale.items.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl bg-slate-950 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-white">
                          {item.product_name}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Quantity: {item.quantity}
                        </p>
                      </div>

                      <p className="text-sm font-semibold text-emerald-400">
                        ${Number(item.line_total).toFixed(2)}
                      </p>
                    </div>

                    <div className="mt-3 flex justify-between text-xs text-slate-500">
                      <span>
                        Unit price: ${Number(item.unit_price).toFixed(2)}
                      </span>

                      <span>
                        Product #{item.product_id}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Payments
              </p>

              {sale.payments.length === 0 ? (
                <p className="mt-3 text-sm text-slate-400">
                  No payment recorded.
                </p>
              ) : (
                <div className="mt-4 space-y-4">
                  {sale.payments.map((payment) => (
                    <div
                      key={payment.id}
                      className="rounded-xl bg-slate-950 p-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {payment.payment_method ?? "Unknown method"}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {payment.payment_status}
                          </p>
                        </div>

                        <p className="text-sm font-semibold text-emerald-400">
                          ${Number(payment.amount).toFixed(2)}
                        </p>
                      </div>

                      {payment.paid_at && (
                        <p className="mt-3 text-xs text-slate-500">
                          {new Date(payment.paid_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Inventory Movements
              </p>

              {sale.inventory_movements.length === 0 ? (
                <p className="mt-3 text-sm text-slate-400">
                  No inventory movements recorded.
                </p>
              ) : (
                <div className="mt-4 space-y-4">
                  {sale.inventory_movements.map((movement) => (
                    <div
                      key={movement.id}
                      className="rounded-xl bg-slate-950 p-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {movement.product_name}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {movement.movement_type}
                          </p>
                        </div>

                        <p className="text-sm font-semibold text-slate-200">
                          {movement.quantity}
                        </p>
                      </div>

                      <div className="mt-3 flex justify-between text-xs text-slate-500">
                        <span>
                          {new Date(
                            movement.created_at,
                          ).toLocaleString()}
                        </span>

                        <span>
                          Product #{movement.product_id}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Financial Summary
              </p>

              <div className="mt-4 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">
                    Subtotal
                  </span>

                  <span className="text-white">
                    ${Number(sale.subtotal).toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-400">
                    Discount
                  </span>

                  <span className="text-white">
                    ${Number(sale.discount).toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-400">
                    Tax
                  </span>

                  <span className="text-white">
                    ${Number(sale.tax).toFixed(2)}
                  </span>
                </div>

                <div className="border-t border-slate-800 pt-3">
                  <div className="flex justify-between font-semibold">
                    <span>
                      Total
                    </span>

                    <span className="text-emerald-400">
                      ${Number(sale.total).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}