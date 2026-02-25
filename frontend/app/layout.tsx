import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'What Does She Use? 💄 | Influencer Product Search',
  description:
    'Search for products used by top Egyptian & MENA beauty influencers. Find where to buy in Egypt with the best prices.',
  keywords: ['influencer', 'beauty', 'Egypt', 'MENA', 'skincare', 'makeup', 'products'],
  openGraph: {
    title: 'What Does She Use? 💄',
    description: 'Discover products used by your favorite Egyptian & MENA influencers',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
