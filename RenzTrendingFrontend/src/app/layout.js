import { Lexend } from "next/font/google";
import "./globals.css";
import Navbar from "./Components/Header/Navbar";

const lexend = Lexend({
  variable: "--font-lexend",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata = {
  title: 'Renz Trending',
  description: 'Shop the latest in fashion with Renz Trending. Discover quality garments from Aslam Garments, your trusted clothing brand for trendy and affordable clothing in our online factory outlet.',
  keywords: 'Aslam garments, Renz Trending, ecommerce, factory outlet, online shopping, clothing brand, fashion, affordable clothing, trendy wear, shop fashion, garment industry, renz, Renz, Titan Dev, TitanDev, TitanNatesan, Titan Natesan, Titan, Natesan, Natesan Titan'
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>

        <meta charSet="utf-8" />
        <title>{metadata.title}</title>
        <meta name="description" content={metadata.description} />
        <meta name="keywords" content={metadata.keywords} />
        <meta property="og:title" content={metadata.title} />
        <meta property="og:description" content={metadata.description} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://renz-trending.titandev.me" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={metadata.title} />
        <meta name="twitter:description" content={metadata.description} />

      </head>
      <body className={`${lexend.variable} antialiased`} >
        {children}
      </body>
    </html>
  );
}
