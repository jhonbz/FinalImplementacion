import { useState, useEffect, useRef } from 'react'
import { documentsAPI } from '../services/api'
import { IoCloudUpload, IoDocument, IoTrash, IoCheckmarkCircle, IoCloseCircle, IoTime } from 'react-icons/io5'
import toast from 'react-hot-toast'
import './DocsPage.css'

const STATUS_CONFIG = {
  ready:      { icon: <IoCheckmarkCircle />, label: 'Listo',      color: '#27ae60' },
  processing: { icon: <IoTime />,            label: 'Procesando', color: '#e67e22' },
  error:      { icon: <IoCloseCircle />,     label: 'Error',      color: '#c0392b' },
}

export default function DocsPage() {
  const [docs, setDocs]         = useState([])
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading]   = useState(true)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef            = useRef(null)

  useEffect(() => { fetchDocs() }, [])

  const fetchDocs = async () => {
    try {
      const { data } = await documentsAPI.list()
      setDocs(data)
    } catch {
      toast.error('Error cargando documentos')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file) => {
    if (!file) return
    const maxMB = 10
    if (file.size > maxMB * 1024 * 1024) {
      toast.error(`El archivo supera ${maxMB} MB`)
      return
    }
    const allowed = ['.pdf', '.txt', '.md', '.docx', '.csv']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      toast.error(`Formato no permitido. Usa: ${allowed.join(', ')}`)
      return
    }

    setUploading(true)
    try {
      const { data } = await documentsAPI.upload(file)
      toast.success(`✅ "${file.name}" procesado — ${data.chunks_created} fragmentos creados`)
      await fetchDocs()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error subiendo el archivo')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (doc) => {
    if (!confirm(`¿Eliminar "${doc.original_name}"?`)) return
    try {
      await documentsAPI.delete(doc.id)
      toast.success('Documento eliminado')
      setDocs(prev => prev.filter(d => d.id !== doc.id))
    } catch {
      toast.error('Error eliminando el documento')
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="docs-page">
      <div className="docs-header">
        <div>
          <h2 className="docs-title">Base de Conocimiento</h2>
          <p className="docs-sub">Sube documentos para que el agente aprenda sobre el café</p>
        </div>
      </div>

      {/* Zona de carga */}
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef} type="file"
          accept=".pdf,.txt,.md,.docx,.csv"
          style={{ display: 'none' }}
          onChange={e => handleUpload(e.target.files[0])}
        />
        <IoCloudUpload size={40} className="upload-icon" />
        {uploading ? (
          <div className="upload-text">Procesando documento... ⏳</div>
        ) : (
          <>
            <div className="upload-text">Arrastra un archivo aquí o haz clic para seleccionar</div>
            <div className="upload-formats">PDF · TXT · Markdown · DOCX · CSV — Máx. 10 MB</div>
          </>
        )}
      </div>

      {/* Lista de documentos */}
      <div className="docs-list-section">
        <h3 className="docs-list-title">Documentos cargados ({docs.length})</h3>

        {loading ? (
          <div className="docs-empty">Cargando...</div>
        ) : docs.length === 0 ? (
          <div className="docs-empty">
            <IoDocument size={40} style={{ opacity: 0.3 }} />
            <p>Aún no has subido ningún documento.</p>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Sube recetas, manuales o procedimientos del café.</p>
          </div>
        ) : (
          <div className="docs-grid">
            {docs.map(doc => {
              const status = STATUS_CONFIG[doc.status] || STATUS_CONFIG.processing
              return (
                <div key={doc.id} className="doc-card card">
                  <div className="doc-icon"><IoDocument size={28} /></div>
                  <div className="doc-info">
                    <div className="doc-name" title={doc.original_name}>{doc.original_name}</div>
                    <div className="doc-meta">
                      <span className="doc-type">{doc.file_type}</span>
                      <span>·</span>
                      <span>{doc.chunk_count} fragmentos</span>
                      <span>·</span>
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="doc-status" style={{ color: status.color }}>
                    {status.icon} {status.label}
                  </div>
                  <button className="btn btn-danger doc-delete" onClick={() => handleDelete(doc)} title="Eliminar">
                    <IoTrash size={15} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
