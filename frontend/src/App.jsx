import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import AdminUsers from './pages/AdminUsers'
import Dashboard from './pages/Dashboard'
import Gjurmo from './pages/kerkese/Gjurmo'
import KerkesaForm from './pages/kerkese/KerkesaForm'
import Konfirmim from './pages/kerkese/Konfirmim'
import Landing from './pages/Landing'
import Login from './pages/Login'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* public (citizens have no account) */}
          <Route path="/" element={<Landing />} />
          <Route path="/kerkese" element={<KerkesaForm />} />
          <Route path="/kerkese/konfirmim/:numri" element={<Konfirmim />} />
          <Route path="/gjurmo" element={<Gjurmo />} />
          <Route path="/gjurmo/:numri" element={<Gjurmo />} />
          <Route path="/kycu" element={<Login />} />

          {/* staff, by role */}
          <Route element={<ProtectedRoute roles={['inspektor']} />}>
            <Route path="/inspektor" element={<Dashboard role="inspektor" />} />
          </Route>
          <Route element={<ProtectedRoute roles={['drejtor']} />}>
            <Route path="/drejtor" element={<Dashboard role="drejtor" />} />
          </Route>
          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="/admin" element={<Dashboard role="admin" />} />
            <Route path="/admin/perdoruesit" element={<AdminUsers />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
