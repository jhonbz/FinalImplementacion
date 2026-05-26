import { useState, useEffect, useRef } from 'react'
import { chatAPI } from '../services/api'
import { IoSend, IoCafe, IoPersonCircle, IoWarning, IoDocument } from 'react-icons/io5'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import './ChatPage.css'

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-bot'}`}>
      <div className="message-avatar">
        {isUser ? <IoPersonCircle size={28} /> : <IoCafe size={28} />}
      </div>
      <div className="message-body">
        <div className={`message-bubble ${!msg.has_context && !isUser ? 'bubble-warning' : ''}`}>
          {!isUser && !msg.has_context && (
            <div className="no-info-badge"><IoWarning size={14} /> Sin información suficiente</div>
          )}
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>
        {/* Mostrar fuentes usadas */}
        {!isUser && msg.sources?.length > 0 && (
          <div className="message-sources">
            <span className="sources-label"><IoDocument size={12} /> Fuentes:</span>
            {msg.sources.map((s, i) => (
              <span key={i} className="source-chip">{s}</span>
            ))}
          </div>
        )}
        <div className="message-time">{msg.time}</div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      id: 0, role: 'bot', has_context: true, sources: [],
      content: '¡Hola! 👋 Soy el asistente virtual del **Café de Magga**. Puedo ayudarte con recetas, procedimientos y todo lo relacionado con nuestro café. ¿En qué te puedo ayudar?',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef             = useRef(null)

  // Auto-scroll al último mensaje
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    // Agregar mensaje del usuario
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: question, time }])
    setInput('')
    setLoading(true)

    try {
      const { data } = await chatAPI.send(question)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'bot',
        content: data.answer,
        sources: data.sources,
        has_context: data.has_context,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }])
    } catch (err) {
      toast.error('Error al conectar con el agente')
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'bot', has_context: false, sources: [],
        content: 'Hubo un error al procesar tu pregunta. Verifica que el servidor esté activo.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <IoCafe size={22} />
        <div>
          <div className="chat-header-title">Asistente del Café de Magga</div>
          <div className="chat-header-sub">Pregúntame sobre recetas y procedimientos</div>
        </div>
        <div className="status-dot" title="Agente activo" />
      </div>

      <div className="chat-messages">
        {messages.map(msg => <Message key={msg.id} msg={msg} />)}

        {loading && (
          <div className="message message-bot">
            <div className="message-avatar"><IoCafe size={28} /></div>
            <div className="message-body">
              <div className="message-bubble typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-area" onSubmit={sendMessage}>
        <input
          className="input chat-input"
          placeholder="Escribe tu pregunta sobre el café..."
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button className="btn btn-primary send-btn" type="submit" disabled={loading || !input.trim()}>
          <IoSend size={18} />
        </button>
      </form>
    </div>
  )
}
