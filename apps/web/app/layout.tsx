export const metadata = {
  title: "AlCosto",
  description: "Plataforma mayorista B2B",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
