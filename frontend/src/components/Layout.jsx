import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { IoChatbubblesOutline, IoDocumentsOutline, IoLogOutOutline } from 'react-icons/io5'
import toast from 'react-hot-toast'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    toast.success('Sesión cerrada')
    navigate('/login')
  }

  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">☕</span>
          <div>
            <div className="logo-title">Café de Magga</div>
            <div className="logo-sub">Asistente Virtual</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/chat" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <IoChatbubblesOutline size={20} />
            Chat
          </NavLink>
          <NavLink to="/docs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <IoDocumentsOutline size={20} />
            Documentos
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{user?.username?.[0]?.toUpperCase()}</div>
            <div className="user-name">{user?.username}</div>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Cerrar sesión">
            <IoLogOutOutline size={20} />
          </button>
        </div>
      </aside>

      {/* ── Contenido principal ── */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
