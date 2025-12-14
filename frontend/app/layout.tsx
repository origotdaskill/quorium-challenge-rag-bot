import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'RAG Q&A Chatbot | AI-Powered Document Assistant',
    description: 'Ask questions about your documents and get intelligent answers powered by RAG technology.',
    keywords: ['RAG', 'chatbot', 'AI', 'question answering', 'document analysis'],
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
            </head>
            <body>
                {children}
            </body>
        </html>
    )
}
