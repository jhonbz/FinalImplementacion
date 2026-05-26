import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Al cargar la app: si hay token, restaura la sesión
  useEffect(() => {
    const token    = localStorage.getItem('token')
    const username = localStorage.getItem('username')
    if (token && username) {
      setUser({ username })
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const { data } = await authAPI.login({ username, password })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    setUser({ username: data.username })
  }

  const register = async (username, email, password) => {
    await authAPI.register({ username, email, password })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
