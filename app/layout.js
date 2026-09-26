import "./globals.css";

export const metadata = {
  title: "Section-wise Stock & Purchase Analytics",
  description: "Purchase activity and stock-review analysis by location",
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
