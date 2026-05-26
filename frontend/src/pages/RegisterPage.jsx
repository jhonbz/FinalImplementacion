import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import './AuthPages.css'

export default function RegisterPage() {
  const [form, setForm]       = useState({ username: '', email: '', password: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const { register }          = useAuth()
  const navigate              = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.username || !form.email || !form.password) {
      toast.error('Completa todos los campos')
      return
    }
    if (form.password !== form.confirm) {
      toast.error('Las contraseñas no coinciden')
      return
    }
    if (form.password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres')
      return
    }
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      toast.success('¡Cuenta creada! Ya puedes iniciar sesión')
      navigate('/login')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al registrarse')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <div className="auth-header">
          <div className="auth-logo">☕</div>
          <h1 className="auth-title">Crear cuenta</h1>
          <p className="auth-sub">Únete al asistente del Café de Magga</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label className="label">Usuario</label>
            <input className="input" type="text" placeholder="Tu nombre de usuario"
              value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} autoFocus />
          </div>
          <div className="field">
            <label className="label">Correo electrónico</label>
            <input className="input" type="email" placeholder="correo@ejemplo.com"
              value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="field">
            <label className="label">Contraseña</label>
            <input className="input" type="password" placeholder="Mínimo 6 caracteres"
              value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
          </div>
          <div className="field">
            <label className="label">Confirmar contraseña</label>
            <input className="input" type="password" placeholder="Repite tu contraseña"
              value={form.confirm} onChange={e => setForm({ ...form, confirm: e.target.value })} />
          </div>
          <button className="btn btn-primary auth-btn" type="submit" disabled={loading}>
            {loading ? 'Creando cuenta...' : 'Registrarse'}
          </button>
        </form>

        <p className="auth-footer">
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" className="auth-link">Inicia sesión</Link>
        </p>
      </div>
    </div>
  )
}
