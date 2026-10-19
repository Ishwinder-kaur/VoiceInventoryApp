import SaleDetailClient from "./sale-detail-client";

export const instant = false;

type SaleDetailPageProps = {
  params: Promise<{
    saleId: string;
  }>;
};

export default async function SaleDetailPage({
  params,
}: SaleDetailPageProps) {
  const { saleId } = await params;

  return (
    <SaleDetailClient
      saleId={saleId}
    />
  );
}