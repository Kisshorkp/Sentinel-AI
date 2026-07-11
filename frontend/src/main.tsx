import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'sonner'
import App from './App'
import { AnalyzerProvider } from './context/AnalyzerContext'
import { AuthProvider } from './context/AuthContext'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AnalyzerProvider>
          <App />
          <Toaster position="top-right" richColors closeButton expand />
        </AnalyzerProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
