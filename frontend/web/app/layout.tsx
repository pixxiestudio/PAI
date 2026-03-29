import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { UserProvider } from '@/contexts/UserContext'

export const metadata: Metadata = {
  title: 'PAI Dashboard',
  description: 'Personal AI Instance Dashboard - Web Interface',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <UserProvider>
            {children}
          </UserProvider>
        </Providers>
      </body>
    </html>
  )
}
